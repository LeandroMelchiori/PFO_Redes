"""Funciones compartidas para intercambiar mensajes JSON por sockets TCP."""

import json
import socket


TAMANO_MAXIMO = 64 * 1024


class ErrorProtocolo(ValueError):
    """Indica que un mensaje recibido no respeta el protocolo esperado."""


def enviar_mensaje(conexion, contenido):
    """Serializa un diccionario como JSON y lo envía terminado en salto de línea."""
    datos = json.dumps(contenido, ensure_ascii=False).encode("utf-8") + b"\n"
    if len(datos) > TAMANO_MAXIMO:
        raise ErrorProtocolo("El mensaje supera el tamaño permitido.")
    conexion.sendall(datos)


def recibir_mensaje(conexion):
    """Lee un mensaje JSON completo y devuelve su contenido como diccionario."""
    datos = bytearray()

    while b"\n" not in datos:
        bloque = conexion.recv(4096)
        if not bloque:
            break
        datos.extend(bloque)
        if len(datos) > TAMANO_MAXIMO:
            raise ErrorProtocolo("El mensaje supera el tamaño permitido.")

    if not datos:
        raise ErrorProtocolo("No se recibió ningún mensaje.")

    linea = bytes(datos).split(b"\n", 1)[0]
    try:
        contenido = json.loads(linea.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ErrorProtocolo("El mensaje no contiene un JSON válido.") from error

    if not isinstance(contenido, dict):
        raise ErrorProtocolo("El mensaje debe ser un objeto JSON.")
    return contenido
