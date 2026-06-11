import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import db
from models import User

app = create_app()
with app.app_context():
    db.create_all()
    print("Database tables ready.")

    admin_email = "samuel.rwunganira@gmail.com"
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(
            email=admin_email,
            name="Samuel Rwunganira",
            role="admin",
        )
        admin.set_password(os.getenv("ADMIN_PASSWORD", "Admin@EVD2024!"))
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user created: {admin_email}")
    else:
        print(f"Admin user already exists: {admin_email}")
