import os
import uuid

import requests
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

limiter = Limiter(
    app,
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=[],
)

TRYON_API_URL = "https://gunguzameai5.lovable.app/api/public/tryon"
GENERATED_IMAGES_DIR = os.path.join(app.root_path, "generated_images")

EXT_BY_CONTENT_TYPE = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/gallaries.html")
def galleries():
    return render_template("gallaries.html")


@app.route("/about.html")
def about():
    return render_template("about.html")


@app.route("/api/tryon", methods=["POST"])
@limiter.limit("2 per hour")
def tryon():
    data = request.get_json(silent=True)
    if not data or not data.get("garmentId") or not data.get("personImage"):
        return jsonify({"error": "garmentId and personImage are required"}), 400

    try:
        resp = requests.post(TRYON_API_URL, json=data, timeout=120)
        resp.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"error": f"Generation service error: {e}"}), 502

    result = resp.json()

    image_url = result.get("imageUrl")
    if image_url:
        saved_url = save_generated_image(image_url)
        if saved_url:
            result["imageUrl"] = saved_url
            result["downloadUrl"] = saved_url

    return jsonify(result)


@app.errorhandler(429)
def ratelimit_handler(_e):
    return jsonify({"error": "Rate limit reached. You can generate 2 images per hour. Please try again later."}), 429


@app.route("/generated_images/<path:filename>")
def generated_images(filename):
    return send_from_directory(GENERATED_IMAGES_DIR, filename)


def save_generated_image(image_url):
    try:
        img_resp = requests.get(image_url, timeout=120)
        img_resp.raise_for_status()
        content_type = img_resp.headers.get("Content-Type", "").split(";")[0].strip()
        ext = EXT_BY_CONTENT_TYPE.get(content_type, ".png")
        filename = f"generated_{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(GENERATED_IMAGES_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(img_resp.content)
        return f"/generated_images/{filename}"
    except requests.RequestException:
        return None


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
