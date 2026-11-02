"""Servidor TCP que distribuye tareas entre un pool de workers."""

import argparse
import socket
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from protocolo import ErrorProtocolo, enviar_mensaje, recibir_mensaje


HOST_PREDETERMINADO = "127.0.0.1"
PUERTO_PREDETERMINADO = 5000


def procesar_tarea(tarea):
    """Ejecuta una tarea admitida e informa qué worker la procesó."""
    if not isinstance(tarea, dict):
        raise ValueError("La tarea debe ser un objeto JSON.")

    tipo = tarea.get("tipo")
    if tipo == "mayusculas":
        texto = tarea.get("texto")
        if not isinstance(texto, str):
            raise ValueError("La tarea mayusculas requiere un texto.")
        valor = texto.upper()
    elif tipo == "contar_palabras":
        texto = tarea.get("texto")
        if not isinstance(texto, str):
            raise ValueError("La tarea contar_palabras requiere un texto.")
        valor = len(texto.split())
    elif tipo == "sumar":
        numeros = tarea.get("numeros")
        if not isinstance(numeros, list) or not all(
            isinstance(numero, (int, float)) and not isinstance(numero, bool)
            for numero in numeros
        ):
            raise ValueError("La tarea sumar requiere una lista de números.")
        valor = sum(numeros)
    else:
        raise ValueError("Tipo de tarea no soportado.")

    return {
        "tipo": tipo,
        "valor": valor,
        "worker": threading.current_thread().name,
    }


class ServidorTareas:
    """Acepta clientes TCP y deriva sus tareas a workers concurrentes."""

    def __init__(self, host=HOST_PREDETERMINADO, puerto=PUERTO_PREDETERMINADO, workers=4):
        """Configura el socket y los pools sin iniciar todavía la escucha."""
        if workers < 1:
            raise ValueError("La cantidad de workers debe ser mayor que cero.")

        self._detenido = threading.Event()
        self._listo = threading.Event()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((host, puerto))
        self._socket.settimeout(0.5)
        self._clientes = ThreadPoolExecutor(
            max_workers=max(4, workers),
            thread_name_prefix="cliente",
        )
        self._workers = ThreadPoolExecutor(
            max_workers=workers,
            thread_name_prefix="worker",
        )

    @property
    def direccion(self):
        """Devuelve el host y el puerto asignados al servidor."""
        return self._socket.getsockname()

    def esperar_inicio(self, timeout=2):
        """Espera hasta que el socket esté listo para recibir conexiones."""
        return self._listo.wait(timeout)

    def servir(self):
        """Acepta conexiones hasta que se solicite la detención del servidor."""
        self._socket.listen()
        self._listo.set()
        host, puerto = self.direccion
        print(f"Servidor escuchando en {host}:{puerto}")

        try:
            while not self._detenido.is_set():
                try:
                    conexion, direccion = self._socket.accept()
                except socket.timeout:
                    continue
                except OSError:
                    if self._detenido.is_set():
                        break
                    raise
                self._clientes.submit(self._atender_cliente, conexion, direccion)
        finally:
            self._socket.close()
            self._clientes.shutdown(wait=True, cancel_futures=True)
            self._workers.shutdown(wait=True, cancel_futures=True)

    def detener(self):
        """Interrumpe la escucha para permitir un cierre ordenado."""
        self._detenido.set()
        self._socket.close()

    def _atender_cliente(self, conexion, direccion):
        """Valida una solicitud y devuelve el resultado generado por un worker."""
        with conexion:
            try:
                solicitud = recibir_mensaje(conexion)
                tarea = solicitud.get("tarea")
                identificador = solicitud.get("id") or str(uuid.uuid4())
                futuro = self._workers.submit(procesar_tarea, tarea)
                resultado = futuro.result(timeout=10)
                respuesta = {
                    "ok": True,
                    "id": identificador,
                    "resultado": resultado,
                }
                print(f"Tarea {identificador} recibida desde {direccion[0]}")
            except (ErrorProtocolo, ValueError) as error:
                respuesta = {"ok": False, "error": str(error)}
            except TimeoutError:
                respuesta = {"ok": False, "error": "La tarea excedió el tiempo de espera."}

            try:
                enviar_mensaje(conexion, respuesta)
            except (ConnectionError, OSError):
                print(f"El cliente {direccion[0]} cerró la conexión antes de tiempo.")


def crear_argumentos():
    """Define los parámetros disponibles al iniciar el servidor."""
    parser = argparse.ArgumentParser(description="Servidor distribuido de tareas")
    parser.add_argument("--host", default=HOST_PREDETERMINADO)
    parser.add_argument("--puerto", type=int, default=PUERTO_PREDETERMINADO)
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args()


def main():
    """Inicia el servidor y permite detenerlo con Ctrl+C."""
    argumentos = crear_argumentos()
    servidor = ServidorTareas(argumentos.host, argumentos.puerto, argumentos.workers)
    try:
        servidor.servir()
    except KeyboardInterrupt:
        print("\nCerrando servidor...")
        servidor.detener()


if __name__ == "__main__":
    main()
