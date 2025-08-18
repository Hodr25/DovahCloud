from flask import Flask, render_template, request, redirect, url_for, session, abort, send_file, jsonify, send_from_directory, flash
from flask_migrate import Migrate
from datetime import datetime, timedelta
from sqlalchemy import func
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from PIL import Image
from config import Config
from models import Archivo, Etiqueta, Usuario, db, archivo_etiqueta, favoritos, Playlist, playlist_archivo, Bloc, bloc_compartido
from utils import (
    guardar_miniatura_si_es_imagen,
    convertir_doc_a_pdf,
    convertir_video_a_audio,
    login_requerido,
    usuario_puede_ver,
    generar_miniatura_pdf,
    generar_miniatura_video,
    calcular_hash
)
from os import listdir
import subprocess
import os
import mimetypes
import hashlib
import yt_dlp
import tempfile

app = Flask(__name__, static_url_path="/media", static_folder="uploads/DovahCloud")
app.secret_key = 'dragonborn'
app.config.from_object(Config)

migrate = Migrate(app, db)

db.init_app(app)

# Crear tablas al iniciar si no existen
with app.app_context():
    db.create_all()

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip().lower()
        contraseña = request.form['contraseña']
        avatar = request.form.get('avatar', 'default_avatar.png')
        acceso_privado = bool(request.form.get('acceso_privado'))

        # Verificar si el usuario ya existe
        if Usuario.query.filter_by(nombre=nombre).first():
            flash("❌ Ese nombre de usuario ya está en uso.")
            return redirect(url_for('registro'))

        nuevo_usuario = Usuario(
            nombre=nombre,
            avatar=avatar,
            acceso_privado=acceso_privado
        )
        nuevo_usuario.establecer_contraseña(contraseña)

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("✅ Usuario registrado correctamente.")
        return redirect(url_for('login'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip().lower()
        contraseña = request.form['contraseña']

        usuario = Usuario.query.filter_by(nombre=nombre).first()
        if usuario and usuario.verificar_contraseña(contraseña):
            session['usuario_id'] = usuario.id
            session['usuario_nombre'] = usuario.nombre
            session['avatar'] = usuario.avatar
            session['es_admin'] = usuario.es_admin
            session['acceso_privado'] = usuario.acceso_privado

            flash(f"✅ ¡Bienvenido, {usuario.nombre}!")
            return redirect(url_for('ver_archivos'))
        else:
            flash("❌ Usuario o contraseña incorrectos.")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("👋 Sesión cerrada correctamente.")
    return redirect(url_for('login'))

@app.route('/privado', methods=['GET', 'POST'])
@login_requerido
def zona_privada():
    clave_correcta = 'dragonborn'

    if request.method == 'POST':
        if request.form.get('clave') == clave_correcta:
            session['acceso_privado'] = True
            flash("🔓 Acceso concedido a la zona privada")
            return redirect(url_for('zona_privada'))
        else:
            return render_template('privado_login.html', error=True)

    if not session.get('acceso_privado'):
        return render_template('privado_login.html')

    return render_template('zona_privada.html')

@app.route("/mi_playlist")
@login_requerido
def mi_playlist():
    playlists = Playlist.query.filter_by(usuario_id=session.get('usuario_id')).all()
    return render_template("mi_playlist.html", playlists=playlists)

@app.route("/crear_playlist", methods=["POST"])
@login_requerido
def crear_playlist():
    nombre = request.form.get("nombre")
    if nombre:
        nueva = Playlist(nombre=nombre, usuario_id=session.get('usuario_id'))
        db.session.add(nueva)
        db.session.commit()
        flash("🎉 Playlist creada con éxito", "success")
    return redirect(url_for("mi_playlist"))

@app.route("/añadir_a_playlist", methods=["POST"])
@login_requerido
def añadir_a_playlist():
    archivo_id = request.form.get("archivo_id")
    playlist_id = request.form.get("playlist_id")
    playlist = Playlist.query.get(playlist_id)
    archivo = Archivo.query.get(archivo_id)
    if playlist and archivo and archivo not in playlist.archivos:
        playlist.archivos.append(archivo)
        db.session.commit()
        flash(f"✔️ Añadido '{archivo.nombre}' a la playlist '{playlist.nombre}'", "success")
    return redirect(request.referrer or url_for("archivos"))

@app.route('/admin')
@login_requerido
def panel_admin():
    if not session.get('es_admin'):
        abort(403)

    usuarios = Usuario.query.all()
    return render_template('panel_admin.html', usuarios=usuarios)

@app.route('/admin/editar/<int:id>', methods=['GET', 'POST'])
@login_requerido
def editar_usuario(id):
    if not session.get('es_admin'):
        abort(403)

    admin_id = session.get('usuario_id')
    usuario = Usuario.query.get_or_404(id)

    if request.method == 'POST':
        usuario.acceso_privado = bool(request.form.get('acceso_privado'))

        nueva_pass = request.form.get('nueva_contraseña')
        if nueva_pass:
            usuario.hashed_password = generate_password_hash(nueva_pass)

        if usuario.id != admin_id:
            usuario.es_admin = bool(request.form.get('es_admin'))

        db.session.commit()
        flash("✅ Usuario actualizado correctamente.")
        return redirect(url_for('panel_admin'))

    return render_template('editar_usuario.html', usuario=usuario)

@app.route('/upload', methods=['GET', 'POST'])
@login_requerido
def upload():
    if request.method == 'POST':
        archivos = request.files.getlist('archivos')
        if not archivos:
            flash("No se seleccionó ningún archivo.")
            return redirect(url_for('upload'))

        convertir_pdf = request.form.get('convertir_pdf')
        convertir_audio = request.form.get('convertir_audio')

        for archivo_subido in archivos:
            if not archivo_subido or archivo_subido.filename == '':
                continue

            filename = secure_filename(archivo_subido.filename)
            carpeta_destino = app.config['UPLOAD_FOLDER']
            ruta = os.path.join(carpeta_destino, filename)
            thumb_path = os.path.join(carpeta_destino, f"thumb_{filename}")

            archivo_subido.save(ruta)
            tipo_detectado = mimetypes.guess_type(ruta)[0] or archivo_subido.mimetype or 'application/octet-stream'
            tamaño = os.path.getsize(ruta)

            if tipo_detectado == 'application/pdf':
                generar_miniatura_pdf(ruta, thumb_path)
            elif tipo_detectado.startswith('video/'):
                generar_miniatura_video(ruta, thumb_path)
            else:
                guardar_miniatura_si_es_imagen(ruta, thumb_path, tipo_detectado)

            nuevo = Archivo(nombre=filename, ruta=ruta, tipo=tipo_detectado, tamaño=tamaño)
            db.session.add(nuevo)

            ext = os.path.splitext(filename)[1].lower()
            convertibles = ['.doc', '.docx', '.odt', '.ppt', '.pptx', '.xls', '.xlsx']

            if convertir_pdf and ext in convertibles:
                convertir_doc_a_pdf(ruta, carpeta_destino)

            if convertir_audio and tipo_detectado.startswith('video/'):
                convertir_video_a_audio(ruta, carpeta_destino)

        db.session.commit()
        flash(f"✅ {len(archivos)} archivo(s) subido(s) correctamente.")
        return redirect(url_for('ver_archivos'))

    return render_template('upload.html')

@app.route('/favorito/<int:archivo_id>', methods=['POST'])
@login_requerido
def toggle_favorito(archivo_id):
    archivo = Archivo.query.get_or_404(archivo_id)
    usuario = Usuario.query.get_or_404(session['usuario_id'])

    if archivo in usuario.favoritos:
        usuario.favoritos.remove(archivo)
        db.session.commit()
        flash("❌ Eliminado de favoritos.")
    else:
        usuario.favoritos.append(archivo)
        db.session.commit()
        flash("⭐ Añadido a favoritos.")

    return redirect(request.referrer or url_for('ver_archivos'))

@app.route('/favoritos')
@login_requerido
def ver_favoritos():
    usuario = Usuario.query.get_or_404(session['usuario_id'])
    return render_template('favoritos.html', archivos=usuario.favoritos)

@app.route('/papelera')
@login_requerido
def papelera():
    ahora = datetime.utcnow()
    archivos = Archivo.query.filter(Archivo.fecha_eliminado != None).order_by(Archivo.fecha_eliminado.desc()).all()
    return render_template('papelera.html', archivos=archivos, ahora=ahora)

@app.route('/restaurar/<int:id>', methods=['POST'])
@login_requerido
def restaurar_archivo(id):
    archivo = Archivo.query.get_or_404(id)
    if archivo.fecha_eliminado is None:
        flash("Este archivo no estaba en la papelera.")
    else:
        archivo.fecha_eliminado = None
        db.session.commit()
        flash("✅ Archivo restaurado correctamente.")
    return redirect(url_for('papelera'))

@app.cli.command("limpiar_papelera")
def limpiar_papelera():
    now = datetime.utcnow()
    log_path = os.path.join('logs', 'limpieza_papelera.txt')
    os.makedirs('logs', exist_ok=True)

    limite = now - timedelta(days=5)
    archivos = Archivo.query.filter(
        Archivo.fecha_eliminado != None,
        Archivo.fecha_eliminado <= limite
    ).all()

    with open(log_path, 'a', encoding='utf-8') as log:
        log.write(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] Limpieza iniciada\n")

        eliminados = 0
        for archivo in archivos:
            try:
                if os.path.exists(archivo.ruta):
                    os.remove(archivo.ruta)
                db.session.delete(archivo)
                eliminados += 1
                log.write(f" - 🗑️ {archivo.nombre} eliminado\n")
            except Exception as e:
                log.write(f" - ⚠️ Error con {archivo.nombre}: {e}\n")

        db.session.commit()
        log.write(f"✅ Total eliminados: {eliminados}\n")

    print(f"🧹 Limpieza completada. {eliminados} archivos purgados.")

@app.route('/descargar_youtube', methods=['GET', 'POST'])
@login_requerido
def descargar_youtube():
    if request.method == 'POST':
        url = request.form.get('url')
        formato = request.form.get('formato')
        accion = request.form.get('accion')

        if not url or not formato or not accion:
            flash("Faltan campos obligatorios.")
            return redirect(url_for('descargar_youtube'))

        session['yt_info'] = {
            'url': url,
            'formato': formato,
            'accion': accion
        }

        return redirect(url_for('procesar_youtube'))

    return render_template('descargar_youtube.html')

@app.route('/procesar_youtube')
@login_requerido
def procesar_youtube():
    info = session.get('yt_info')
    if not info:
        flash("No se encontró la información de descarga.")
        return redirect(url_for('descargar_youtube'))

    url = info['url']
    formato = info['formato']
    accion = info['accion']

    temp_dir = tempfile.mkdtemp()
    output_path = f"{temp_dir}/%(title).80s.%(ext)s"

    ydl_opts = {
        'outtmpl': output_path,
        'quiet': True,
        'format': 'bestaudio/best' if formato == 'audio' else 'best',
        'postprocessors': []
    }

    if formato == 'audio':
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info_dict)
        if formato == 'audio':
            filename = filename.rsplit('.', 1)[0] + '.mp3'

    if accion == 'descargar':
        return send_file(filename, as_attachment=True)

    session['archivo_youtube'] = filename
    session['nombre_youtube'] = info_dict.get('title', 'archivo_youtube')
    session['tipo_youtube'] = 'audio/mpeg' if formato == 'audio' else 'video/mp4'
    return redirect(url_for('subida_desde_youtube'))

@app.route('/debug-thumb/<filename>')
def debug_thumb(filename):
    from flask import send_from_directory
    return send_from_directory("uploads/DovahCloud/Tilok", filename)

@app.context_processor
def inyectar_funciones_utiles():
    def get_thumb_url(archivo):
        folder = 'Tilok/' if archivo.es_privado else ''
        return f"/media/{folder}thumb_{archivo.nombre}.jpg"

    def etiquetas_visibles():
        if session.get('acceso_privado'):
            etiquetas = Etiqueta.query.order_by(Etiqueta.nombre).all()
        else:
            etiquetas = Etiqueta.query.filter_by(es_privada=False).order_by(Etiqueta.nombre).all()

        top_etiquetas = (
            db.session.query(Etiqueta, func.count(Archivo.id))
            .join(Etiqueta.archivos)
            .filter(Archivo.es_privado == False, Etiqueta.es_privada == False)
            .group_by(Etiqueta.id)
            .order_by(func.count(Archivo.id).desc())
            .limit(20)
            .all()
        )
        return dict(top_etiquetas=top_etiquetas)

    cola_ids = session.get('cola_repro', [])
    cantidad_cola = len(cola_ids)

    return {
        'usuario_puede_ver': usuario_puede_ver,
        'get_thumb_url': get_thumb_url,
        'cantidad_cola': cantidad_cola,
        **etiquetas_visibles()
    }

@app.route('/')
def inicio():
    if session.get('acceso_privado'):
        etiquetas = Etiqueta.query.order_by(Etiqueta.nombre).all()
    else:
        etiquetas = Etiqueta.query.filter_by(es_privada=False).order_by(Etiqueta.nombre).all()

    top_etiquetas = (
        db.session.query(Etiqueta, func.count(Archivo.id).label('cantidad'))
        .join(Etiqueta.archivos)
        .filter(Archivo.es_privado == False, Etiqueta.es_privada == False)
        .group_by(Etiqueta.id)
        .order_by(func.count(Archivo.id).desc())
        .limit(5)
        .all()
    )

    return render_template('inicio.html', top_etiquetas=top_etiquetas)

@app.route('/archivos')
@login_requerido
def ver_archivos():
    orden = request.args.get('orden', '')

    query = Archivo.query.filter(Archivo.fecha_eliminado == None, Archivo.es_privado == False)

    ordenes = {
        'recientes': Archivo.fecha_subida.desc(),
        'antiguos': Archivo.fecha_subida.asc(),
        'peso_desc': Archivo.tamaño.desc(),
        'peso_asc': Archivo.tamaño.asc(),
        'tipo': Archivo.tipo.asc()
    }

    orden_campo = ordenes.get(orden)
    if orden_campo is not None:
        query = query.order_by(orden_campo)
    else:
        query = query.order_by(Archivo.fecha_subida.desc())

    archivos = query.all()

    try:
        archivos_en_media = set(listdir(app.config['UPLOAD_FOLDER']))
    except FileNotFoundError:
        archivos_en_media = set()

    favoritos_ids = []
    playlists_usuario = []

    if 'usuario_id' in session:
        usuario = Usuario.query.get(session['usuario_id'])
        favoritos_ids = [a.id for a in usuario.favoritos]
        playlists_usuario = Playlist.query.filter_by(usuario_id=usuario.id).all()

    return render_template("archivos.html", archivos=archivos, playlists_usuario=playlists_usuario)

@app.route('/archivo/<int:id>')
@login_requerido
def detalle_archivo(id):
    archivo = Archivo.query.get_or_404(id)

    if not usuario_puede_ver(archivo):
        abort(403)

    if archivo.es_privado:
        carpeta = app.config['PRIVATE_UPLOAD_FOLDER']
    else:
        carpeta = app.config['UPLOAD_FOLDER']

    try:
        archivos_en_media = set(os.listdir(carpeta))
    except FileNotFoundError:
        archivos_en_media = set()

    return render_template(
        'detalle.html',
        archivo=archivo,
        archivos_en_media=archivos_en_media
    )

@app.route('/archivo/<int:id>/editar_descripcion', methods=['POST'])
@login_requerido
def editar_descripcion(id):
    if not session.get('acceso_privado'):
        abort(403)
    archivo = Archivo.query.get_or_404(id)
    descripcion = request.form.get('descripcion', '').strip()
    archivo.descripcion = descripcion
    db.session.commit()
    return redirect(url_for('detalle_archivo', id=id))

@app.route('/descargar/<int:id>')
def descargar(id):
    archivo = Archivo.query.get_or_404(id)
    return send_file(archivo.ruta, as_attachment=True)

@app.route('/filtrar_privado')
@login_requerido
def filtrar_privado():
    if not session.get('acceso_privado'):
        abort(403)

    consulta = request.args.get('etiqueta', '').strip().lower()
    orden = request.args.get('orden', '')
    archivos = []

    if consulta:
        terminos = consulta.split()
        incluir = [t for t in terminos if not t.startswith('-')]
        excluir = [t[1:] for t in terminos if t.startswith('-')]

        query = db.session.query(Archivo).join(Archivo.etiquetas)

        for etiqueta in incluir:
            query = query.filter(Archivo.etiquetas.any(Etiqueta.nombre == etiqueta))
        for etiqueta in excluir:
            query = query.filter(~Archivo.etiquetas.any(Etiqueta.nombre == etiqueta))

        query = query.filter(Archivo.es_privado == True)

        ordenes = {
            'recientes': Archivo.fecha_subida.desc(),
            'antiguos': Archivo.fecha_subida.asc(),
            'peso_desc': Archivo.tamaño.desc(),
            'peso_asc': Archivo.tamaño.asc(),
            'tipo': Archivo.tipo.asc()
        }

        orden_campo = ordenes.get(orden)
        if orden_campo:
            query = query.order_by(orden_campo)

        archivos = query.distinct().all()

    return render_template('filtrar_privado.html', archivos=archivos, etiqueta_buscada=consulta)

@app.route('/etiquetas')
def ver_etiquetas():
    if session.get('acceso_privado'):
        etiquetas = Etiqueta.query.all()
    else:
        etiquetas = Etiqueta.query.filter_by(es_privada=False).all()

    etiquetas.sort(key=lambda e: (e.nombre.startswith("'"), e.nombre.lower()))

    return render_template('etiquetas.html', etiquetas=etiquetas)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_requerido
def editar_etiquetas(id):
    if session.get('acceso_privado'):
        etiquetas = Etiqueta.query.order_by(Etiqueta.nombre).all()
    else:
        etiquetas = Etiqueta.query.filter_by(es_privada=False).order_by(Etiqueta.nombre).all()

    archivo = Archivo.query.get_or_404(id)

    if request.method == 'POST':
        nuevas = request.form.get('etiqueta', '').strip()
        if nuevas:
            etiquetas_nuevas = [e.strip().lower() for e in nuevas.split(',') if e.strip()]
            for nombre in etiquetas_nuevas:
                etiqueta = Etiqueta.query.filter_by(nombre=nombre).first()
                if not etiqueta:
                    etiqueta = Etiqueta(nombre=nombre)
                    db.session.add(etiqueta)
                if etiqueta not in archivo.etiquetas:
                    archivo.etiquetas.append(etiqueta)

        for etiqueta in archivo.etiquetas[:]:
            campo = f"editar_{etiqueta.id}"
            nuevo_nombre = request.form.get(campo, '').strip().lower()
            if nuevo_nombre and nuevo_nombre != etiqueta.nombre:
                etiqueta_existente = Etiqueta.query.filter_by(nombre=nuevo_nombre).first()
                if etiqueta_existente:
                    archivo.etiquetas.remove(etiqueta)
                    if etiqueta_existente not in archivo.etiquetas:
                        archivo.etiquetas.append(etiqueta_existente)
                else:
                    etiqueta.nombre = nuevo_nombre

        etiquetas_a_eliminar = request.form.getlist('eliminar')
        for id_str in etiquetas_a_eliminar:
            etiqueta = Etiqueta.query.get(int(id_str))
            if etiqueta and etiqueta in archivo.etiquetas:
                archivo.etiquetas.remove(etiqueta)

        db.session.commit()
        return redirect(url_for('detalle_archivo', id=archivo.id))

    return render_template('editar.html', archivo=archivo)

@app.route('/eliminar/<int:id>', methods=['GET', 'POST'])
@login_requerido
def eliminar(id):
    archivo = Archivo.query.get_or_404(id)

    if request.method == 'POST':
        if archivo.fecha_eliminado:
            flash("Este archivo ya estaba en la papelera.")
            return redirect(url_for('ver_archivos'))

        archivo.fecha_eliminado = datetime.utcnow()
        db.session.commit()

        flash("🗑️ Archivo movido a la papelera. Será eliminado definitivamente en 5 días.")
        return redirect(url_for('ver_archivos'))

    return render_template('confirmar_eliminacion.html', archivo=archivo)

@app.route('/buscar')
def buscar():
    consulta = request.args.get('q', '').strip().lower()
    if not consulta:
        return render_template('filtro.html', archivos=[], consulta='')

    terminos = consulta.split()
    etiquetas_incluir = [t for t in terminos if not t.startswith('-')]
    etiquetas_excluir = [t[1:] for t in terminos if t.startswith('-')]

    query = db.session.query(Archivo).join(Archivo.etiquetas)

    for etiqueta in etiquetas_incluir:
        query = query.filter(Archivo.etiquetas.any(Etiqueta.nombre == etiqueta))
    for etiqueta in etiquetas_excluir:
        query = query.filter(~Archivo.etiquetas.any(Etiqueta.nombre == etiqueta))

    # Limitar resultados si el usuario no tiene acceso privado
    if not session.get('acceso_privado'):
        query = query.filter(Archivo.es_privado == False)

    archivos = query.distinct().all()
    return render_template('filtro.html', archivos=archivos, consulta=consulta)

@app.route('/sugerencias_etiquetas')
def sugerencias_etiquetas():
    texto = request.args.get('q', '').strip().lower()
    if not texto:
        return jsonify([])

    ultima = texto.split()[-1]
    es_exclusion = ultima.startswith('-')
    parcial = ultima[1:] if es_exclusion else ultima

    query = (
        db.session.query(Etiqueta.nombre, func.count(Archivo.id).label('cantidad'))
        .select_from(Etiqueta)
        .join(archivo_etiqueta, Etiqueta.id == archivo_etiqueta.c.etiqueta_id)
        .join(Archivo, archivo_etiqueta.c.archivo_id == Archivo.id)
        .filter(Etiqueta.nombre.ilike(f'{parcial}%'))
    )

    if not session.get('acceso_privado'):
        query = query.filter(Etiqueta.es_privada == False, Archivo.es_privado == False)

    resultados = (
        query.group_by(Etiqueta.nombre)
             .having(func.count(Archivo.id) > 0)
             .order_by(
                 db.case(
                     (Etiqueta.nombre.startswith("'"), 1),
                     else_=0
                 ),
                 Etiqueta.nombre.asc()
             )
             .limit(10)
             .all()
    )

    sugerencias = [
        {'nombre': f"-{nombre}" if es_exclusion else nombre, 'cantidad': cantidad}
        for nombre, cantidad in resultados
    ]

    return jsonify(sugerencias)

@app.route('/media/<nombre>')
def media(nombre):
    archivo_nombre = nombre.replace('thumb_', '') if nombre.startswith('thumb_') else nombre
    archivo = Archivo.query.filter_by(nombre=archivo_nombre).first_or_404()

    # Protegemos archivos privados
    if archivo.es_privado and not session.get('acceso_privado'):
        abort(403)

    # Determinar carpeta de origen
    carpeta_base = app.config['PRIVATE_UPLOAD_FOLDER'] if archivo.es_privado else app.config['UPLOAD_FOLDER']
    ruta_archivo = os.path.join(carpeta_base, nombre)

    if not os.path.isfile(ruta_archivo):
        print(f"[⚠️] Archivo no encontrado físicamente: {ruta_archivo}")
        abort(404)

    # Detectar tipo MIME real si no se trata de una imagen miniatura
    mimetype = mimetypes.guess_type(ruta_archivo)[0] or 'application/octet-stream'
    return send_file(ruta_archivo, mimetype=mimetype, as_attachment=False)

@app.route('/multimedia')
def estado_multimedia():
    archivos = Archivo.query.filter_by(es_privado=False).all()
    analisis = []

    for archivo in archivos:
        if archivo.tipo.startswith(('video/', 'audio/')):
            info = analizar_codec(archivo)
            analisis.append({
                'archivo': archivo,
                'info': info
            })

    return render_template('multimedia.html', analisis=analisis)

@app.route('/convertir/<int:id>')
def convertir(id):
    archivo = Archivo.query.get_or_404(id)
    convertir_archivo(archivo)
    return redirect(url_for('detalle_archivo', id=archivo.id))

@app.route('/galeria')
def galeria():
    imagenes = Archivo.query.filter(
        Archivo.tipo.like('image/%'),
        Archivo.es_privado == False
    ).order_by(Archivo.fecha_subida.desc()).all()
    return render_template('galeria.html', imagenes=imagenes)

@app.route('/videos')
def galeria_videos():
    videos = Archivo.query.filter(
        Archivo.tipo.like('video/%'),
        Archivo.es_privado == False
    ).order_by(Archivo.fecha_subida.desc()).all()
    return render_template('videos.html', videos=videos)

@app.route('/regenerar_thumbs')
@login_requerido
def regenerar_thumbs():
    procesadas = 0
    omitidas = 0
    errores = 0

    archivos = Archivo.query.filter(Archivo.fecha_eliminado == None).all()

    for archivo in archivos:
        nombre = archivo.nombre
        ruta_origen = archivo.ruta
        carpeta = app.config['PRIVATE_UPLOAD_FOLDER'] if archivo.es_privado else app.config['UPLOAD_FOLDER']
        thumb_path = os.path.join(carpeta, f"thumb_{nombre}.jpg")

        if os.path.exists(thumb_path):
            omitidas += 1
            continue

        tipo = archivo.tipo or mimetypes.guess_type(nombre)[0] or ''

        try:
            if tipo == 'application/pdf':
                exito = generar_miniatura_pdf(ruta_origen, thumb_path)
            elif tipo.startswith('video/'):
                exito = generar_miniatura_video(ruta_origen, thumb_path)
            elif tipo.startswith('image/'):
                exito = guardar_miniatura_si_es_imagen(ruta_origen, thumb_path, tipo)
            else:
                exito = False

            if exito:
                procesadas += 1
            else:
                errores += 1
                print(f"⚠️ No se pudo generar miniatura para: {nombre}")
        except Exception as e:
            errores += 1
            print(f"💥 Error procesando {nombre}: {e}")

        print("Analizando: {} ({}) --> {}".format(archivo.nombre, tipo, archivo.ruta))
        print(f"➡️ Miniatura en: {thumb_path}")
        print("📦 ¿Archivo original existe?", os.path.exists(ruta_origen))
        print("📦 ¿Miniatura ya existe?", os.path.exists(thumb_path))

        return (
            f"<h2>🔁 Regeneración completada</h2>"
            f"<p>✅ Miniaturas nuevas: {procesadas}</p>"
            f"<p>⏭️ Ya existentes: {omitidas}</p>"
            f"<p>⚠️ Fallidas: {errores}</p>"
        )

@app.route('/regenerar_thumbs_fisico')
@login_requerido
def regenerar_thumbs_fisico():
    carpeta = app.config['UPLOAD_FOLDER']
    procesadas = 0
    omitidas = 0
    errores = 0

    for nombre in os.listdir(carpeta):
        if nombre.startswith('thumb_'):
            continue
        ruta = os.path.join(carpeta, nombre)
        if not os.path.isfile(ruta):
            continue

        thumb_path = os.path.join(carpeta, f'thumb_{nombre}.jpg')
        if os.path.exists(thumb_path):
            omitidas += 1
            continue

        tipo = mimetypes.guess_type(nombre)[0] or ''
        print(f"🧪 {nombre} → tipo: {tipo}")

        try:
            if tipo == 'application/pdf':
                ok = generar_miniatura_pdf(ruta, thumb_path)
            elif tipo.startswith('video/'):
                ok = generar_miniatura_video(ruta, thumb_path)
            elif tipo.startswith('image/'):
                ok = guardar_miniatura_si_es_imagen(ruta, thumb_path, tipo)
            else:
                ok = False

            if ok:
                procesadas += 1
                print(f"✅ Miniatura generada: {thumb_path}")
            else:
                errores += 1
                print(f"⚠️ Sin miniatura: {nombre}")
        except Exception as e:
            errores += 1
            print(f"💥 Error con {nombre}: {e}")

    return (
        f"<h2>🔁 Miniaturas generadas (basado en disco)</h2>"
        f"<p>✅ Nuevas: {procesadas}</p>"
        f"<p>⏭️ Ya existentes: {omitidas}</p>"
        f"<p>⚠️ Fallidas: {errores}</p>"
    )

@app.route('/privado/archivos')
@login_requerido
def ver_archivos_privados():
    if not session.get('acceso_privado'):
        return redirect(url_for('zona_privada'))

    etiquetas = Etiqueta.query.order_by(Etiqueta.nombre).all()
    archivos = Archivo.query.filter_by(es_privado=True).order_by(Archivo.fecha_subida.desc()).all()

    try:
        archivos_en_media = set(os.listdir(app.config['PRIVATE_UPLOAD_FOLDER']))
    except FileNotFoundError:
        archivos_en_media = set()

    return render_template('privado.html', archivos=archivos, archivos_en_media=archivos_en_media)

@app.route('/upload_privado', methods=['GET', 'POST'])
@login_requerido
def upload_privado():
    if request.method == 'POST':
        archivos = request.files.getlist('archivos')
        if not archivos:
            flash("❌ No se seleccionó ningún archivo.")
            return redirect(url_for('upload_privado'))

        etiquetas_raw = request.form.get('etiqueta', '')
        es_privada = 'privada' in request.form
        nombres_etiquetas = [e.strip() for e in etiquetas_raw.split(',') if e.strip()]

        carpeta_destino = app.config['PRIVATE_UPLOAD_FOLDER']
        guardados = 0

        for archivo_subido in archivos:
            if not archivo_subido or archivo_subido.filename == '':
                continue

            filename = secure_filename(archivo_subido.filename)
            ruta = os.path.join(carpeta_destino, filename)
            archivo_subido.save(ruta)

            tipo_detectado = mimetypes.guess_type(ruta)[0] or archivo_subido.mimetype or 'application/octet-stream'
            tamaño = os.path.getsize(ruta)
            archivo_hash = calcular_hash(ruta)
            thumb_path = os.path.join(carpeta_destino, f"thumb_{filename}.jpg")

            if tipo_detectado == 'application/pdf':
                generar_miniatura_pdf(ruta, thumb_path)
            elif tipo_detectado.startswith('video/'):
                generar_miniatura_video(ruta, thumb_path)
            elif tipo_detectado.startswith('image/'):
                guardar_miniatura_si_es_imagen(ruta, thumb_path, tipo_detectado)

            archivo = Archivo(
                nombre=filename,
                ruta=ruta,
                tipo=tipo_detectado,
                fecha_subida=datetime.now(),
                tamaño=tamaño,
                es_privado=True,
                hash_archivo=archivo_hash
            )

            for nombre_et in nombres_etiquetas:
                etiqueta = Etiqueta.query.filter_by(nombre=nombre_et).first()
                if not etiqueta:
                    etiqueta = Etiqueta(nombre=nombre_et, es_privada=es_privada)
                    db.session.add(etiqueta)
                archivo.etiquetas.append(etiqueta)

            db.session.add(archivo)
            guardados += 1

        db.session.commit()
        flash(f"✅ {guardados} archivo(s) subido(s) a zona privada.")
        return redirect(url_for('ver_archivos_privados'))

    return render_template('upload_privado.html')

def analizar_codec(archivo):
    ruta = archivo.ruta
    resultado = {
        'video': False,
        'audio': False,
        'video_codec': None,
        'audio_codec': None,
        'recomendado': True
    }

    try:
        datos = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=codec_name', '-of', 'default=nw=1', ruta],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if datos.stdout:
            resultado['video'] = True
            resultado['video_codec'] = datos.stdout.strip().split('=')[-1]

        datos = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=codec_name', '-of', 'default=nw=1', ruta],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if datos.stdout:
            resultado['audio'] = True
            resultado['audio_codec'] = datos.stdout.strip().split('=')[-1]

        # Verificamos si es un formato recomendado
        if resultado['video'] and resultado['video_codec'] != 'h264':
            resultado['recomendado'] = False
        if resultado['audio'] and resultado['audio_codec'] not in ['aac', 'mp3']:
            resultado['recomendado'] = False

    except Exception as e:
        resultado['error'] = str(e)

    return resultado

def convertir_archivo(archivo):
    origen = archivo.ruta
    destino = origen  # Sobrescribe el original

    # Si es audio WMA → MP3
    if archivo.tipo.startswith('audio/') and archivo.nombre.lower().endswith('.wma'):
        nuevo_nombre = archivo.nombre.rsplit('.', 1)[0] + '.mp3'
        destino = os.path.join(app.config['UPLOAD_FOLDER'], nuevo_nombre)

        comando = [
            'ffmpeg', '-i', origen,
            '-acodec', 'libmp3lame', '-y',
            destino
        ]
        subprocess.run(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Actualizar en base de datos
        archivo.nombre = nuevo_nombre
        archivo.ruta = destino
        archivo.tipo = 'audio/mpeg'

    # Si es vídeo con códec incompatible → H.264 + AAC
    elif archivo.tipo.startswith('video/'):
        nuevo_nombre = archivo.nombre.rsplit('.', 1)[0] + '_compatible.mp4'
        destino = os.path.join(app.config['UPLOAD_FOLDER'], nuevo_nombre)

        comando = [
            'ffmpeg', '-i', origen,
            '-c:v', 'libx264', '-c:a', 'aac',
            '-preset', 'fast', '-crf', '23',
            '-y', destino
        ]
        subprocess.run(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        archivo.nombre = nuevo_nombre
        archivo.ruta = destino
        archivo.tipo = 'video/mp4'

    db.session.commit()

@app.route('/playlist/<int:id>')
@login_requerido
def ver_playlist(id):
    playlist = Playlist.query.get_or_404(id)

    if playlist.usuario_id != session.get('usuario_id'):
        abort(403)

    return render_template('playlist_detalle.html', playlist=playlist)

@app.route('/playlist/<int:playlist_id>/quitar/<int:archivo_id>', methods=['POST'])
@login_requerido
def quitar_de_playlist(playlist_id, archivo_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.usuario_id != session.get('usuario_id'):
        abort(403)

    archivo = Archivo.query.get_or_404(archivo_id)
    if archivo in playlist.archivos:
        playlist.archivos.remove(archivo)
        db.session.commit()
        flash(f"❌ Quitado '{archivo.nombre}' de la playlist.")
    return redirect(url_for('ver_playlist', id=playlist.id))

@app.route('/playlist/<int:id>/editar', methods=['GET', 'POST'])
@login_requerido
def editar_playlist(id):
    playlist = Playlist.query.get_or_404(id)

    if playlist.usuario_id != session.get('usuario_id'):
        abort(403)

    if request.method == 'POST':
        nuevo_nombre = request.form.get('nombre', '').strip()
        eliminar = request.form.get('eliminar')

        if eliminar == '1':
            db.session.delete(playlist)
            db.session.commit()
            flash("🗑️ Playlist eliminada con éxito.")
            return redirect(url_for('mi_playlist'))

        if nuevo_nombre:
            playlist.nombre = nuevo_nombre
            db.session.commit()
            flash("✅ Nombre de playlist actualizado.")

    return render_template('editar_playlist.html', playlist=playlist)

@app.route('/reproductor/iniciar/<int:playlist_id>')
@login_requerido
def iniciar_reproductor(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.usuario_id != session.get('usuario_id'):
        abort(403)

    archivo_ids = [a.id for a in playlist.archivos]
    if not archivo_ids:
        flash("Esta playlist no contiene archivos.")
        return redirect(url_for('ver_playlist', id=playlist_id))

    # Estado inicial del reproductor
    session['reproductor'] = {
        'playlist_id': playlist_id,
        'modo': 'normal',
        'cola': archivo_ids,
        'actual': archivo_ids[0]
    }

    return redirect(url_for('ver_reproductor'))

@app.route('/reproductor')
@login_requerido
def ver_reproductor():
    estado = session.get('reproductor')
    if not estado:
        flash("No hay reproducción en curso.")
        return redirect(url_for('mi_playlist'))

    playlist = Playlist.query.get_or_404(estado['playlist_id'])
    actual = Archivo.query.get_or_404(estado['actual'])

    return render_template('reproductor.html', archivo=actual, playlist=playlist, estado=estado)

@app.route('/reproductor/siguiente')
@login_requerido
def siguiente_reproductor():
    estado = session.get('reproductor')
    if not estado or not estado.get('cola'):
        return redirect(url_for('ver_reproductor'))

    cola = estado['cola']
    actual_id = estado['actual']
    if actual_id in cola:
        idx = cola.index(actual_id)
        siguiente_idx = (idx + 1) % len(cola)
        estado['actual'] = cola[siguiente_idx]
        session['reproductor'] = estado

    return redirect(url_for('ver_reproductor'))

@app.route('/reproductor/anterior')
@login_requerido
def anterior_reproductor():
    estado = session.get('reproductor')
    if not estado or not estado.get('cola'):
        return redirect(url_for('ver_reproductor'))

    cola = estado['cola']
    actual_id = estado['actual']
    if actual_id in cola:
        idx = cola.index(actual_id)
        anterior_idx = (idx - 1) % len(cola)
        estado['actual'] = cola[anterior_idx]
        session['reproductor'] = estado

    return redirect(url_for('ver_reproductor'))

@app.route('/reproductor/toggle_aleatorio', methods=['POST'])
@login_requerido
def toggle_aleatorio():
    estado = session.get('reproductor')
    if not estado:
        flash("No hay reproducción en curso.")
        return redirect(url_for('mi_playlist'))

    modo_actual = estado.get('modo', 'normal')
    cola_actual = estado.get('cola', [])
    actual_id = estado.get('actual')

    if modo_actual == 'aleatorio':
        # Restaurar orden original
        playlist = Playlist.query.get_or_404(estado['playlist_id'])
        orden = [a.id for a in playlist.archivos]
        if actual_id in orden:
            orden.remove(actual_id)
            orden.insert(0, actual_id)
        estado['cola'] = orden
        estado['modo'] = 'normal'
        flash("🔁 Modo aleatorio desactivado")
    else:
        # Activar aleatorio
        import random
        mezcla = list(cola_actual)
        if actual_id in mezcla:
            mezcla.remove(actual_id)
        random.shuffle(mezcla)
        mezcla.insert(0, actual_id)  # Mantenemos el actual al principio
        estado['cola'] = mezcla
        estado['modo'] = 'aleatorio'
        flash("🔀 Modo aleatorio activado")

    session['reproductor'] = estado
    return redirect(url_for('ver_reproductor'))

@app.route('/reproducir/cola/añadir/<int:archivo_id>', methods=['POST'])
@login_requerido
def añadir_a_cola(archivo_id):
    archivo = Archivo.query.get_or_404(archivo_id)
    if 'cola_repro' not in session:
        session['cola_repro'] = []
    if archivo_id not in session['cola_repro']:
        session['cola_repro'].append(archivo_id)
        session.modified = True
        flash(f"📥 Añadido '{archivo.nombre}' a la cola.")
    else:
        flash("Este archivo ya está en la cola.")
    return redirect(request.referrer or url_for('ver_archivos'))

@app.route('/reproducir/cola')
@login_requerido
def ver_cola():
    ids = session.get('cola_repro', [])
    archivos = Archivo.query.filter(Archivo.id.in_(ids)).all()

    # Mantener orden de la cola
    archivos_ordenados = sorted(archivos, key=lambda a: ids.index(a.id))
    return render_template('cola.html', cola=archivos_ordenados)

@app.route('/reproducir/cola/reproducir/<int:pos>')
@login_requerido
def reproducir_desde_cola(pos):
    ids = session.get('cola_repro', [])
    if not ids or pos >= len(ids):
        flash("La cola de reproducción está vacía o no tiene más archivos.")
        return redirect(url_for('ver_cola'))

    actual = Archivo.query.get_or_404(ids[pos])
    return render_template('repro_coladin.html', archivo=actual, pos=pos, total=len(ids))

@app.route('/reproducir/cola/quitar/<int:archivo_id>', methods=['POST'])
@login_requerido
def quitar_de_cola(archivo_id):
    cola = session.get('cola_repro', [])
    if archivo_id in cola:
        cola.remove(archivo_id)
        session['cola_repro'] = cola
        session.modified = True
        flash("🗑️ Archivo quitado de la cola.")
    return redirect(request.referrer or url_for('ver_cola'))

@app.route('/reproducir/cola/vaciar', methods=['POST'])
@login_requerido
def vaciar_cola():
    session['cola_repro'] = []
    session.modified = True
    flash("🧹 Cola de reproducción vaciada.")
    return redirect(url_for('ver_cola'))

@app.route('/blocs/crear', methods=['GET', 'POST'])
@login_requerido
def crear_bloc():
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        contenido = request.form.get('contenido', '').strip()
        privado = bool(request.form.get('privado'))
        publico = bool(request.form.get('publico'))

        if not titulo:
            flash("El título no puede estar vacío.")
            return redirect(url_for('crear_bloc'))

        nuevo_bloc = Bloc(
            titulo=titulo,
            contenido=contenido,
            autor_id=session.get('usuario_id'),
            privado=privado,
            publico=publico
        )
        db.session.add(nuevo_bloc)
        db.session.commit()
        flash("📓 Bloc creado con éxito.")
        return redirect(url_for('mis_blocs'))

    return render_template('crear_bloc.html')

@app.route('/mis_blocs')
@login_requerido
def mis_blocs():
    usuario_id = session.get('usuario_id')

    # Blocs propios
    propios = Bloc.query.filter_by(autor_id=usuario_id).order_by(Bloc.fecha_actualizado.desc()).all()

    # Blocs compartidos con este usuario
    usuario = Usuario.query.get_or_404(usuario_id)
    compartidos = usuario.blocs_compartidos if hasattr(usuario, 'blocs_compartidos') else []

    return render_template("mis_blocs.html", propios=propios, compartidos=compartidos)

@app.route('/bloc/<int:id>')
@login_requerido
def ver_bloc(id):
    bloc = Bloc.query.get_or_404(id)
    usuario_id = session.get('usuario_id')

    # ¿El usuario puede verlo?
    puede_ver = (
        bloc.autor_id == usuario_id or
        (not bloc.privado and bloc.publico) or
        (usuario_id in [u.id for u in bloc.invitados])
    )

    if not puede_ver:
        abort(403)

    return render_template('ver_bloc.html', bloc=bloc)

@app.route('/bloc/<int:id>/editar', methods=['GET', 'POST'])
@login_requerido
def editar_bloc(id):
    bloc = Bloc.query.get_or_404(id)
    usuario_id = session.get('usuario_id')

    # Solo el autor puede editar
    if bloc.autor_id != usuario_id:
        abort(403)

    if request.method == 'POST':
        bloc.titulo = request.form.get('titulo', '').strip()
        bloc.contenido = request.form.get('contenido', '').strip()
        bloc.privado = bool(request.form.get('privado'))
        bloc.publico = bool(request.form.get('publico'))

        if not bloc.titulo:
            flash("El título no puede estar vacío.")
            return redirect(url_for('editar_bloc', id=id))

        db.session.commit()
        flash("📝 Bloc actualizado con éxito.")
        return redirect(url_for('ver_bloc', id=id))

    return render_template('crear_bloc.html', bloc=bloc, modo_edicion=True)

@app.route('/bloc/<int:id>/compartir', methods=['GET', 'POST'])
@login_requerido
def compartir_bloc(id):
    bloc = Bloc.query.get_or_404(id)
    usuario_id = session.get('usuario_id')

    # Solo el autor puede compartirlo
    if bloc.autor_id != usuario_id:
        abort(403)

    if request.method == 'POST':
        # Aquí iría la lógica de compartir el bloc
        # Ejemplo: lista de IDs de usuarios seleccionados para compartir
        ids_invitados = request.form.getlist('invitados')
        usuarios_invitados = Usuario.query.filter(Usuario.id.in_(ids_invitados)).all()

        # Asegúrate de que bloc.invitados sea una relación tipo many-to-many
        bloc.invitados = usuarios_invitados
        db.session.commit()
        flash("🤝 Bloc compartido con éxito.")
        return redirect(url_for('ver_bloc', id=id))

    usuarios = Usuario.query.filter(Usuario.id != usuario_id).all()
    return render_template('compartir_bloc.html', bloc=bloc, usuarios=usuarios)

@app.route('/bloc/<int:id>/eliminar', methods=['POST'])
@login_requerido
def eliminar_bloc(id):
    bloc = Bloc.query.get_or_404(id)
    usuario_id = session.get('usuario_id')

    # Solo el autor puede eliminar
    if bloc.autor_id != usuario_id:
        abort(403)

    db.session.delete(bloc)
    db.session.commit()
    flash("🗑️ Bloc eliminado con éxito.")
    return redirect(url_for('mis_blocs'))

if __name__ == '__main__':
    app.run(debug=True, host='192.168.1.102', port=5000)
