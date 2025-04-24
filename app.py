from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import hashlib
from werkzeug.utils import secure_filename

app = Flask(__name__)

# إعداد مجلد رفع الصور
app.config['UPLOAD_FOLDER'] = 'static/images'
app.secret_key = 'secret_key'

# إعداد الاتصال بقاعدة بيانات SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tshirtstore.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# نموذج قاعدة بيانات TShirts
class TShirt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    sizes = db.Column(db.String(50), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)

# نموذج قاعدة بيانات Orders
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tshirt_id = db.Column(db.Integer, db.ForeignKey('t_shirt.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    seen_by_admin = db.Column(db.Boolean, default=False)

# نموذج قاعدة بيانات Users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# إنشاء الجداول في قاعدة البيانات
with app.app_context():
    db.create_all()

# Helper function to count new orders
def get_new_orders_count():
    if session.get('is_admin'):
        return Order.query.filter_by(seen_by_admin=False).count()
    return 0

# Home page
@app.route('/')
def index():
    tshirts = TShirt.query.all()
    new_orders_count = get_new_orders_count()
    return render_template('index.html', tshirts=tshirts, new_orders_count=new_orders_count)

# Admin-only page to add new t-shirt
@app.route('/add', methods=['GET', 'POST'])
def add():
    if not session.get('is_admin'):
        return redirect(url_for('log_in'))

    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        sizes = request.form['sizes']
        payment_method = "Cash on delivery"

        images = request.files.getlist('images')
        image_filenames = []

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        for image in images:
            if image and image.filename:
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_filenames.append(filename)

        image_urls = ','.join(image_filenames)

        new_tshirt = TShirt(
            name=name,
            price=price,
            description=description,
            sizes=sizes,
            payment_method=payment_method,
            image_url=image_urls
        )

        db.session.add(new_tshirt)
        db.session.commit()
        return redirect('/')

    new_orders_count = get_new_orders_count()
    return render_template('add.html', new_orders_count=new_orders_count)

# Order page
@app.route('/order/<int:tshirt_id>', methods=['GET', 'POST'])
def order(tshirt_id):
    if request.method == 'POST':
        customer_name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        size = request.form['size']

        new_order = Order(
            tshirt_id=tshirt_id,
            customer_name=customer_name,
            phone=phone,
            address=address,
            size=size,
            order_date=datetime.now()
        )

        db.session.add(new_order)
        db.session.commit()
        return redirect('/success')

    new_orders_count = get_new_orders_count()
    return render_template('order.html', tshirt_id=tshirt_id, new_orders_count=new_orders_count)

# Success page after an order
@app.route('/success')
def success():
    new_orders_count = get_new_orders_count()
    return render_template('success.html', new_orders_count=new_orders_count)

# Sign up page
@app.route('/signup', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        new_user = User(
            username=username,
            email=email,
            phone=phone,
            password=hashed_password,
            is_admin=False
        )

        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('log_in'))

    return render_template('sign_up.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def log_in():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        user = User.query.filter_by(username=username, password=hashed_password).first()

        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            return redirect(url_for('index'))
        return 'Incorrect username or password'

    return render_template('log_in.html')

# Admin dashboard
@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('log_in'))
    new_orders_count = get_new_orders_count()
    return render_template('admin_dashboard.html', new_orders_count=new_orders_count)

# Orders page for admin
@app.route('/orders')
def orders():
    if not session.get('is_admin'):
        return redirect(url_for('log_in'))

    orders = db.session.query(Order, TShirt).join(TShirt).order_by(Order.order_date.desc()).all()

    for order in orders:
        order[0].seen_by_admin = True
    db.session.commit()

    new_orders_count = get_new_orders_count()
    return render_template('orders.html', orders=orders, new_orders_count=new_orders_count)

# Edit t-shirt
@app.route('/edit/<int:tshirt_id>', methods=['GET', 'POST'])
def edit(tshirt_id):
    if not session.get('is_admin'):
        return redirect(url_for('log_in'))

    tshirt = TShirt.query.get(tshirt_id)

    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        sizes = request.form['sizes']

        tshirt.name = name
        tshirt.price = price
        tshirt.description = description
        tshirt.sizes = sizes

        db.session.commit()
        return redirect('/')

    new_orders_count = get_new_orders_count()
    return render_template('edit.html', tshirt=tshirt, new_orders_count=new_orders_count)

# Delete t-shirt
@app.route('/delete/<int:tshirt_id>', methods=['GET'])
def delete(tshirt_id):
    if not session.get('is_admin'):
        return redirect(url_for('log_in'))

    tshirt = TShirt.query.get(tshirt_id)
    db.session.delete(tshirt)
    db.session.commit()
    return redirect('/')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Run the website
if __name__ == '__main__':
    app.run(debug=True)
