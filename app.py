from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
from marshmallow import ValidationError



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:**YOURPASSWORD**@localhost/e_commerce_db'
db = SQLAlchemy(app)
ma = Marshmallow(app)


class Product(db.Model):
    __tablename__ = 'Products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)


class Customer(db.Model):
    __tablename__ = 'Customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(320))
    phone = db.Column(db.String(15))


class CustomerAccount(db.Model):
    __tablename__ = 'Customer_Accounts'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))


class Order(db.Model): 
    __tablename__ = 'Orders'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customers.id'))

class OrderStatus(db.Model):
    __tablename__="order_status"
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(255), nullable=False) 


order_product = db.Table('Order_Product',
    db.Column('order_id', db.Integer, db.ForeignKey('Orders.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('Products.id'), primary_key=True),
    db.Column('quantity', db.Integer, nullable=False)
)


Customer.orders = db.relationship('Order', backref='customer')
CustomerAccount.customer = db.relationship('Customer', backref='customer_account', uselist=False)
Order.products = db.relationship('Product', secondary=order_product, backref=db.backref('orders'))




class OrderProductSchema(ma.Schema):
    product_id = fields.Integer(required=True)
    quantity = fields.Integer(required=True)


class CustomerSchema(ma.Schema):
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)
    class Meta:
        fields = ("name", "email", "phone", "id")
customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)


class AccountSchema(ma.Schema):
    id = fields.Integer(required=True)
    username = fields.String(required=True)
    password = fields.String(required=True)
    customer_id = fields.Integer(required=True)
    class Meta:
        fields = ("id", "username", "password", "customer_id")
customer_account_schema = AccountSchema()
customer_accounts_schema = AccountSchema(many=True)


class ProductSchema(ma.Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    price = fields.Float(required=True)
    class Meta:
        fields = ("id", "name", "price")
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)


class OrderSchema(ma.Schema):
    id = fields.Integer(required=True)
    date = fields.Date(required=True)
    customer_id = fields.Integer(required=True)
    status = fields.String(required=True)
    products = fields.List(fields.Nested(OrderProductSchema))

    app.config['PROPAGATE_EXCEPTIONS'] = True
    
    class Meta:
        fields = ("id", "date", "customer_id", "status", "products")
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)




@app.route('/customers', methods=['GET'])
def GET():
    customers = Customer.query.all()
    return customers_schema.jsonify(customers)


@app.route('/customers', methods=['POST'])
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    new_customer = Customer(name=customer_data['name'], email=customer_data['email'], phone=customer_data['phone'])
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({"message": "Customer added successfully"}), 201


@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    customer.name = customer_data['name']
    customer.email = customer_data['email']
    customer.phone = customer_data['phone']
    db.session.commit()
    return jsonify({"message": "Customer updated successfully"}), 200


@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer Removed successfully"}), 200

@app.route('/accounts', methods=['GET'])
def get_accounts():
    try:
        accounts = CustomerAccount.query.all()
        return customer_accounts_schema.jsonify(accounts)
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@app.route('/accounts', methods=['POST'])
def add_accounts():
    try:
        customer_account_data = customer_account_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    new_customer_account = CustomerAccount(username=customer_account_data['username'], password=customer_account_data['password'], customer_id=customer_account_data['customer_id'])
    db.session.add(new_customer_account)
    db.session.commit()
    return jsonify({"message": "New customer created"})

@app.route('/accounts/<int:id>', methods=['PUT'])
def update_accounts(id):
    account = CustomerAccount.query.get_or_404(id)
    try:
        customer_account_data = customer_account_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    account.username = customer_account_data['username']
    account.password = customer_account_data['password']
    account.customer_id = customer_account_data['customer_id']
    db.session.commit()
    return jsonify({"message": "Account updated successfully"}), 200

@app.route('/accounts/<int:id>', methods=['DELETE'])
def delete_accounts(id):
    account = CustomerAccount.query.get_or_404(id)
    db.session.delete(account)
    db.session.commit()
    return jsonify({"message": "Account Removed successfully"}), 200


@app.route('/products', methods=['GET'])
def get_products():
    try:
        products = Product.query.all()
        return products_schema.jsonify(products)
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@app.route('/products', methods=['POST'])
def add_products():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    new_product = Product(name=product_data['name'], price=product_data['price'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"message": "New product created"})


@app.route('/products/<int:id>', methods=['PUT'])
def update_products(id):
    product = Product.query.get_or_404(id)
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    product.name = product_data['name']
    product.price = product_data['price']
    db.session.commit()
    return jsonify({"message": "Product updated successfully"}), 200


@app.route('/products/<int:id>', methods=['DELETE'])
def delete_products(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product removed successfully"}), 200



@app.route('/orders', methods=['GET'])
def get_orders():
    try:
        orders = Order.query.all()
        return orders_schema.jsonify(orders)
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    

@app.route('/orders', methods=['POST'])
def add_orders():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    new_order = Order(date=order_data['date'], customer_id=order_data['customer_id'])
    db.session.add(new_order)
    db.session.commit()

    for product in order_data['products']:
        op = order_product.insert().values(order_id=new_order.id, product_id=product['product_id'], quantity=product['quantity'])
        db.session.execute(op)

    return jsonify({"message": "New customer created"})


@app.route('/orders/<int:id>', methods=['PUT'])
def update_orders(id):
    order = Order.query.get_or_404(id)
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    order.date = order_data['date']
    order.custome_id = order_data['customer_id']
    db.session.commit()
   
    db.session.execute(order_product.delete().where(order_product.c.order_id == id))
    for product in order_data['products']:
        op = order_product.insert().values(order_id=id, product_id=product['product_id'], quantity=product['quantity'])
        db.session.execute(op)
        return jsonify({"message": "Product updated successfully"}), 200


@app.route('/orders/<int:id>', methods=['DELETE'])
def delete_orderss(id):
    order = Order.query.get_or_404(id)
    db.session.execute(order_product.delete().where(order_product.c.order_id == id))
    db.session.delete(order)
    db.session.commit()
    return jsonify({"message": "Product removed successfully"}), 200


@app.route('/order_statuses', methods=['GET'])
def get_order_statuses():
    statuses = OrderStatus.query.all()
    return jsonify([status.status for status in statuses])

with app.app_context():
    if not OrderStatus.query.all():
        statuses = ["Pending", "Shipped", "Delivered", "Cancelled"]
        for status in statuses:
            new_status = OrderStatus(status=status)
            db.session.add(new_status)
        db.session.commit()


@app.route('/customers/<int:customer_id>/orders', methods=['GET'])
def get_customer_orders(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    orders = Order.query.filter_by(customer_id=customer.id).all()
    return orders_schema.jsonify(orders)


@app.route('/customers/<int:customer_id>/orders/<int:order_id>', methods=['PUT'])
def update_customer_order(customer_id, order_id):
    order = Order.query.filter_by(id=order_id, customer_id=customer_id).first_or_404()
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    order.status = order_data['status']
    db.session.commit()
    return jsonify({"message": "Order status updated successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)

with app.app_context():
    db.create_all()