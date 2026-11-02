# PFO 3 - Sistema distribuido de tareas

Sistema cliente-servidor desarrollado en Python. El servidor recibe tareas mediante sockets TCP y las distribuye entre un pool de workers para procesarlas de forma concurrente.

Alumno:

- Leandro Melchiori - Comisión D

## Arquitectura

```mermaid
flowchart TB
    subgraph clientes[CLIENTES]
        direction LR
        web[Cliente web]
        movil[Cliente móvil]
    end

    balanceador[Balanceador de carga<br/>Nginx / HAProxy]

    subgraph servidores[SERVIDORES DE SOCKETS]
        direction LR
        servidor1[Servidor de sockets 1<br/>Gestión de tareas]
        servidor2[Servidor de sockets 2<br/>Gestión de tareas]
    end

    cola[Cola de mensajes<br/>RabbitMQ]

    subgraph procesamiento[PROCESAMIENTO]
        direction LR
        worker1[Servidor worker 1<br/>Pool de hilos]
        worker2[Servidor worker 2<br/>Pool de hilos]
    end

    subgraph almacenamiento[ALMACENAMIENTO DISTRIBUIDO]
        direction LR
        postgres[(PostgreSQL<br/>Usuarios y tareas)]
        s3[(S3<br/>Archivos)]
    end

    web -->|TCP| balanceador
    movil -->|TCP| balanceador
    balanceador -->|Distribución| servidor1
    balanceador -->|Distribución| servidor2
    servidor1 <-->|Tareas y resultados| cola
    servidor2 <-->|Tareas y resultados| cola
    cola <-->|Procesamiento asíncrono| worker1
    cola <-->|Procesamiento asíncrono| worker2
    worker1 --> postgres
    worker1 --> s3
    worker2 --> postgres
    worker2 --> s3

    classDef principal fill:#f8fafc,stroke:#334155,color:#0f172a,stroke-width:1.5px;
    classDef destacado fill:#e2e8f0,stroke:#1e3a5f,color:#0f172a,stroke-width:2px;
    classDef datos fill:#f1f5f9,stroke:#475569,color:#0f172a,stroke-width:1.5px;

    class web,movil,servidor1,servidor2,worker1,worker2 principal;
    class balanceador,cola destacado;
    class postgres,s3 datos;

    style clientes fill:#ffffff,stroke:#94a3b8,stroke-width:1px
    style servidores fill:#ffffff,stroke:#94a3b8,stroke-width:1px
    style procesamiento fill:#ffffff,stroke:#94a3b8,stroke-width:1px
    style almacenamiento fill:#ffffff,stroke:#94a3b8,stroke-width:1px
```

El diagrama representa el diseño completo solicitado. La implementación local se concentra en la comunicación por sockets y la distribución concurrente entre workers. RabbitMQ, PostgreSQL, S3 y el balanceador quedan definidos como la evolución necesaria para desplegar varias instancias.

## Estructura

```text
.
├── cliente.py             # Cliente de consola del PFO3
├── protocolo.py           # Intercambio de mensajes JSON por TCP
├── servidor.py            # Servidor y pool de workers
├── tests/                 # Pruebas del PFO3
├── pfo2/                  # Código y documentación de la entrega anterior
└── docs/                  # Documentación publicada con GitHub Pages
```

## Requisitos

- Python 3.10 o superior.
- `pip` disponible.

La aplicación utiliza solamente módulos de la biblioteca estándar de Python.

## Instalación

En PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

Para ejecutar las pruebas también se deben instalar las dependencias de desarrollo:

```powershell
py -m pip install -r requirements-dev.txt
```

## Ejecución

Iniciá el servidor:

```powershell
py servidor.py
```

De forma predeterminada escucha en `127.0.0.1:5000` y utiliza cuatro workers. Estos valores se pueden modificar:

```powershell
py servidor.py --host 0.0.0.0 --puerto 5000 --workers 4
```

En otra terminal, ejecutá el cliente:

```powershell
py cliente.py
```

El cliente permite convertir texto a mayúsculas, contar palabras y sumar números. Cada respuesta indica el worker que procesó la tarea.

## Protocolo

El cliente y el servidor intercambian un objeto JSON por conexión. Cada mensaje termina con un salto de línea para que el receptor pueda reconocer su final.

Ejemplo de solicitud:

```json
{
  "id": "identificador-de-la-tarea",
  "tarea": {
    "tipo": "contar_palabras",
    "texto": "programación sobre redes"
  }
}
```

Ejemplo de respuesta:

```json
{
  "ok": true,
  "id": "identificador-de-la-tarea",
  "resultado": {
    "tipo": "contar_palabras",
    "valor": 3,
    "worker": "worker_0"
  }
}
```

## Pruebas

```powershell
py -m pytest -q
```

Las pruebas verifican el procesamiento de tareas, el rechazo de datos incorrectos, la validación del protocolo y el recorrido completo entre el cliente, el servidor y los workers.

## Entrega anterior

El PFO2 se conserva en [`pfo2/`](pfo2/README.md), con su API Flask, cliente, pruebas y capturas originales.

## Documentación publicada

La documentación del PFO3 se publica mediante [GitHub Pages](https://leandromelchiori.github.io/PFO_Redes/). La versión anterior permanece disponible en la sección dedicada al PFO2.
