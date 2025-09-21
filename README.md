# Djin_Test

Pruebas de librerias y funcionalidades del Djin

# Comandos de Interes

Ejecutar en CMD con Administrador

- Enviroment
  Desactivar enviroment -> deactivate
  Activar enviroment -> .venv\Scripts\activate
  Crear un nuevo enviroment -> python -m venv .venv

- Libraries
  Instalar psutil -> pip install psutil
  Instalar wmi pip -> install wmi
  Instalar pywin32 -> pip install pywin32
  Instalar pyinstaller -> pip install pyinstaller
  Instalar pyqt6 -> pip install PyQt6

- Build Executable
  Un solo archivo -> pyinstaller --onefile chat_app.py
  Carpeta con dependencias -> pyinstaller --noconsole --noconfirm chat_app.py

Others
pyinstaller --onefile --noconsole chat_app.py
pyinstaller --onefile --noconsole --icon=mi_icono.ico chat_app.py
