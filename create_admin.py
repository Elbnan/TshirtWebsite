from app import app, db, User
import hashlib

# بيانات الأدمن
username = "Bnan"
email = "admin@example.com"
phone = "0123456789"
password = "1234"
hashed_password = hashlib.sha256(password.encode()).hexdigest()

with app.app_context():
    # تأكد إنه مفيش أدمن بنفس الاسم
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        print("Admin user already exists.")
    else:
        admin = User(
            username=username,
            email=email,
            phone=phone,
            password=hashed_password,
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully.")

