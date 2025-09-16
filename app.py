# Importação de bibliotecas necessárias
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
from datetime import datetime
from sqlalchemy import or_

app = Flask(__name__)
app.config['SECRET_KEY'] = 'senha_secreta123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_tyo9NsGnJP3F@ep-weathered-sky-ac4h3zbt-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"message": "Você precisa estar logado para acessar essa função!"}), 401
db = SQLAlchemy(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
CORS(app)



# Modelagem tabela de usuario (id, nome, senha)
class funcionario(db.Model, UserMixin):
    __tablename__ = 'funcionario'
    idfuncionario = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    datanascimento = db.Column(db.Date, nullable=True)
    telefone = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)

        # Corrige o erro "No id attribute"
    def get_id(self):
        return str(self.idfuncionario)

# Modelagem tabela de remedios
class Remedio(db.Model):
    __tablename__ = 'remedio'
    idremedio = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return funcionario.query.get(int(user_id))

# Rota de login de funcionarios
@app.route('/login', methods=['POST'])
def login():
    data = request.json

#login com email ou cpf
    user = funcionario.query.filter(or_(funcionario.email == data.get("email"), funcionario.cpf == data.get("cpf"))).first()
    
    if user and data.get("senha") == user.senha:
            login_user(user) # cria a sessão e cookie
            return jsonify({"message": "Login bem-sucedido!"}), 200
    return jsonify({"message": "Credenciais inválidas!"}), 401

# Rota de logout de funcionarios
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout bem-sucedido!"}), 200

# Rota de adição de funcionarios
@app.route('/api/users/add', methods=['POST'])
@login_required
def add_user():
    data = request.get_json()
    if not data:
        return jsonify({"messege": "Requisição inválida, nenhum dado enviado!"}), 400

    campos_obrigatorios = ["nome", "cpf", "email", "senha"]
    for campo in campos_obrigatorios:
        if campo not in data or not str(data[campo]).strip():
            return jsonify({"messege": f"Dados inválidos, campo {campo} obrigatório!"}), 400
        
        # processar data de nascimento
        data_nascimento = None
        if "datanascimento" in data and data["datanascimento"]:
            try:
                # tenta converter do formato YYYY-MM-DD
                data_nascimento = datetime.strptime(data["datanascimento"], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"messege": "Formato de data inválido! Use YYYY-MM-DD"}), 400
    
    funcionario_novo = funcionario(
        nome=data["nome"], 
        cpf=data.get("cpf", ""), 
        datanascimento=data.get("datanascimento", None), 
        telefone=data.get("telefone", ""), 
        email=data.get("email", ""), 
        senha=data.get("senha", "")
        )
    
    db.session.add(funcionario_novo)
    db.session.commit()
    return jsonify({"messege": "Funcionario adicionado com sucesso!"}), 201


#rota de deleção de funcionarios
@app.route('/api/users/delete/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    # recuperar o usuário pelo ID
    user = funcionario.query.get(user_id)  # usa outro nome de variável

    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"messege": "Funcionario deletado do banco de dados com sucesso!"}), 200

    return jsonify({"messege": "Funcionario não encontrado!"}), 404

#rota para listar funcionarios
@login_required
@app.route('/api/users', methods=['GET'])
def list_users():
    funcionarios = funcionario.query.all()
    result = []
    for user in funcionarios:
        result.append({
            "idfuncionario": user.idfuncionario,
            "nome": user.nome,
            "cpf": user.cpf,
            "datanascimento": user.datanascimento.strftime("%Y-%m-%d") if user.datanascimento else None,
            "telefone": user.telefone,
            "email": user.email
        })
    return jsonify(result)

# Rota de adição de remedios
@app.route('/api/products/add', methods=['POST'])
@login_required
def add_product():
    data = request.get_json()
    if not data or 'nome' not in data or not data['nome'].strip():
        return jsonify({"messege": "Dados invalidos, campo de nome obrigatorio!"}), 400
    
    remedio = Remedio(
        nome=data["nome"], 
        descricao=data.get("descricao", "")
        )
    
    db.session.add(remedio)
    db.session.commit()
    return jsonify({"messege": "Produto adicionado com sucesso!"}), 201

# Rota de deleção de remedios
@app.route('/api/products/delete/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    # 1 - recuperar o id do produto
    remedio = Remedio.query.get(product_id)
     # 2 - verificar se existe
    if remedio != None:
        # 3 - se existir, apagar
        db.session.delete(remedio)
        db.session.commit()
        return jsonify({"messege": "Produto deletado do banco de dados com sucesso!"}), 200
    # 4 - se não existir retornar mensagem de erro
    return jsonify({"messege": "Produto não encontrado!"}), 404

# rota para busca de remedios
@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product_details(product_id):
    remedio = Remedio.query.get(product_id)
    if remedio:
        return jsonify({
            "idremedio": remedio.idremedio,
            "nome": remedio.nome,
            "descricao": remedio.descricao
        })
    return jsonify({"messege": "Medicamento não encontrado!"}), 404

# rota de atualização de itens
@app.route('/api/products/update/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    remedio = Remedio.query.get(product_id)
    if not remedio:
        return jsonify({"messege": "Medicamento não encontrado!"}), 404
    
    data = request.json
    if "nome" in data and data["nome"] is not None and data["nome"].strip():
        remedio.nome = data["nome"]

    if "descricao" in data:
        remedio.descricao = data["descricao"]

    db.session.commit()

    return jsonify({"messege": "Produto atualizado com sucesso!"}), 200

# rota para listar produtos
@app.route('/api/products', methods=['GET'])
def list_products():
    remedios = Remedio.query.all()
    result = []
    for remedio in remedios:
        result.append({
            "idremedio": remedio.idremedio,
            "nome": remedio.nome,
        })
    return jsonify(result)

    # Usado para iniciar o servidor Flask
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)