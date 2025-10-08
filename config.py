import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'archivos.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'DovahCloud')
    PRIVATE_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'DovahCloud', 'Privado')

