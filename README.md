# PFO 2 - Sistema de gestión de tareas

API REST desarrollada con Flask y SQLite. Permite registrar usuarios, iniciar y cerrar sesión, y acceder a una página protegida de tareas. Las contraseñas se almacenan mediante hashes seguros de Werkzeug.

## PFO 3 - Arquitectura distribuida

El rediseño distribuye la recepción, el procesamiento y el almacenamiento de las tareas entre varios componentes.

```mermaid
flowchart TB
    subgraph clientes[CLIENTES]
        direction LR
        web[Cliente web<br/>Navegador]
        movil[Cliente móvil<br/>Aplicación]
    end

    balanceador[Balanceador de carga<br/>Nginx / HAProxy]

    subgraph sockets[SERVIDORES DE SOCKETS]
        direction LR
        servidor1[Servidor de sockets 1<br/>Autenticación y gestión de tareas]
        servidor2[Servidor de sockets 2<br/>Autenticación y gestión de tareas]
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

    web -->|HTTPS / TCP| balanceador
    movil -->|HTTPS / TCP| balanceador
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

    classDef cliente fill:#dbeafe,stroke:#2563eb,color:#172554,stroke-width:2px;
    classDef balance fill:#ede9fe,stroke:#7c3aed,color:#2e1065,stroke-width:2px;
    classDef servidor fill:#ffedd5,stroke:#ea580c,color:#431407,stroke-width:2px;
    classDef mensajes fill:#ffe4e6,stroke:#e11d48,color:#4c0519,stroke-width:2px;
    classDef worker fill:#ccfbf1,stroke:#0f766e,color:#042f2e,stroke-width:2px;
    classDef datos fill:#dcfce7,stroke:#16a34a,color:#052e16,stroke-width:2px;

    class web,movil cliente;
    class balanceador balance;
    class servidor1,servidor2 servidor;
    class cola mensajes;
    class worker1,worker2 worker;
    class postgres,s3 datos;

    style clientes fill:#eff6ff,stroke:#93c5fd,stroke-width:1px
    style sockets fill:#fff7ed,stroke:#fdba74,stroke-width:1px
    style procesamiento fill:#f0fdfa,stroke:#5eead4,stroke-width:1px
    style almacenamiento fill:#f0fdf4,stroke:#86efac,stroke-width:1px
```

## Requisitos

- Python 3.10 o superior.
- `pip` disponible.

## Instalación

En PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

Para instalar también las dependencias de prueba:

```powershell
py -m pip install -r requirements-dev.txt
```

## Ejecución

Definí una clave de sesión y ejecutá el servidor:

```powershell
$env:SECRET_KEY = "una-clave-local-larga-y-aleatoria"
py servidor.py
```

La API queda disponible en `http://127.0.0.1:5000`. La base `tareas.db` se crea automáticamente y no se versiona.

En otra terminal podés abrir el cliente de consola:

```powershell
.\.venv\Scripts\Activate.ps1
py cliente.py
```

## Endpoints

| Método | Ruta | Descripción |
| --- | --- | --- |
| `POST` | `/registro` | Registra un usuario y guarda su contraseña hasheada. |
| `POST` | `/login` | Verifica las credenciales e inicia una sesión. |
| `POST` | `/logout` | Cierra la sesión actual. |
| `GET` | `/tareas` | Muestra el HTML de bienvenida si hay una sesión válida. |

El registro y el login reciben JSON con este formato:

```json
{
  "usuario": "nombre",
  "contraseña": "1234"
}
```

## Prueba manual con curl

Los siguientes comandos conservan la cookie de sesión en `cookies.txt`:

```powershell
curl.exe -c cookies.txt -H "Content-Type: application/json" -d '{"usuario":"ana","contraseña":"1234"}' http://127.0.0.1:5000/registro
curl.exe -c cookies.txt -b cookies.txt -H "Content-Type: application/json" -d '{"usuario":"ana","contraseña":"1234"}' http://127.0.0.1:5000/login
curl.exe -b cookies.txt http://127.0.0.1:5000/tareas
```

## Pruebas automáticas

```powershell
py -m pytest -v
```

Las pruebas comprueban el hash de contraseñas, los usuarios duplicados, el rechazo de credenciales incorrectas, la protección de `/tareas` y el cierre de sesión.

## Capturas de pruebas

### Registro correcto

![Registro exitoso](capturas/registro-exitoso.png)

### Acceso autenticado a tareas

![Acceso a tareas](capturas/acceso-tareas.png)

## Respuestas conceptuales

### ¿Por qué hashear contraseñas?

El hash evita guardar la contraseña original. Si alguien obtiene la base de datos, no encuentra las claves en texto plano. Para validar el acceso se compara la contraseña ingresada con el hash almacenado. Werkzeug aplica un algoritmo lento y sal aleatoria, lo que dificulta ataques por diccionario y evita que dos contraseñas iguales produzcan registros idénticos.

### Ventajas de usar SQLite en este proyecto

SQLite no requiere instalar ni administrar un servidor de base de datos. Guarda la información en un único archivo, viene integrado con Python y ofrece transacciones, restricciones y consultas SQL. Es apropiado para una aplicación de bajo tráfico y permite trasladar o respaldar los datos con facilidad.

## GitHub Pages

La presentación estática del proyecto se encuentra en [`docs/index.html`](docs/index.html). Para publicarla, en la configuración del repositorio se debe seleccionar **Pages**, elegir **Deploy from a branch** y usar la rama `main` con la carpeta `/docs`.

Sitio publicado: [GitHub Pages](https://leandromelchiori.github.io/PFO2_Redes/)

GitHub Pages muestra la documentación y las capturas. El servidor Flask y SQLite se ejecutan localmente porque Pages no admite aplicaciones Python del lado servidor.

