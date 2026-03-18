# Proyecto 6: Computer Vision

## Sistema de asistencia automatizada con reconocimiento facial

Este proyecto implementa el **Proyecto 1** de la consigna: un sistema que registra asistencia automaticamente a partir del reconocimiento facial de una persona en una imagen o en tiempo real mediante webcam.

La solucion usa la libreria `deepface` para:

- verificacion y reconocimiento facial
- busqueda de coincidencias dentro de una base de rostros registrados
- analisis de atributos faciales basicos como edad, genero y emocion

Ademas, el sistema genera una **bitacora CSV de asistencia** para que el docente o evaluador pueda revisar los registros.

## Funcionalidades

- Registro de personas a partir de fotografias
- Reconocimiento facial sobre una imagen
- Pase de asistencia con imagen
- Pase de asistencia en tiempo real con webcam
- Reporte de asistencia guardado en `data/reports/attendance_log.csv`
- Analisis facial opcional usando DeepFace

## Estructura del proyecto

```text
.
├── app.py
├── data/
│   ├── captures/
│   ├── known_faces/
│   └── reports/
├── face_attendance/
│   ├── cli.py
│   ├── config.py
│   ├── service.py
│   └── storage.py
└── requirements.txt
```

## Requisitos

- Python 3.10 o superior
- Webcam opcional para el modo en tiempo real

## Instalacion

1. Clona el repositorio y entra a la carpeta del proyecto.

```bash
git clone https://github.com/EnigmaticIndividual1/Computer-Vision.git
cd Computer-Vision
```

2. Crea un entorno virtual.

```bash
python3 -m venv .venv
```

3. Activa el entorno virtual.

En macOS / Linux:

```bash
source .venv/bin/activate
```

En Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

4. Instala dependencias.

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Uso

### 1. Inicializar carpetas del proyecto

```bash
python app.py init-dirs
```

### 2. Registrar personas

Agrega al menos una fotografia clara por persona.

```bash
python app.py register --name "Alan Pineda" --image /ruta/a/alan_1.jpg
python app.py register --name "Alan Pineda" --image /ruta/a/alan_2.jpg
python app.py register --name "Maria Lopez" --image /ruta/a/maria.jpg
```

Las imagenes quedan copiadas dentro de `data/known_faces/`.

### 3. Ver las personas registradas

```bash
python app.py list-people
```

### 4. Reconocer un rostro dentro de una imagen

```bash
python app.py recognize --image /ruta/a/foto_prueba.jpg
```

Salida esperada aproximada:

```text
Rostro 1: Alan Pineda (distance=0.2143, threshold=0.4)
```

### 5. Marcar asistencia desde una imagen

```bash
python app.py mark --image /ruta/a/foto_prueba.jpg
```

Si la persona ya fue registrada en la fecha actual, el sistema la marca como `duplicado` para evitar asistencias repetidas el mismo dia.

### 6. Marcar asistencia en tiempo real con webcam

```bash
python app.py webcam
```

Comandos del modo webcam:

- `q`: salir de la aplicacion

Opcionalmente puedes ajustar el indice de camara y la frecuencia de reconocimiento:

```bash
python app.py webcam --camera 0 --frame-interval 20
```

### 7. Ver el reporte de asistencia

Todos los registros se guardan en `data/reports/attendance_log.csv`.

Para verlos en consola:

```bash
python app.py report
```

Para filtrar por fecha:

```bash
python app.py report --date 2026-03-18
```

### 8. Analizar atributos faciales

```bash
python app.py analyze --image /ruta/a/foto_prueba.jpg
```

Salida esperada aproximada:

```text
Rostro 1: edad=24, genero=Man, emocion=happy
```

## Flujo recomendado para calificar el proyecto

1. Instalar dependencias con `requirements.txt`.
2. Registrar una o mas personas con fotografias reales.
3. Ejecutar `python app.py recognize --image ...` para comprobar reconocimiento.
4. Ejecutar `python app.py mark --image ...` o `python app.py webcam` para registrar asistencia.
5. Revisar `data/reports/attendance_log.csv`.

## Notas

- La primera ejecucion de DeepFace puede tardar mas porque descarga pesos del modelo si todavia no existen en el equipo.
- Para obtener mejores resultados, usa fotos frontales, con buena iluminacion y sin filtros.
- Si la webcam no esta disponible, todo el proyecto puede demostrarse usando solamente imagenes.
