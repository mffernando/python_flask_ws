from flask import Flask, render_template, redirect, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import os.path
import json
import base64

db_filename = "purchase_list.db"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_filename
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "secret"

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# auth
class User(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(100),unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    def json(self):
        return{
            'id':self.id,
            'name':self.name,
            'email':self.email
        }

# criar novo usuario
@app.route('/api/signup',methods=['POST'])
def signup_post():
    req_data = request.get_json()
    email = req_data['email']
    password = req_data['password']
    name = req_data['name']

    user = User.query.filter_by(email=email).first()

    if user is not None:
        data = {"error":"email address already exists."}
        return Response(json.dumps(data),status=409,mimetype='application/json')


    new_user = User(email=email,name=name,password=generate_password_hash(password,method='sha256'))
    db.session.add(new_user)
    db.session.commit()
    db.session.refresh(new_user)

    return Response(json.dumps(new_user.json()),status=201,mimetype='application/json')

# listar usuarios
@app.route("/api/signup", methods=["GET"])
def get_json_users():
    all_users = User.query.order_by(User.email).all()
    return jsonify([row.json() for row in all_users])

# autorizacao
@login_manager.request_loader
def load_user(request):
    token = request.headers.get('Authorization')
    print(token)

    if token is not None:
        token = token.replace('Basic ', '', 1)
        print(token)
        try:
            # token = base64.b64decode(token)
            token = base64.b64decode(token).decode('utf-8') # decode utf-8 para retirar b''
            print(token)
        except TypeError:
            print("TypeError")
        print(token)
        email,password = token.split(':')
        user = User.query.filter_by(email=email).first()
        if user is not None:
            if check_password_hash(user.password,password):
                return user
    return None

# nao autorizado
@login_manager.unauthorized_handler
def unauthorized():
    data = {"error":"unauthorized"}
    return Response(json.dumps(data),status=401,mimetype='application/json')

@app.route('/api/profile')
@login_required
def profile_get():
    return Response(json.dumps(current_user.json()),status=200,mimetype='application/json')

@app.route('/api/protected')
@login_required
def protected_get():
    return Response("protected data",status=200,mimetype='application/text')

### PRODUTOS ###

# 1 - o descritivo do exercicio: #Criar um model Compras com campos no Banco de dados
# (id,nome,quantidade,marca,validade)
class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    validity = db.Column(db.String, nullable=True, default="Indeterminada")
    creation_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    #json
    def json(self):
        return {
            'id':self.id,
            'name':self.name,
            'amount':self.amount,
            'brand':self.brand,
            'validity':self.validity,
            'creation_date':str(self.creation_date)
        }

# JSON

# GET json route to return all Customers order by creation_date
# 1 - #@app.route("/compras",methods=["GET"]) retorna toda a lista de compras
@app.route("/api/purchases", methods=["GET"])
def get_json_products():
    all_products = Products.query.order_by(Products.creation_date).all()
    # return json.dumps([row.json() for row in all_products])
    # return "all products: " + str(all_products)
    # return jsonify({'products': [row.json() for row in all_products]})
    # return jsonify({'products': [row.json() for row in all_products]})
    return jsonify([row.json() for row in all_products])

# 2 - #@app.route("/compras",methods=["POST"]) cria um novo item na lista de compras
@app.route("/api/purchases", methods=["POST"])
def post_json_product():
    result = request.get_json(silent=True)
    name = result['name']
    amount = result['amount']
    brand = result['brand']
    validity = result['validity']
    product = Products(name=name, amount=amount, brand=brand, validity=validity)
    db.session.add(product)
    db.session.commit()
    return json.dumps(result)

# 3 - #@app.route("/compras/<int:id>",methods=["GET"]) retorna o item com o id
@app.route("/api/purchases/<int:id>", methods=["GET"])
def get_json_product(id):
    product = Products.query.get_or_404(id).json()
    return jsonify(product)

# 4 - #@app.route("/compras/<int:id>",methods=["PATCH"]) SUBSTITUI parcialmente item ou cria um novo
# @app.route('/api/purchases/<int:id>', methods=['PATCH'])
# def patch_json_product(id):
#     result = request.get_json(silent=True)
#     if id in products:
#
#         return
    # product = Products.query.get_or_404(id).json()
    # return jsonify(product)

# 5 - #@app.route("/compras/<int:id>",methods=["PUT"]) SUBSTITUI o item ou cria um novo
@app.route("/api/purchases/<int:id>", methods=["PUT"])
def update_json_product(id):
    result = request.get_json(silent=True)
    product = Products.query.get_or_404(id)
    name = result['name']
    amount = result['amount']
    brand = result['brand']
    validity = result['validity']

    product.name = name
    product.amount = amount
    product.brand = brand
    product.validity = validity

    db.session.add(product)
    db.session.commit()
    # db.session.flush()

    return json.dumps(""), 200

# 6 - #@app.route("/compras/<int:id>",methods=["DELETE"]) remove o item
@app.route("/api/purchases/<int:id>", methods=["DELETE"])
def delete_json_product(id):
    product = Products.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify("")

# filter by age
#using: http://127.0.0.1:5000/customers.json/age?from=3&to=10
# @app.route('/customers.json/age')
# def age_customer():
#     fromAge = request.args.get('from')
#     toAge = request.args.get('to')
#     customers = Customers.query.filter(Customers.age > fromAge, Customers.age < toAge)
#     return json.dumps([row.json() for row in customers])

# HTML

# redirect home
@app.route('/')
def home():
    return redirect("/purchases")

# GET route to return all Customers order by creation_date
@app.route("/purchases/", methods=["GET"])
def get_products():
    # if request.method == 'POST': if user methods = GET POST
    all_products = Products.query.order_by(Products.creation_date).all()
    return render_template("purchases.html", products=all_products)

# POST route to insert
@app.route("/purchases", methods=["POST"])
def post_products():
    name = request.form['name']
    amount = request.form['amount']
    brand = request.form['brand']
    validity = request.form['validity']
    product = Products(name=name, amount=amount, brand=brand, validity=validity)
    db.session.add(product)
    db.session.commit()
    return redirect("/purchases"), 302


# delete route
@app.route("/purchases/delete/<int:id>")
def delete_product(id):
    product = Products.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return redirect("/purchases")

# show product
@app.route("/purchases/product/<int:id>", methods=["GET"])
def show_product(id):
    product = Products.query.get_or_404(id)
    return render_template("product.html", product=product)

@app.route('/purchases/edit/<int:id>', methods=["GET", "POST"])
def edit_product(id):
    product = Products.query.get_or_404(id)
    if request.method == "POST":
        product.name = request.form["name"]
        product.amount = request.form["amount"]
        product.brand = request.form["brand"]
        product.validity = request.form["validity"]
        db.session.commit()
        return redirect("/purchases")
    else:
        return render_template("edit.html", product=product)

# run app
if __name__ == "__main__":
    # create db if it does not exist
    # if os.path.exists(db_filename) == False:
    if not os.path.exists(db_filename):
        db.create_all()
    # seed db
    # db.session.add(Customers(name="teste 1", age=10, address="address 1", email="teste1@email.com"))
    # db.session.add(Customers(name="teste 2", address="address 2", email="teste2@email.com"))
    # db.session.commit()

    # host='10.0.0.5' externally visible server
    app.run(host='10.0.0.4', debug=True)