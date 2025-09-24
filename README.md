# Djin_Test

Este proyecto contiene una serie de pruebas para **librerías y funcionalidades** relacionadas con el proyecto **Djin**.

---

## Comandos de Interés

Se recomienda ejecutar estos comandos en la **línea de comandos (CMD)** con privilegios de **administrador**.

### Gestión de Entorno Virtual

- **Activar entorno:**
  ```bash
  .venv\Scripts\activate
  ```
- **Desactivar entorno:**
  ```bash
  deactivate
  ```
- **Crear un nuevo entorno:**
  ```bash
  python -m venv .venv
  ```

### Instalación de Librerías

- **Instalar individualmente:**
  ```bash
  pip install psutil
  pip install wmi
  pip install pywin32
  pip install pyinstaller
  pip install PyQt6
  ```

### Creación de Ejecutables (Build Executable)

Utiliza `PyInstaller` para empaquetar tu aplicación en un ejecutable.

- **Un solo archivo sin consola:**
  ```bash
  pyinstaller --onefile --noconsole chat_app.py
  ```
- **Carpeta con dependencias sin consola:**
  ```bash
  pyinstaller --noconsole --noconfirm chat_app.py
  ```
- **Empaquetar con icono:**
  ```bash
  pyinstaller --onefile --noconsole --icon=mi_icono.ico chat_app.py
  ```
