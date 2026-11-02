"""Cliente de consola para probar los endpoints de la API."""

import getpass

import requests


BASE_URL = "http://127.0.0.1:5000"


def mostrar_respuesta(response):
    """Muestra mensajes JSON o el HTML devuelto por el servidor."""
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        data = response.json()
        print(data.get("mensaje") or data.get("error"))
    else:
        print(response.text)


def pedir_credenciales():
    """Solicita las credenciales sin mostrar la contraseña en pantalla."""
    usuario = input("Usuario: ").strip()
    contrasena = getpass.getpass("Contraseña: ")
    return {"usuario": usuario, "contraseña": contrasena}


def main():
    """Ejecuta el menú interactivo y envía las solicitudes a la API."""
    # La sesión conserva automáticamente la cookie recibida después del login.
    session = requests.Session()

    while True:
        print("\n1. Registrar usuario")
        print("2. Iniciar sesión")
        print("3. Ver tareas")
        print("4. Cerrar sesión")
        print("0. Salir")
        opcion = input("Elegí una opción: ").strip()

        try:
            if opcion == "1":
                response = session.post(f"{BASE_URL}/registro", json=pedir_credenciales())
            elif opcion == "2":
                response = session.post(f"{BASE_URL}/login", json=pedir_credenciales())
            elif opcion == "3":
                response = session.get(f"{BASE_URL}/tareas")
            elif opcion == "4":
                response = session.post(f"{BASE_URL}/logout")
            elif opcion == "0":
                break
            else:
                print("Opción inválida.")
                continue

            mostrar_respuesta(response)
        except requests.ConnectionError:
            print("No se pudo conectar con el servidor. Verificá que esté en ejecución.")


if __name__ == "__main__":
    main()

