import os
import hashlib
from app import app, db
from models import Archivo

def calcular_hash(ruta_archivo):
    hasher = hashlib.sha256()
    with open(ruta_archivo, 'rb') as f:
        for bloque in iter(lambda: f.read(8192), b''):
            hasher.update(bloque)
    return hasher.hexdigest()

with app.app_context():
    for archivo in Archivo.query.all():
        if archivo.ruta.startswith('/var/www/dovahcloud/'):
            nueva_ruta = archivo.ruta.replace('/var/www/dovahcloud/', '/home/dovah/dovahcloud/')
            if os.path.exists(nueva_ruta):
                print(f"🔁 Corrigiendo ruta: {archivo.nombre}")
                archivo.ruta = nueva_ruta
    db.session.commit()

    archivos = Archivo.query.filter((Archivo.hash_archivo == None) | (Archivo.hash_archivo == '')).all()
    print(f"🔍 Archivos sin hash encontrados: {len(archivos)}")

    for archivo in archivos:
        if os.path.exists(archivo.ruta):
            nuevo_hash = calcular_hash(archivo.ruta)
            archivo.hash_archivo = nuevo_hash
            print(f"✅ Hash generado para: {archivo.nombre}")
            print(f"Ruta en DB: {archivo.ruta}")
            print("¿Existe?", os.path.exists(archivo.ruta))

        else:
            print(f"⚠️ Archivo no encontrado: {archivo.ruta}")
            print(f"Ruta en DB: {archivo.ruta}")
            print("¿Existe?", os.path.exists(archivo.ruta))


    db.session.commit()
    print("🎉 Todos los hashes han sido recalculados.")
