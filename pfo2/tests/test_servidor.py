"""Pruebas de registro, autenticación y acceso protegido."""

import sqlite3

import pytest

from servidor import create_app


@pytest.fixture()
def app(tmp_path):
    """Crea una aplicación aislada con una base temporal para cada prueba."""
    return create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "pruebas.db"),
            "SECRET_KEY": "clave-de-pruebas",
        }
    )


@pytest.fixture()
def client(app):
    """Proporciona un cliente HTTP de Flask sin iniciar un servidor real."""
    return app.test_client()


def test_registro_guarda_la_contrasena_hasheada(app, client):
    """Comprueba que SQLite nunca guarde la contraseña en texto plano."""
    response = client.post(
        "/registro",
        json={"usuario": "ana", "contraseña": "1234"},
    )

    assert response.status_code == 201

    with sqlite3.connect(app.config["DATABASE"]) as database:
        stored_hash = database.execute(
            "SELECT contrasena_hash FROM usuarios WHERE usuario = ?",
            ("ana",),
        ).fetchone()[0]

    assert stored_hash != "1234"
    assert "1234" not in stored_hash


def test_registro_rechaza_usuarios_duplicados(client):
    """Comprueba que un nombre de usuario no pueda registrarse dos veces."""
    credentials = {"usuario": "ana", "contraseña": "1234"}
    client.post("/registro", json=credentials)

    response = client.post("/registro", json=credentials)

    assert response.status_code == 409
    assert response.get_json()["error"] == "El usuario ya existe."


def test_login_rechaza_credenciales_incorrectas(client):
    """Comprueba que una contraseña incorrecta no permita iniciar sesión."""
    client.post("/registro", json={"usuario": "ana", "contraseña": "1234"})

    response = client.post(
        "/login",
        json={"usuario": "ana", "contraseña": "incorrecta"},
    )

    assert response.status_code == 401


def test_tareas_requiere_inicio_de_sesion(client):
    """Comprueba que la ruta de tareas rechace visitantes sin sesión."""
    response = client.get("/tareas")

    assert response.status_code == 401


def test_usuario_autenticado_puede_ver_tareas(client):
    """Comprueba que un usuario autenticado reciba el HTML de bienvenida."""
    credentials = {"usuario": "ana", "contraseña": "1234"}
    client.post("/registro", json=credentials)
    login_response = client.post("/login", json=credentials)

    response = client.get("/tareas")

    assert login_response.status_code == 200
    assert response.status_code == 200
    assert "Bienvenido, ana" in response.get_data(as_text=True)


def test_logout_cierra_la_sesion(client):
    """Comprueba que cerrar sesión vuelva a proteger la ruta de tareas."""
    credentials = {"usuario": "ana", "contraseña": "1234"}
    client.post("/registro", json=credentials)
    client.post("/login", json=credentials)

    client.post("/logout")
    response = client.get("/tareas")

    assert response.status_code == 401

