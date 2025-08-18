# 🐉 DovahCloud

DovahCloud es una herramienta de gestión y visualización de archivos multimedia, diseñada para facilitar el 
acceso a colecciones locales de forma intuitiva y multiplataforma.

---

## 🚀 Características

- Navegación por carpetas locales
- Visualización de imágenes, vídeos y audio
- Interfaz web ligera y responsiva
- Compatible con Linux, Windows (sin probar)

---

## 🛠️ Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- ffmpeg (para manejo de audio/video)
- Navegador web moderno

---

## 📦 Instalación

### 🔧 Linux

```bash
git clone https://github.com/Hodr25/DovahCloud.git
cd DovahCloud
python3 -m venv venv
pip install -r requirements.txt
python app.py
```

### Windows

- Instalar Python
- Clonar el repositorio o descargar el ZIP
- Abrir PowerShell o CMD en la carpeta del proyecto
- Ejecutar
```pip install -r requirements.txt
python app.py
```
- Asegúrate de tener ffmpeg instalado y agregado al PATH. Puedes descargarlo desde ffmpeg.org

## 📁 Configuración de rutas

Por defecto, DovahCloud busca archivos en la carpeta uploads/DovahCloud.
Si estás en Windows, asegúrate de que las rutas estén bien configuradas en el archivo config.py:

```import os
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'DovahCloud')
PRIVATE_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'DovahCloud', 'Tilok')
```

## 🧪 Ejecución

Una vez instalado, ejecuta:
```python app.py```

Y abre tu navegador en http://<ip>:5000

la ip y puerto se configuran en app.py, al final del todo, se debe poner la misma ip
que tiene el equipo que dará el servicio:

```if __name__ == '__main__':
app.run(debug=True, host='x.x.x.x', port=5000)
```

## 📚 Licencia

Este proyecto está bajo la licencia MIT. Libre para usar, modificar y compartir.

## 🤝 Contribuciones

¡Toda ayuda es bienvenida! Puedes abrir un issue o enviar un pull request.

## 📬 Contacto

Creado por Hodr25
GitHub: @hodr25

---
