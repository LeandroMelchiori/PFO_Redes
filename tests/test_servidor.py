"""Pruebas unitarias y de integración del sistema distribuido."""

import socket
import threading

import pytest

from cliente import enviar_tarea
from protocolo import recibir_mensaje
from servidor import ServidorTareas, procesar_tarea


@pytest.fixture()
def servidor():
    """Inicia un servidor en un puerto libre durante cada prueba de integración."""
    instancia = ServidorTareas(puerto=0, workers=2)
    hilo = threading.Thread(target=instancia.servir, daemon=True)
    hilo.start()
    assert instancia.esperar_inicio()

    yield instancia

    instancia.detener()
    hilo.join(timeout=2)
    assert not hilo.is_alive()


def test_procesar_tarea_convierte_texto_a_mayusculas():
    """Comprueba el procesamiento básico de una tarea de texto."""
    resultado = procesar_tarea({"tipo": "mayusculas", "texto": "hola red"})

    assert resultado["valor"] == "HOLA RED"
    assert resultado["worker"]


def test_procesar_tarea_suma_numeros():
    """Comprueba que el worker sume todos los números recibidos."""
    resultado = procesar_tarea({"tipo": "sumar", "numeros": [2, 3.5, 4]})

    assert resultado["valor"] == 9.5


def test_procesar_tarea_rechaza_un_tipo_desconocido():
    """Comprueba que una operación no admitida produzca un error claro."""
    with pytest.raises(ValueError, match="no soportado"):
        procesar_tarea({"tipo": "eliminar"})


def test_cliente_recibe_resultado_del_worker(servidor):
    """Verifica el recorrido completo desde el cliente hasta un worker."""
    host, puerto = servidor.direccion

    respuesta = enviar_tarea(
        {"tipo": "contar_palabras", "texto": "uno dos tres"},
        host,
        puerto,
    )

    assert respuesta["ok"] is True
    assert respuesta["resultado"]["valor"] == 3
    assert respuesta["resultado"]["worker"].startswith("worker")


def test_servidor_rechaza_tarea_invalida(servidor):
    """Verifica que el servidor responda sin cerrar abruptamente la conexión."""
    host, puerto = servidor.direccion

    respuesta = enviar_tarea({"tipo": "sumar", "numeros": "1, 2"}, host, puerto)

    assert respuesta["ok"] is False
    assert "lista de números" in respuesta["error"]


def test_servidor_rechaza_json_invalido(servidor):
    """Comprueba la validación del protocolo ante un mensaje mal formado."""
    host, puerto = servidor.direccion

    with socket.create_connection((host, puerto), timeout=2) as conexion:
        conexion.sendall(b"esto no es json\n")
        respuesta = recibir_mensaje(conexion)

    assert respuesta["ok"] is False
    assert "JSON válido" in respuesta["error"]
