"""Cliente de consola para enviar tareas al servidor TCP."""

import argparse
import socket
import uuid

from protocolo import enviar_mensaje, recibir_mensaje


HOST_PREDETERMINADO = "127.0.0.1"
PUERTO_PREDETERMINADO = 5000


def enviar_tarea(tarea, host=HOST_PREDETERMINADO, puerto=PUERTO_PREDETERMINADO, timeout=5):
    """Envía una tarea al servidor y devuelve la respuesta recibida."""
    solicitud = {"id": str(uuid.uuid4()), "tarea": tarea}
    with socket.create_connection((host, puerto), timeout=timeout) as conexion:
        conexion.settimeout(timeout)
        enviar_mensaje(conexion, solicitud)
        return recibir_mensaje(conexion)


def pedir_numeros():
    """Convierte una línea de números separados por espacios en una lista."""
    valores = input("Números separados por espacios: ").split()
    return [float(valor) for valor in valores]


def construir_tarea(opcion):
    """Solicita los datos necesarios para la opción elegida."""
    if opcion == "1":
        return {"tipo": "mayusculas", "texto": input("Texto: ")}
    if opcion == "2":
        return {"tipo": "contar_palabras", "texto": input("Texto: ")}
    if opcion == "3":
        return {"tipo": "sumar", "numeros": pedir_numeros()}
    return None


def mostrar_respuesta(respuesta):
    """Muestra el resultado o el error informado por el servidor."""
    if not respuesta.get("ok"):
        print(f"Error: {respuesta.get('error', 'respuesta desconocida')}")
        return

    resultado = respuesta["resultado"]
    print(f"Resultado: {resultado['valor']}")
    print(f"Procesado por: {resultado['worker']}")


def crear_argumentos():
    """Define la dirección del servidor que utilizará el cliente."""
    parser = argparse.ArgumentParser(description="Cliente del sistema de tareas")
    parser.add_argument("--host", default=HOST_PREDETERMINADO)
    parser.add_argument("--puerto", type=int, default=PUERTO_PREDETERMINADO)
    return parser.parse_args()


def main():
    """Ejecuta el menú interactivo hasta que el usuario decida salir."""
    argumentos = crear_argumentos()

    while True:
        print("\n1. Convertir texto a mayúsculas")
        print("2. Contar palabras")
        print("3. Sumar números")
        print("0. Salir")
        opcion = input("Elegí una opción: ").strip()

        if opcion == "0":
            break

        try:
            tarea = construir_tarea(opcion)
            if tarea is None:
                print("Opción inválida.")
                continue
            mostrar_respuesta(enviar_tarea(tarea, argumentos.host, argumentos.puerto))
        except ValueError:
            print("Ingresá solamente números válidos.")
        except (ConnectionError, OSError, TimeoutError):
            print("No se pudo conectar con el servidor.")


if __name__ == "__main__":
    main()
