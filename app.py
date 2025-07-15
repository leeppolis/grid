from flask import Flask, request, send_file, make_response
from PIL import Image, ImageDraw
import io
import os
import math

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

COLOR_MAP = {
    "bianco": (255, 255, 255),
    "magenta": (255, 0, 255),
    "nero": (0, 0, 0),
    "ciano": (0, 255, 255)
}

MAX_WIDTH = 4000
MAX_HEIGHT = 4000

ALLOWED_ORIGIN = "https://grid.simonelippolis.com"

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin != ALLOWED_ORIGIN:
        return {"error": "Dominio non autorizzato"}, 403
    if origin and origin == ALLOWED_ORIGIN:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        origin = request.headers.get('Origin')
        if origin == ALLOWED_ORIGIN:
            response = make_response('', 204)
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
        return {"error": "Dominio non autorizzato"}, 403

@app.route('/grid', methods=['POST'])
def grid():
    origin = request.headers.get('Origin') or request.headers.get('Referer')
    if not origin or origin != ALLOWED_ORIGIN:
        return {"error": "Dominio non autorizzato"}, 403

    if 'image' not in request.files:
        return {"error": "Nessuna immagine inviata"}, 400

    image_file = request.files['image']
    image_file.seek(0, io.SEEK_END)
    file_size = image_file.tell()
    image_file.seek(0)
    if file_size > 10 * 1024 * 1024:
        return {"error": "File troppo grande. Massimo 10MB."}, 400

    colore = request.form.get('colore')
    n = int(request.form.get('n', 0))
    try:
        line_width = int(request.form.get('width', 1))
        if line_width < 1:
            line_width = 1
    except:
        line_width = 1

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
        step = width / n
        num_cols = n
        num_rows = math.ceil(height / step)

        for i in range(1, num_cols):
            x = round(i * step)
            draw.line([(x, 0), (x, height)], fill=color, width=line_width)
        for j in range(1, num_rows):
            y = round(j * step)
            draw.line([(0, y), (width, y)], fill=color, width=line_width)

    output = io.BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return send_file(output, mimetype='image/png')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
