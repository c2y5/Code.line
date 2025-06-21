from flask import Flask, render_template, request, redirect, url_for, abort, jsonify
import os
import secrets
import base64
from datetime import datetime, timedelta
import json

app = Flask(__name__)
SNIPPET_FOLDER = "snippets"
os.makedirs(SNIPPET_FOLDER, exist_ok=True)

EXTENSION_LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".sh": "bash",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".rb": "ruby",
    ".go": "go",
    ".ts": "typescript",
    ".php": "php",
    ".rs": "rust",
    ".md": "markdown",
    ".sql": "sql",
    ".xml": "xml"
}

def generate_id():
    return secrets.token_hex(3)

def calculate_expiration(hours):
    if not hours or int(hours) == 0:
        return None
    return datetime.now() + timedelta(hours=int(hours))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/new", methods=["POST"])
def new_snippet():
    title = request.form.get("title", "Untitled").strip()
    encoded_code = request.form.get("codeEncoded")
    password = request.form.get("password")
    expiration_hours = request.form.get("expiration", "0")
    burn_after_read = request.form.get("burn_after_read") == "on"

    if not encoded_code:
        return "Code is required.", 400

    try:
        decoded_code = base64.b64decode(encoded_code).decode("utf-8")
    except Exception as e:
        return f"Failed to decode code: {str(e)}", 400

    while True:
        snippet_id = generate_id()
        snippet_path = os.path.join(SNIPPET_FOLDER, f"{snippet_id}.json")
        if not os.path.exists(snippet_path):
            break

    snippet_data = {
        "title": title,
        "code": decoded_code,
        "password": password,
        "expires_at": calculate_expiration(expiration_hours).isoformat() if expiration_hours != "0" else None, # type: ignore
        "burn_after_read": burn_after_read,
        "views": 0,
        "content_viewed": False
    }

    with open(snippet_path, "w", encoding="utf-8") as f:
        json.dump(snippet_data, f)

    return redirect(url_for("view_snippet", snippet_id=snippet_id))

@app.route("/<string:snippet_id>", methods=["GET", "POST"])
def view_snippet(snippet_id):
    filepath = os.path.join(SNIPPET_FOLDER, f"{snippet_id}.json")
    if not os.path.exists(filepath):
        abort(404)

    with open(filepath, "r", encoding="utf-8") as f:
        snippet_data = json.load(f)

    if snippet_data.get("expires_at"):
        expires_at = datetime.fromisoformat(snippet_data["expires_at"])
        if datetime.now() > expires_at:
            os.remove(filepath)
            abort(410)

    if snippet_data.get("password"):
        if request.method == "POST":
            if request.form.get("password") != snippet_data["password"]:
                return render_template("password.html", snippet_id=snippet_id, error="Invalid password")
        else:
            return render_template("password.html", snippet_id=snippet_id)

    if request.method == "POST":
        if request.form.get("action") == "password_submit":
            if request.form.get("password") != snippet_data.get("password"):
                return render_template(
                    "password.html",
                    snippet_id=snippet_id,
                    error="Invalid password"
                )
        elif request.is_json and request.json and request.json.get("confirm_view"):
            if snippet_data.get("burn_after_read"):
                snippet_data["content_viewed"] = True
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(snippet_data, f)
                return jsonify({"status": "success", "code": snippet_data["code"]})

    if snippet_data.get("burn_after_read"):
        if snippet_data.get("content_viewed", False):
            os.remove(filepath)
            abort(410)
        if request.method == "GET":
            return render_template("view.html",
                                snippet_id=snippet_id,
                                title=snippet_data["title"],
                                code="",
                                language="",
                                burn_after_read=True,
                                show_content=False)

    if not snippet_data.get("burn_after_read") or snippet_data.get("content_viewed", False):
        snippet_data["views"] = snippet_data.get("views", 0) + 1
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(snippet_data, f)

    _, ext = os.path.splitext(snippet_data["title"].lower())
    language = EXTENSION_LANGUAGE_MAP.get(ext, "")

    return render_template("view.html",
                         snippet_id=snippet_id,
                         title=snippet_data["title"],
                         code=snippet_data["code"],
                         language=language,
                         burn_after_read=snippet_data.get("burn_after_read", False),
                         show_content=True)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(410)
def snippet_expired(e):
    return render_template('410.html'), 410

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)