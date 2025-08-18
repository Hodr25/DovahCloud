from functools import wraps
from flask import session, redirect, url_for, flash
from pdf2image import convert_from_path
from PIL import Image
import hashlib
import subprocess
import os

def guardar_miniatura_si_es_imagen(ruta_original, ruta_destino, tipo_mime):
    try:
        if not tipo_mime.startswith('image/'):
            return False  # No es imagen, omitir

        with Image.open(ruta_original) as im:
            im.convert('RGB').thumbnail((300, 300))
            im.save(ruta_destino, format='JPEG')
        return True
    except Exception as e:
        print(f"⚠️ Error generando miniatura para {ruta_original}: {e}")
        return False

def convertir_doc_a_pdf(ruta_doc, carpeta_salida):
    print(f"🔁 Convirtiendo Word a PDF: {ruta_doc}")
    try:
        subprocess.run([
            'libreoffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', carpeta_salida,
            ruta_doc
        ], check=True)
        print(f"✅ Conversión completada: {os.path.basename(ruta_doc)}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al convertir Word → PDF: {e}")
        return False

def convertir_video_a_audio(ruta_video, carpeta_salida, formato='mp3'):
    nombre_base = os.path.splitext(os.path.basename(ruta_video))[0]
    salida = os.path.join(carpeta_salida, f"{nombre_base}.{formato}")

    print(f"🔁 Extrayendo audio de: {ruta_video}")
    try:
        subprocess.run([
            'ffmpeg',
            '-i', ruta_video,
            '-q:a', '0',
            '-map', 'a',
            salida
        ], check=True)
        print(f"✅ Audio generado: {salida}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al convertir video → audio: {e}")
        return False

def login_requerido(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        if 'usuario_id' not in session:
            flash("🔒 Debes iniciar sesión.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorada

def usuario_puede_ver(archivo):
    if archivo.fecha_eliminado:
        return False
    if archivo.es_privado:
        return session.get('acceso_privado', False)
    return True

def generar_miniatura_pdf(ruta_pdf, ruta_destino):
    try:
        paginas = convert_from_path(ruta_pdf, first_page=1, last_page=1, size=(300, None))
        if paginas:
            paginas[0].save(ruta_destino, 'JPEG')
            return True
    except Exception as e:
        print(f"⚠️ Error al generar miniatura PDF: {e}")
    return False

def generar_miniatura_video(ruta_video, ruta_destino):
    try:
        comando = [
            'ffmpeg', '-y',
            '-i', ruta_video,
            '-ss', '00:00:03',
            '-vframes', '1',
            '-vf', 'scale=320:-1',
            ruta_destino
        ]
        subprocess.run(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return os.path.exists(ruta_destino)
    except Exception as e:
        print(f"🎥 Error al generar miniatura video: {e}")
        return False

def calcular_hash(ruta_archivo, algoritmo='md5'):
    hash_func = hashlib.new(algoritmo)
    try:
        with open(ruta_archivo, 'rb') as f:
            for bloque in iter(lambda: f.read(4096), b""):
                hash_func.update(bloque)
        return hash_func.hexdigest()
    except Exception as e:
        print(f"⚠️ Error calculando hash de {ruta_archivo}: {e}")
        return None
