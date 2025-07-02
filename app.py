from flask import Flask, render_template, request, redirect, url_for, abort, jsonify, session
import os
import secrets
import base64
from datetime import datetime, timedelta
import json
from utils.aes import aes_encrypt, aes_decrypt
import hashlib
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")

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

    password_hash = None
    if password:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        decoded_code = aes_encrypt(decoded_code.encode("utf-8"), password)

        decoded_code = base64.b64encode(decoded_code).decode("utf-8")

    while True:
        snippet_id = generate_id()
        snippet_path = os.path.join(SNIPPET_FOLDER, f"{snippet_id}.json")
        if not os.path.exists(snippet_path):
            break

    snippet_data = {
        "title": title,
        "code": decoded_code,
        "password_hash": password_hash,
        "expires_at": calculate_expiration(expiration_hours).isoformat() if expiration_hours != "0" else None, # type: ignore
        "burn_after_read": burn_after_read,
        "views": 0,
        "content_viewed": False
    }

    with open(snippet_path, "w", encoding="utf-8") as f:
        json.dump(snippet_data, f)

    return redirect(url_for("view_snippet", snippet_id=snippet_id))

@app.route("/getCode/<string:snippet_id>", methods=["GET"])
def get_code(snippet_id):
    if not snippet_id:
        return jsonify({"error": "Snippet ID is required"}), 400

    filepath = os.path.join(SNIPPET_FOLDER, f"{snippet_id}.json")
    if not os.path.exists(filepath):
        return jsonify({"error": "Snippet not found"}), 404

    with open(filepath, "r", encoding="utf-8") as f:
        snippet_data = json.load(f)


    if snippet_data.get("burn_after_read"):
        return jsonify({"error": f"Please use the correct way to view code: https://codeline.amsky.xyz/{snippet_id}"}), 400

    if snippet_data.get("expires_at"):
        expires_at = datetime.fromisoformat(snippet_data["expires_at"])
        if datetime.now() > expires_at:
            os.remove(filepath)
            return jsonify({"error": "Snippet has expired"}), 410

    code = snippet_data["code"]
    password_hash = snippet_data.get("password_hash")
    encrypted = bool(password_hash)
    unlocked = session.get("unlocked_snippets", {})

    if encrypted:
        password_input = unlocked.get(snippet_id)
        code_bytes = base64.b64decode(code)
        code = aes_decrypt(code_bytes, password_input).decode("utf-8")

    return jsonify({"code": code})

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

    unlocked = session.get("unlocked_snippets", {})
    password_hash = snippet_data.get("password_hash")
    encrypted = bool(password_hash)

    if encrypted and snippet_id not in unlocked:
        if request.method == "POST" and request.form.get("action") == "password_submit":
            password_input = request.form.get("password")
            if password_input and hashlib.sha256(password_input.encode()).hexdigest() != password_hash:
                return render_template(
                    "password.html",
                    snippet_id=snippet_id,
                    error="Invalid password"
                )
            unlocked[snippet_id] = password_input
            session["unlocked_snippets"] = unlocked
        else:
            return render_template("password.html", snippet_id=snippet_id)

    if request.method == "POST" and request.is_json and request.json and request.json.get("confirm_view"):
        if snippet_data.get("burn_after_read"):
            snippet_data["content_viewed"] = True
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(snippet_data, f)
            code = snippet_data["code"]
            if encrypted:
                password_input = session.get("unlocked_snippets", {}).get(snippet_id)
                code_bytes = base64.b64decode(code)
                code = aes_decrypt(code_bytes, password_input).decode("utf-8")

            _, ext = os.path.splitext(snippet_data["title"].lower())
            language = EXTENSION_LANGUAGE_MAP.get(ext, "")
            return jsonify({"status": "success", "code": code, "language": language})

    if snippet_data.get("burn_after_read"):
        if snippet_data.get("content_viewed"):
            os.remove(filepath)
            abort(410)
        return render_template(
            "view.html",
            snippet_id=snippet_id,
            title=snippet_data["title"],
            code="",
            language="",
            burn_after_read=True,
            show_content=False,
            show_raw=False,
        )

    snippet_data["views"] = snippet_data.get("views", 0) + 1
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(snippet_data, f)

    code = snippet_data["code"]
    if encrypted:
        password_input = request.form.get("password") if request.method == "POST" else None
        code_bytes = base64.b64decode(code)
        code = aes_decrypt(code_bytes, password_input).decode("utf-8") if password_input else ""

    _, ext = os.path.splitext(snippet_data["title"].lower())
    language = EXTENSION_LANGUAGE_MAP.get(ext, "")

    return render_template(
        "view.html",
        snippet_id=snippet_id,
        title=snippet_data["title"],
        language=language,
        burn_after_read=False,
        show_content=True,
        show_raw=not encrypted and not snippet_data.get("burn_after_read", False),
    )

@app.route("/<string:snippet_id>/raw", methods=["GET"])
def view_snippet_raw(snippet_id):
    filepath = os.path.join(SNIPPET_FOLDER, f"{snippet_id}.json")
    if not os.path.exists(filepath):
        abort(404)

    with open(filepath, "r", encoding="utf-8") as f:
        snippet_data = json.load(f)

    if snippet_data.get("expires_at"):
        expires_at = datetime.fromisoformat(snippet_data["expires_at"])
        if datetime.now() > expires_at:
            os.remove(filepath)
            return "The snippet has expired", 410

    password_hash = snippet_data.get("password_hash")
    encrypted = bool(password_hash)

    if snippet_data.get("burn_after_read"):
        return "Cannot view raw for burn after read files", 400

    snippet_data["views"] = snippet_data.get("views", 0) + 1
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(snippet_data, f)

    code = snippet_data["code"]

    if encrypted:
        password_input = request.args.get("pwd")
        if not password_input:
            return "Password is required for this snippet", 400
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(password_input + ("=" * (len(password_input) % 4)))
            password_input = aes_decrypt(encrypted_bytes, app.secret_key).decode("utf-8")
            if hashlib.sha256(password_input.encode()).hexdigest() != password_hash:
                return "Invalid password", 403

            code_bytes = base64.b64decode(code)
            code = aes_decrypt(code_bytes, password_input).decode("utf-8")
        except Exception as e:
            return f"Failed to process password: {str(e)}", 400

    return code

@app.route("/<string:snippet_id>/get_pass", methods=["GET"])
def get_encrypted_password(snippet_id):
    filepath = os.path.join(SNIPPET_FOLDER, f"{snippet_id}.json")
    if not os.path.exists(filepath):
        return jsonify({"error": "Snippet not found"}), 404

    with open(filepath, "r", encoding="utf-8") as f:
        snippet_data = json.load(f)
    
    if not snippet_data.get("password_hash"):
        return jsonify({"error": "Snippet is not password protected"}), 400

    unlocked = session.get("unlocked_snippets", {})
    password_input = unlocked.get(snippet_id)
    
    if not password_input:
        return jsonify({"error": "Password not found in session"}), 403

    try:
        encrypted_bytes = aes_encrypt(password_input.encode("utf-8"), app.secret_key)
        encrypted_password = base64.urlsafe_b64encode(encrypted_bytes).decode("utf-8").rstrip("=")
        return jsonify({"encrypted_password": encrypted_password})
    except Exception as e:
        return jsonify({"error": "Failed to encrypt password"}), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(410)
def snippet_expired(e):
    return render_template("410.html"), 410

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)