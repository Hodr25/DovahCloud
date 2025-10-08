import os
from dotenv import load_dotenv
from app import app
from models import db, Usuario

# Cargar variables del .env
load_dotenv("credenciales.env")  # o ".env" según el nombre del archivo que uses

def create_user_if_not_exists(username, password):
    with app.app_context():
        user = Usuario.query.filter_by(nombre=username).first()
        if user:
            print(f"⚠️ Usuario '{username}' ya existe")
        else:
            user = Usuario(nombre=username)
            user.establecer_contraseña(password)
            db.session.add(user)
            db.session.commit()
            print(f"✅ Usuario '{username}' creado")

if __name__ == "__main__":
    u1, p1 = os.getenv("USER1"), os.getenv("PASS1")
    u2, p2 = os.getenv("USER2"), os.getenv("PASS2")

    if u1 and p1:
        create_user_if_not_exists(u1, p1)
    if u2 and p2:
        create_user_if_not_exists(u2, p2)
