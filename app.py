# Importação de bibliotecas necessárias
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from flask_cors import CORS
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from datetime import datetime
from sqlalchemy import or_
from dotenv import load_dotenv
import os


app = Flask(__name__)
load_dotenv()  # carrega variáveis do .env
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Desativa o aviso de modificação do SQLAlchemy

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"message": "Você precisa estar logado para acessar essa função!"}), 401

#criando instance do banco de dados
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
CORS(app)  # ativa CORS

# Modelagem tabela de funcionario (id, nome, senha)
class funcionario(db.Model, UserMixin):
    __tablename__ = 'funcionario'
    idfuncionario = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    datanascimento = db.Column(db.Date, nullable=True)
    telefone = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    carrinho = db.relationship('Carrinho', backref='funcionario', lazy=True)

    # Corrige o erro "No id attribute"
    def get_id(self):
        return str(self.idfuncionario)

# Modelagem tabela de remedios
class Remedio(db.Model):
    __tablename__ = 'remedio'
    idremedio = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)

    # Modelagem tabela de cliente (id, nome, senha)
class Cliente(db.Model, UserMixin):
    __tablename__ = 'cliente'
    idcliente = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    datanascimento = db.Column(db.Date, nullable=True)
    telefone = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    carrinho = db.relationship('Carrinho', backref='cliente', lazy=True)

        # Corrige o erro "No id attribute"
    def get_id(self):
        return str(self.idcliente)

# Modelagem tabela do carrinho
class Carrinho(db.Model):
    __tablename__ = 'carrinho'
    idcarrinho = db.Column(db.Integer, primary_key=True)
    funcionario_idfuncionario = db.Column(db.Integer, db.ForeignKey('funcionario.idfuncionario'), nullable=True)
    cliente_idcliente = db.Column(db.Integer, db.ForeignKey('cliente.idcliente'), nullable=True)
    remedio_idremedio = db.Column(db.Integer, db.ForeignKey('remedio.idremedio'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)

    # relacionamento com Remedio
    remedio = db.relationship('Remedio', backref='carrinhos')

# Load user correto, usando session para diferenciar cliente e funcionário
@login_manager.user_loader
def load_user(user_id):
    user_type = session.get('user_type')
    if user_type == 'funcionario':
        return funcionario.query.get(int(user_id))
    elif user_type == 'cliente':
        return Cliente.query.get(int(user_id))
    return None

# Rota de login de funcionarios e clientes
@app.route('/login', methods=['POST'])
def login():
    data = request.json

    # login com email ou cpf se funcionario
    user = funcionario.query.filter(
        or_(funcionario.email == data.get("email"), funcionario.cpf == data.get("cpf"))
    ).first()

    if not user:
        user = Cliente.query.filter(
            or_(Cliente.email == data.get("email"), Cliente.cpf == data.get("cpf"))
        ).first()

    if user and data.get("senha") == user.senha:
        login_user(user)  # cria a sessão e cookie

        # Salva o tipo de usuário na sessão
        if isinstance(user, funcionario):
            session['user_type'] = 'funcionario'
        else:
            session['user_type'] = 'cliente'

        return jsonify({"message": "Login bem-sucedido!"}), 200

    return jsonify({"message": "Credenciais inválidas!"}), 401

# Rota de logout de funcionarios
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout bem-sucedido!"}), 200

# Rota de adição de funcionarios
@app.route('/api/worker/add', methods=['POST'])
@login_required
def add_worker():
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
@app.route('/api/worker/delete/<int:user_id>', methods=['DELETE'])
@login_required
def delete_worker(user_id):
    # recuperar o usuário pelo ID
    user = funcionario.query.get(user_id)  # usa outro nome de variável

    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"messege": "Funcionario deletado do banco de dados com sucesso!"}), 200

    return jsonify({"messege": "Funcionario não encontrado!"}), 404

#rota para listar funcionarios
@app.route('/api/worker', methods=['GET'])
@login_required
def list_workers():
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

# Rota de adição de clientes
@app.route('/api/client/add', methods=['POST'])
def add_client():
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
    
    cliente_novo = Cliente(
        nome=data["nome"], 
        cpf=data.get("cpf", ""), 
        datanascimento=data.get("datanascimento", None), 
        telefone=data.get("telefone", ""), 
        email=data.get("email", ""), 
        senha=data.get("senha", "")
        )
    
    db.session.add(cliente_novo)
    db.session.commit()
    return jsonify({"messege": "Cliente adicionado com sucesso!"}), 201


#rota de deleção de clientes
@app.route('/api/client/delete/<int:user_id>', methods=['DELETE'])
@login_required
def delete_client(user_id):
    # recuperar o usuário pelo ID
    user = Cliente.query.get(user_id)  # usa outro nome de variável

    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"messege": "Cliente deletado do banco de dados com sucesso!"}), 200

    return jsonify({"messege": "Cliente não encontrado!"}), 404

#rota para listar clientes
@app.route('/api/client', methods=['GET'])
@login_required
def list_clients():
    clientes = Cliente.query.all()
    result = []
    for user in clientes:
        result.append({
            "idcliente": user.idcliente,
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

# Rota para buscar remédios pelo nome
@app.route('/api/products/search', methods=['GET'])
def search_products():
    nome_query = request.args.get("nome", "").strip()
    if not nome_query:
        return jsonify({"message": "Informe o nome do remédio para pesquisar!"}), 400

    # Busca remedios com nomes parecidos
    remedios = Remedio.query.filter(Remedio.nome.ilike(f"%{nome_query}%")).all()
    
    if not remedios:
        return jsonify({"message": "Nenhum medicamento encontrado!"}), 404

    result = []
    for r in remedios:
        result.append({
            "idremedio": r.idremedio,
            "nome": r.nome,
            "descricao": r.descricao
        })

    return jsonify(result)

# Rota para adicionar itens ao carrinho
@app.route('/api/cart/add/<int:remedio_id>', methods=['POST'])
@login_required
def add_to_cart(remedio_id):
    user = current_user
    product = Remedio.query.get(remedio_id)

    if not product:
        return jsonify({"message": "Produto não encontrado!"}), 404

    # Inicializa IDs
    cliente_id = None
    funcionario_id = None

    # Define o ID correto
    if isinstance(user, Cliente):
        cliente_id = user.idcliente
    elif isinstance(user, funcionario):
        funcionario_id = user.idfuncionario

    # Garante que pelo menos um ID esteja presente
    if cliente_id is None and funcionario_id is None:
        return jsonify({"message": "Usuário inválido para adicionar ao carrinho!"}), 400

    # Cria a instância corretamente
    carrinho_item = Carrinho(
        cliente_idcliente=cliente_id,
        funcionario_idfuncionario=funcionario_id,
        remedio_idremedio=product.idremedio,
        quantidade=1
    )

    db.session.add(carrinho_item)
    db.session.commit()

    return jsonify({"message": "Produto adicionado ao carrinho!"}), 200

#Rota para remover itens do carrinho
@app.route('/api/cart/remove/<int:item_id>', methods=['DELETE'])
@login_required
def remove_from_cart(item_id):

    # produto, usuario = item no carrinho
    cart_item = Carrinho.query.get(item_id)

    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()

        return jsonify({"message": "Item removido do carrinho!"}), 200
    return jsonify({"message": "Item não encontrado no carrinho!"}), 400

# Rota para listar itens do carrinho
@app.route('/api/cart', methods=['GET'])
@login_required
def view_cart():
    user = current_user

    # Carrega o carrinho junto com os remedios de uma vez
    cart_items = (
        Carrinho.query
        .options(joinedload(Carrinho.remedio))  # carrega o objeto remedio junto
        .filter(
            (Carrinho.cliente_idcliente == getattr(user, 'idcliente', None)) |
            (Carrinho.funcionario_idfuncionario == getattr(user, 'idfuncionario', None))
        )
        .all()
    )

    cart_content = []
    for cart_item in cart_items:
        cart_content.append({
            "idcarrinho": cart_item.idcarrinho,
            "cliente_idcliente": cart_item.cliente_idcliente,
            "funcionario_idfuncionario": cart_item.funcionario_idfuncionario,
            "remedio_idremedio": cart_item.remedio_idremedio,
            "quantidade": cart_item.quantidade,
            "nome": cart_item.remedio.nome  # já vem carregado
        })

    return jsonify(cart_content)

#rota de checkout do carrinho
@app.route('/api/cart/checkout', methods=['POST'])
@login_required
def checkout():
    user = current_user

    # Busca todos os itens do carrinho do usuário de uma vez, com os produtos já carregados
    cart_items = (
        Carrinho.query
        .options(joinedload(Carrinho.remedio))
        .filter(
            (Carrinho.cliente_idcliente == getattr(user, 'idcliente', None)) |
            (Carrinho.funcionario_idfuncionario == getattr(user, 'idfuncionario', None))
        )
        .all()
    )

    if not cart_items:
        return jsonify({"message": "Carrinho vazio!"}), 400

    # Deleta todos os itens de uma vez, sem precisar iterar
    deleted_count = Carrinho.query.filter(
        (Carrinho.cliente_idcliente == getattr(user, 'idcliente', None)) |
        (Carrinho.funcionario_idfuncionario == getattr(user, 'idfuncionario', None))
    ).delete(synchronize_session=False)

    db.session.commit()

    return jsonify({"message": f"Checkout realizado com sucesso! Itens removidos: {deleted_count}"}), 200

# Usado para iniciar o servidor Flask
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)