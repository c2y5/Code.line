# code.line 📝

**code.line** is a simple minimalist web app to create, save, and view syntax-highlighted code snippets. It supports automatic language detection and presents code with monaco editor

[Try it out yourself here!](https://codeline.amsky.xyz/)

---

![Banner](./img/CodeLineBanner.jpg)

---

## Features ✨

* Create new code snippets with a title and code content.
* Automatically detect syntax language based on file extension in the title (e.g. `.py`, `.js`, `.html`).
* View saved snippets with syntax highlighting using monaco editor
* Unique snippet URLs generated securely with random IDs.
* Minimal dependencies and easy to run locally.
* Password protected
* Expiration date
* Burn after read

---

## Installation 📦

1. Clone the repository:

   ```bash
   git clone https://github.com/c2y5/code.line.git
   cd code.line
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Setup ``.env``
   
   ```
   APP_SECRET_KEY=ABCD1234
   ```

---

## Usage 🚀

Run the app locally:

```bash
python app.py
```

Open your browser at `http://localhost:5000` to create and view code snippets.

---

## Project Structure 📂

```
code.line/
├── snippets/                   # Folder where snippets are stored (will be auto created)
├── static/
│   ├── favicon.png             # Favicon of the website
│   ├── GraviticaMono.otf       # Gravitica Mono font
│   └── style.css               # Custom CSS styles
├── templates/
│   ├── index.html              # Homepage for snippet submission
│   ├── password.html           # Password page for password-locked snippets
│   ├── 404.html                # Error page for snippet not found
│   ├── 410.html                # Error page for expired snippets
│   └── view.html               # Snippet display page
├── utils/                      # Utility tool(s)
│   └── aes.py                  # For password-protected encryptions
├── .env.example                # Example of the .env file
├── app.py                      # Flask app main script
└── README.md                   # Project README file
```

---

## Dependencies 🔨

* [Python 3.10+](https://python.org)
* `Flask`
* `gunicorn`
* `cryptography`
* `python-dotenv`

---

## License 📄

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

## Contributing 🤝

Feel free to submit issues or pull requests! Suggestions to improve code.line are very welcome.

---
