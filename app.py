from flask import Flask, request, send_file, make_response
from PIL import Image, ImageDraw
import io
import os
import fnmatch
from urllib.parse import urlparse

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

COLOR_MAP = {
    "bianco": (255, 255, 255),
    "magenta": (255, 0, 255),
    "nero": (0, 0, 0),
    "ciano": (0, 255, 255)
}

MAX_WIDTH = 2000
MAX_HEIGHT = 2000

ALLOWED_ORIGINS = [
    "grid.simonelippolis.com",
    "*.*.pages.dev",
    "*.koolmoe.at",
    "localhost"
]

def is_allowed_origin(origin):
    if not origin:
        return False
    try:
        parsed = urlparse(origin)
        hostname = parsed.hostname or parsed.path
        if not hostname:
            return False
        for pattern in ALLOWED_ORIGINS:
            if fnmatch.fnmatch(hostname, pattern):
                return True
    except Exception as e:
        print("Errore in is_allowed_origin:", e)
    return False

# Gestione CORS preflight
@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        origin = request.headers.get('Origin')
        if not is_allowed_origin(origin):
            return {"error": "Dominio non autorizzato"}, 403
        else:
            response = make_response('', 204)
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if is_allowed_origin(origin):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    return response

@app.route('/grid', methods=['POST'])
def grid():
    origin = request.headers.get('Origin') or request.headers.get('Referer')
    if not is_allowed_origin(origin):
        return {"error": "Dominio non autorizzato"}, 403

    if 'image' not in request.files:
        return {"error": "Nessuna immagine inviata"}, 400

    image_file = request.files['image']
    image_file.seek(0, io.SEEK_END)
    file_size = image_file.tell()
    image_file.seek(0)
    if file_size > 5 * 1024 * 1024:
        return {"error": "File troppo grande. Massimo 5MB."}, 400

    colore = request.form.get('colore')
    n = int(request.form.get('n', 0))

    if colore not in COLOR_MAP:
        return {"error": "Colore non valido"}, 400

    try:
        image = Image.open(image_file).convert('RGB')
    except Exception:
        return {"error": "Errore nella lettura dell'immagine"}, 400

    width, height = image.size
    if width > MAX_WIDTH or height > MAX_HEIGHT:
        return {
            "error": f"Immagine troppo grande. Massimo {MAX_WIDTH}x{MAX_HEIGHT}px."
        }, 400

    draw = ImageDraw.Draw(image)
    color = COLOR_MAP[colore]

    if n > 0:
        step_x = width / n
        step_y = height / n
        for i in range(1, n):
            draw.line([(int(i * step_x), 0), (int(i * step_x), height)], fill=color)
            draw.line([(0, int(i * step_y)), (width, int(i * step_y))], fill=color)

    output = io.BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return send_file(output, mimetype='image/png')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
