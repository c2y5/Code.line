from flask import Flask, render_template, request, redirect, url_for, abort
import os
import secrets

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
    return secrets.token_hex(8)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/new", methods=["POST"])
def new_snippet():
    title = request.form.get("title")
    code = request.form.get("code")

    if not title or not code:
        return "Both title and code are required.", 400

    snippet_id = generate_id()
    snippet_path = os.path.join(SNIPPET_FOLDER, f"{snippet_id}.txt")

    with open(snippet_path, "w", encoding="utf-8") as f:
        f.write(title.strip() + "\n")
        f.write(code.strip())

    return redirect(url_for("view_snippet", snippet_id=snippet_id))

@app.route("/<string:snippet_id>")
def view_snippet(snippet_id):
    filepath = os.path.join(SNIPPET_FOLDER, f"{snippet_id}.txt")
    if not os.path.exists(filepath):
        abort(404)

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        title = lines[0].strip()
        code = "".join(lines[1:])

    _, ext = os.path.splitext(title.lower())
    language = EXTENSION_LANGUAGE_MAP.get(ext, "")

    return render_template("view.html", snippet_id=snippet_id, title=title, code=code, language=language)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)