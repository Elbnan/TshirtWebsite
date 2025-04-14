from flask import Flask, render_template, request, redirect, session, url_for
import pyodbc
import os
from datetime import datetime
import hashlib
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images'
app.secret_key = 'secret_key'

# Connect to the database
conn = pyodbc.connect(
    'DRIVER={SQL Server};'
    'SERVER=DESKTOP-VR0FRNK;'
    'DATABASE=TshirtStore;'
    'Trusted_Connection=yes;'
)
cursor = conn.cursor()

# Helper function to count new orders
def get_new_orders_count():
    if session.get('is_admin'):
        cursor.execute("SELECT COUNT(*) FROM Orders WHERE seen_by_admin = 0")
        return cursor.fetchone()[0]
    return 0

# Home page
@app.route('/')
def index():
    cursor.execute("SELECT * FROM TShirts")
    tshirts = cursor.fetchall()
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

        images = request.files.getlist('images')  # استخدم 'images' بدل 'image'
        image_filenames = []

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # تأكد من وجود المسار

        for image in images:
            if image and image.filename:
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_filenames.append(filename)

        image_urls = ','.join(image_filenames)

        cursor.execute("INSERT INTO TShirts (name, price, description, sizes, payment_method, image_url) VALUES (?, ?, ?, ?, ?, ?)",
                       name, price, description, sizes, payment_method, image_urls)
        conn.commit()
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

        cursor.execute("INSERT INTO Orders (tshirt_id, customer_name, phone, address, size, order_date, seen_by_admin) VALUES (?, ?, ?, ?, ?, ?, 0)",
                       tshirt_id, customer_name, phone, address, size, datetime.now())
        conn.commit()
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
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        cursor.execute("INSERT INTO Users (username, password, is_admin) VALUES (?, ?, 0)", (username, hashed_password))
        conn.commit()
        return redirect(url_for('log_in'))

    return render_template('sign_up.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def log_in():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        cursor.execute("SELECT * FROM Users WHERE username=? AND password=?", (username, hashed_password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            return redirect(url_for('index'))
        return 'Incorrect username or password'

    return render_template('log_in.html')

# Admin dashboard (اختياري)
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

    cursor.execute(""" 
        SELECT Orders.id, Orders.customer_name, Orders.phone, Orders.address, Orders.size, Orders.order_date, TShirts.name 
        FROM Orders 
        JOIN TShirts ON Orders.tshirt_id = TShirts.id 
        ORDER BY Orders.order_date DESC
    """)
    orders = cursor.fetchall()

    # update seen_by_admin to 1
    cursor.execute("UPDATE Orders SET seen_by_admin = 1 WHERE seen_by_admin = 0")
    conn.commit()

    new_orders_count = get_new_orders_count()
    return render_template('orders.html', orders=orders, new_orders_count=new_orders_count)

# Edit t-shirt
@app.route('/edit/<int:tshirt_id>', methods=['GET', 'POST'])
def edit(tshirt_id):
    if not session.get('is_admin'):
        return redirect(url_for('log_in'))

    cursor.execute("SELECT * FROM TShirts WHERE id=?", (tshirt_id,))
    tshirt = cursor.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        sizes = request.form['sizes']

        cursor.execute("""
            UPDATE TShirts SET name=?, price=?, description=?, sizes=? WHERE id=?
        """, (name, price, description, sizes, tshirt_id))
        conn.commit()
        return redirect('/')

    new_orders_count = get_new_orders_count()
    return render_template('edit.html', tshirt=tshirt, new_orders_count=new_orders_count)

# Delete t-shirt
@app.route('/delete/<int:tshirt_id>', methods=['GET'])
def delete(tshirt_id):
    if not session.get('is_admin'):
        return redirect(url_for('log_in'))

    cursor.execute("DELETE FROM TShirts WHERE id=?", (tshirt_id,))
    conn.commit()
    return redirect('/')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Run the website
if __name__ == '__main__':
    app.run(debug=True)
