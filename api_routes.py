import os
import mimetypes
from datetime import datetime
from typing import Optional

from flask import (
    Blueprint,
    jsonify,
    request,
    session,
    current_app,
    url_for,
)
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash

from models import db, Archivo, Etiqueta, Playlist, Usuario
from utils import (
    guardar_miniatura_si_es_imagen,
    convertir_doc_a_pdf,
    convertir_video_a_audio,
    generar_miniatura_pdf,
    generar_miniatura_video,
    usuario_puede_ver,
)


api_bp = Blueprint("api", __name__, url_prefix="/api")


def _current_user():
    """Return the currently authenticated user, or None."""
    user_id = session.get("usuario_id")
    if not user_id:
        return None
    return Usuario.query.get(user_id)


def _serialize_user(usuario: Usuario) -> dict:
    """Transform a Usuario instance into a JSON-safe dictionary."""
    if not usuario:
        return {}

    return {
        "id": usuario.id,
        "username": usuario.nombre,
        "avatar": usuario.avatar,
        "isAdmin": bool(usuario.es_admin),
        "hasPrivateAccess": bool(usuario.acceso_privado),
    }


def _build_media_url(archivo: Archivo, nombre: str) -> Optional[str]:
    """Create a /media URL for a given file if the file exists."""
    if archivo.es_privado and not session.get("acceso_privado"):
        return None

    carpeta_base = (
        current_app.config["PRIVATE_UPLOAD_FOLDER"]
        if archivo.es_privado
        else current_app.config["UPLOAD_FOLDER"]
    )
    ruta = os.path.join(carpeta_base, nombre)
    if not os.path.exists(ruta):
        return None
    return url_for("media", nombre=nombre)


def _serialize_archivo(archivo: Archivo, usuario: Optional[Usuario]) -> dict:
    """Transform an Archivo instance into a JSON-safe dictionary."""
    favorite_ids = {a.id for a in usuario.favoritos} if usuario else set()

    thumb_name = f"thumb_{archivo.nombre}"
    media_url = _build_media_url(archivo, archivo.nombre)
    thumb_url = _build_media_url(archivo, thumb_name)

    safe_size = 0
    if archivo.ruta and os.path.exists(archivo.ruta):
        safe_size = os.path.getsize(archivo.ruta)

    return {
        "id": archivo.id,
        "name": archivo.nombre,
        "description": archivo.descripcion or "",
        "mimeType": archivo.tipo,
        "size": safe_size,
        "uploadedAt": archivo.fecha_subida.isoformat() if archivo.fecha_subida else None,
        "isPrivate": bool(archivo.es_privado),
        "isFavorite": archivo.id in favorite_ids,
        "thumbnailUrl": thumb_url,
        "mediaUrl": media_url,
        "tags": [etiqueta.nombre for etiqueta in archivo.etiquetas],
    }


def _serialize_playlist(playlist: Playlist, usuario: Optional[Usuario]) -> dict:
    """Transform a Playlist instance into a JSON-safe dictionary."""
    return {
        "id": playlist.id,
        "name": playlist.nombre,
        "createdAt": playlist.fecha_creacion.isoformat()
        if playlist.fecha_creacion
        else None,
        "items": [
            _serialize_archivo(archivo, usuario)
            for archivo in playlist.archivos
            if not archivo.fecha_eliminado and usuario_puede_ver(archivo)
        ],
    }


@api_bp.route("/session", methods=["GET"])
def session_status():
    """Expose the authentication status for the SPA."""
    usuario = _current_user()
    if not usuario:
        return jsonify({"authenticated": False}), 200
    return jsonify({"authenticated": True, "user": _serialize_user(usuario)}), 200


@api_bp.route("/login", methods=["POST"])
def api_login():
    """Handle JSON based login requests."""
    payload = request.get_json(silent=True) or {}
    nombre = (payload.get("username") or "").strip().lower()
    contrasena = payload.get("password") or ""

    if not nombre or not contrasena:
        return jsonify({"error": "Credenciales incompletas."}), 400

    usuario = Usuario.query.filter_by(nombre=nombre).first()
    if usuario is None:
        return jsonify({"error": "Usuario o contraseña incorrectos."}), 401

    # Compat fallback for legacy attribute names without tilde characters.
    hash_attr = (
        getattr(usuario, "contrase\u00f1a_hash", None)
        or getattr(usuario, "contrasena_hash", None)
    )

    if hash_attr is None or not check_password_hash(hash_attr, contrasena):
        return jsonify({"error": "Usuario o contraseña incorrectos."}), 401

    session["usuario_id"] = usuario.id
    session["usuario_nombre"] = usuario.nombre
    session["avatar"] = usuario.avatar
    session["es_admin"] = usuario.es_admin
    session["acceso_privado"] = usuario.acceso_privado

    return jsonify({"authenticated": True, "user": _serialize_user(usuario)}), 200


@api_bp.route("/logout", methods=["POST"])
def api_logout():
    """Clear the current session when the user signs out."""
    session.clear()
    return jsonify({"authenticated": False}), 200


@api_bp.route("/files", methods=["GET"])
def api_list_files():
    """Return the accessible files for the current user."""
    usuario = _current_user()
    if not usuario:
        return jsonify({"error": "No autenticado."}), 401

    favoritos_ids = {archivo.id for archivo in usuario.favoritos}

    query = Archivo.query.filter(Archivo.fecha_eliminado.is_(None))

    if not session.get("acceso_privado"):
        query = query.filter(Archivo.es_privado.is_(False))

    search = (request.args.get("search") or "").strip()
    if search:
        wildcard = f"%{search}%"
        query = query.filter(
            or_(
                Archivo.nombre.ilike(wildcard),
                Archivo.descripcion.ilike(wildcard),
                Archivo.tipo.ilike(wildcard),
            )
        )

    tipo = (request.args.get("type") or "").strip()
    if tipo:
        query = query.filter(Archivo.tipo.ilike(f"{tipo}%"))

    only_favorites = request.args.get("favorites") == "1"
    if only_favorites:
        if not favoritos_ids:
            return jsonify([])
        query = query.filter(Archivo.id.in_(favoritos_ids))

    order = request.args.get("order", "recent")
    order_map = {
        "recent": Archivo.fecha_subida.desc(),
        "oldest": Archivo.fecha_subida.asc(),
        "name": Archivo.nombre.asc(),
        "name_desc": Archivo.nombre.desc(),
    }
    query = query.order_by(order_map.get(order, Archivo.fecha_subida.desc()))

    archivos = [
        _serialize_archivo(archivo, usuario)
        for archivo in query.all()
        if usuario_puede_ver(archivo)
    ]
    return jsonify(archivos), 200


@api_bp.route("/files/<int:archivo_id>", methods=["GET"])
def api_file_detail(archivo_id: int):
    """Return the details for a single file."""
    usuario = _current_user()
    if not usuario:
        return jsonify({"error": "No autenticado."}), 401

    archivo = Archivo.query.get_or_404(archivo_id)
    if not usuario_puede_ver(archivo):
        return jsonify({"error": "Acceso no autorizado."}), 403

    return jsonify(_serialize_archivo(archivo, usuario)), 200


@api_bp.route("/files/<int:archivo_id>/favorite", methods=["POST"])
def api_toggle_favorite(archivo_id: int):
    """Allow the SPA to toggle favorite entries."""
    usuario = _current_user()
    if not usuario:
        return jsonify({"error": "No autenticado."}), 401

    archivo = Archivo.query.get_or_404(archivo_id)
    if not usuario_puede_ver(archivo):
        return jsonify({"error": "Acceso no autorizado."}), 403

    payload = request.get_json(silent=True) or {}
    desired_state = payload.get("favorite")

    if desired_state is True:
        if archivo not in usuario.favoritos:
            usuario.favoritos.append(archivo)
            db.session.commit()
    elif desired_state is False:
        if archivo in usuario.favoritos:
            usuario.favoritos.remove(archivo)
            db.session.commit()
    else:
        # Toggle if no explicit state is provided.
        if archivo in usuario.favoritos:
            usuario.favoritos.remove(archivo)
        else:
            usuario.favoritos.append(archivo)
        db.session.commit()

    return jsonify({"id": archivo.id, "favorite": archivo in usuario.favoritos}), 200


@api_bp.route("/files", methods=["POST"])
def api_upload_files():
    """Handle multi-file uploads triggered from the SPA."""
    usuario = _current_user()
    if not usuario:
        return jsonify({"error": "No autenticado."}), 401

    archivos = request.files.getlist("files")
    if not archivos:
        return jsonify({"error": "No se proporcionaron archivos."}), 400

    convertir_pdf = request.form.get("convertToPdf") == "1"
    convertir_audio = request.form.get("convertToAudio") == "1"
    marcar_privado = request.form.get("private") == "1"

    carpeta_destino = (
        current_app.config["PRIVATE_UPLOAD_FOLDER"]
        if marcar_privado
        else current_app.config["UPLOAD_FOLDER"]
    )
    os.makedirs(carpeta_destino, exist_ok=True)

    guardados = []

    for archivo_subido in archivos:
        if not archivo_subido or not archivo_subido.filename:
            continue

        filename = secure_filename(archivo_subido.filename)
        ruta = os.path.join(carpeta_destino, filename)
        thumb_path = os.path.join(carpeta_destino, f"thumb_{filename}")

        archivo_subido.save(ruta)
        tipo_detectado = (
            mimetypes.guess_type(ruta)[0] or archivo_subido.mimetype or "application/octet-stream"
        )

        if tipo_detectado == "application/pdf":
            generar_miniatura_pdf(ruta, thumb_path)
        elif tipo_detectado.startswith("video/"):
            generar_miniatura_video(ruta, thumb_path)
        else:
            guardar_miniatura_si_es_imagen(ruta, thumb_path, tipo_detectado)

        nuevo = Archivo(
            nombre=filename,
            ruta=ruta,
            tipo=tipo_detectado,
            es_privado=marcar_privado,
            fecha_subida=datetime.utcnow(),
        )
        db.session.add(nuevo)
        guardados.append(nuevo)

        ext = os.path.splitext(filename)[1].lower()
        convertibles = {".doc", ".docx", ".odt", ".ppt", ".pptx", ".xls", ".xlsx"}

        if convertir_pdf and ext in convertibles:
            convertir_doc_a_pdf(ruta, carpeta_destino)

        if convertir_audio and tipo_detectado.startswith("video/"):
            convertir_video_a_audio(ruta, carpeta_destino)

    db.session.commit()

    usuario = _current_user()
    return (
        jsonify(
            {
                "uploaded": [_serialize_archivo(archivo, usuario) for archivo in guardados],
                "count": len(guardados),
            }
        ),
        201,
    )


@api_bp.route("/tags", methods=["GET"])
def api_list_tags():
    """Expose all tag names for quick filtering."""
    usuario = _current_user()
    if not usuario:
        return jsonify({"error": "No autenticado."}), 401

    etiquetas = Etiqueta.query.order_by(Etiqueta.nombre.asc()).all()
    if not session.get("acceso_privado"):
        etiquetas = [etiqueta for etiqueta in etiquetas if not etiqueta.es_privada]
    return (
        jsonify(
            [
                {"id": etiqueta.id, "name": etiqueta.nombre, "isPrivate": bool(etiqueta.es_privada)}
                for etiqueta in etiquetas
            ]
        ),
        200,
    )


@api_bp.route("/playlists", methods=["GET", "POST"])
def api_playlists():
    """Read or create playlists for the current user."""
    usuario = _current_user()
    if not usuario:
        return jsonify({"error": "No autenticado."}), 401

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        nombre = (payload.get("name") or "").strip()
        if not nombre:
            return jsonify({"error": "El nombre es obligatorio."}), 400

        nueva = Playlist(nombre=nombre, usuario_id=usuario.id)
        db.session.add(nueva)
        db.session.commit()
        return jsonify(_serialize_playlist(nueva, usuario)), 201

    playlists = (
        Playlist.query.filter_by(usuario_id=usuario.id)
        .order_by(Playlist.fecha_creacion.desc())
        .all()
    )

    return jsonify([_serialize_playlist(playlist, usuario) for playlist in playlists]), 200


@api_bp.route("/playlists/<int:playlist_id>", methods=["DELETE"])
def api_delete_playlist(playlist_id: int):
    """Remove a playlist owned by the current user."""
    usuario = _current_user()
    if not usuario:
        return jsonify({"error": "No autenticado."}), 401

    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.usuario_id != usuario.id:
        return jsonify({"error": "Acceso no autorizado."}), 403

    db.session.delete(playlist)
    db.session.commit()
    return jsonify({"deleted": True}), 200


@api_bp.route("/playlists/<int:playlist_id>/items", methods=["POST"])
def api_add_playlist_item(playlist_id: int):
    """Append a file to a playlist."""
    usuario = _current_user()
    if not usuario:
        return jsonify({"error": "No autenticado."}), 401

    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.usuario_id != usuario.id:
        return jsonify({"error": "Acceso no autorizado."}), 403

    payload = request.get_json(silent=True) or {}
    archivo_id = payload.get("fileId")
    if not archivo_id:
        return jsonify({"error": "Identificador de archivo requerido."}), 400

    archivo = Archivo.query.get_or_404(archivo_id)
    if not usuario_puede_ver(archivo):
        return jsonify({"error": "Acceso no autorizado al archivo."}), 403

    if archivo not in playlist.archivos:
        playlist.archivos.append(archivo)
        db.session.commit()

    return jsonify(_serialize_playlist(playlist, usuario)), 200


@api_bp.route("/playlists/<int:playlist_id>/items/<int:archivo_id>", methods=["DELETE"])
def api_remove_playlist_item(playlist_id: int, archivo_id: int):
    """Remove a file from a playlist."""
    usuario = _current_user()
    if not usuario:
        return jsonify({"error": "No autenticado."}), 401

    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.usuario_id != usuario.id:
        return jsonify({"error": "Acceso no autorizado."}), 403

    archivo = Archivo.query.get_or_404(archivo_id)
    if archivo in playlist.archivos:
        playlist.archivos.remove(archivo)
        db.session.commit()

    return jsonify(_serialize_playlist(playlist, usuario)), 200
