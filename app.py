# Importação de bibliotecas necessárias
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:2106@localhost:5432/ConsultaFarma'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelagem tabela de remedios
class Remedio(db.Model):
    __tablename__ = 'remedio'
    idremedio = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)

# Rota de adição de remedios
@app.route('/api/products/add', methods=['POST'])
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