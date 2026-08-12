import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

TRYON_API_URL = "https://gunguzameai5.lovable.app/api/public/tryon"


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
def tryon():
    data = request.get_json(silent=True)
    if not data or not data.get("garmentId") or not data.get("personImage"):
        return jsonify({"error": "garmentId and personImage are required"}), 400

    try:
        resp = requests.post(TRYON_API_URL, json=data, timeout=120)
        resp.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"error": f"Generation service error: {e}"}), 502

    return jsonify(resp.json())


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
