"""API Flask para registrar usuarios y proteger el acceso a tareas."""

import os
import sqlite3
from pathlib import Path

from flask import Flask, g, jsonify, render_template_string, request, session
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent


def create_app(test_config=None):
    """Crea la aplicación y permite reemplazar la configuración en las pruebas."""
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=os.getenv("DATABASE_PATH", str(BASE_DIR / "tareas.db")),
        SECRET_KEY=os.getenv("SECRET_KEY", "clave-solo-para-desarrollo"),
    )

    if test_config:
        app.config.update(test_config)

    def get_db():
        """Devuelve la conexión SQLite asociada a la petición actual."""
        # Flask conserva una sola conexión por petición y la cierra al finalizar.
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_error=None):
        """Cierra la conexión SQLite cuando Flask termina la petición."""
        database = g.pop("db", None)
        if database is not None:
            database.close()

    def init_db():
        """Crea la tabla la primera vez sin borrar usuarios existentes."""
        database = get_db()
        database.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL UNIQUE,
                contrasena_hash TEXT NOT NULL
            )
            """
        )
        database.commit()

    @app.post("/registro")
    def registro():
        """Registra un usuario nuevo y almacena su contraseña hasheada."""
        data = request.get_json(silent=True) or {}
        usuario = data.get("usuario")
        contrasena = data.get("contraseña")

        if not isinstance(usuario, str) or not usuario.strip():
            return jsonify(error="El usuario es obligatorio."), 400
        if not isinstance(contrasena, str) or len(contrasena) < 4:
            return jsonify(error="La contraseña debe tener al menos 4 caracteres."), 400

        try:
            database = get_db()
            # Se guarda únicamente el hash; la contraseña original nunca llega a SQLite.
            database.execute(
                "INSERT INTO usuarios (usuario, contrasena_hash) VALUES (?, ?)",
                (usuario.strip(), generate_password_hash(contrasena)),
            )
            database.commit()
        except sqlite3.IntegrityError:
            return jsonify(error="El usuario ya existe."), 409

        return jsonify(mensaje="Usuario registrado correctamente."), 201

    @app.post("/login")
    def login():
        """Valida las credenciales y crea la sesión del usuario."""
        data = request.get_json(silent=True) or {}
        usuario = data.get("usuario")
        contrasena = data.get("contraseña")

        if not isinstance(usuario, str) or not isinstance(contrasena, str):
            return jsonify(error="Usuario y contraseña son obligatorios."), 400

        # El parámetro separado evita concatenar datos del usuario en la consulta SQL.
        user = get_db().execute(
            "SELECT id, usuario, contrasena_hash FROM usuarios WHERE usuario = ?",
            (usuario.strip(),),
        ).fetchone()

        if user is None or not check_password_hash(user["contrasena_hash"], contrasena):
            return jsonify(error="Credenciales incorrectas."), 401

        # La sesión recuerda al usuario autenticado entre las distintas peticiones.
        session.clear()
        session["usuario_id"] = user["id"]
        session["usuario"] = user["usuario"]
        return jsonify(mensaje="Inicio de sesión correcto.", usuario=user["usuario"])

    @app.post("/logout")
    def logout():
        """Elimina los datos de la sesión activa."""
        session.clear()
        return jsonify(mensaje="Sesión cerrada correctamente.")

    @app.get("/tareas")
    def tareas():
        """Muestra la bienvenida solo a usuarios autenticados."""
        # La ruta solo entrega el HTML cuando existe una sesión válida.
        if "usuario_id" not in session:
            return jsonify(error="Debes iniciar sesión para acceder a las tareas."), 401

        return render_template_string(
            """
            <!doctype html>
            <html lang="es">
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>Gestión de tareas</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; background: #f4f6f8; }
                    main { max-width: 680px; margin: 10vh auto; padding: 2rem; background: white;
                           border-radius: 12px; box-shadow: 0 4px 18px #0002; }
                    h1 { color: #17324d; }
                </style>
            </head>
            <body>
                <main>
                    <h1>Bienvenido, {{ usuario }}</h1>
                    <p>Accediste correctamente al sistema de gestión de tareas.</p>
                </main>
            </body>
            </html>
            """,
            usuario=session["usuario"],
        )

    with app.app_context():
        init_db()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")

