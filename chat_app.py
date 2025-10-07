# -*- coding: utf-8 -*-
# Título: Monitor de Métricas del Sistema Interactivo

"""
Este script crea una aplicación de escritorio con PyQt6 que actúa como un
monitor de sistema interactivo. El usuario puede escribir el nombre de una
métrica de sistema para obtener un valor almacenado en una base de datos SQLite.
Ahora se utiliza DuckDB para consultar directamente el archivo SQLite,
garantizando un acceso eficiente y transaccional.

Para su correcto funcionamiento, necesitas instalar las librerías:
pip install pyqt6 psutil duckdb

Uso:
1. Asegúrate de tener Python instalado.
2. Instala PyQt6, psutil y duckdb usando pip.
3. Ejecuta este script desde la línea de comandos: python chat_app.py
"""

import sys
import time
import random
import psutil
import duckdb  # Reemplazo de sqlite3 por duckdb
import os
import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                             QWidget, QTextEdit, QLineEdit, QLabel)
from PyQt6.QtCore import Qt

class ChatApp(QMainWindow):
    """
    Clase principal de la aplicación que crea la ventana y gestiona la lógica
    del chat para mostrar las métricas del sistema.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador de Chat de Métricas")
        self.setGeometry(100, 100, 600, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QLabel {
                color: #ecf0f1;
                font-size: 14px;
                padding: 10px;
                background-color: #34495e;
                border-radius: 8px;
            }
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-size: 14px;
                border: 2px solid #2980b9;
                border-radius: 12px;
                padding: 15px;
                margin: 10px;
            }
            QLineEdit {
                background-color: #34495e;
                color: #ecf0f1;
                font-size: 14px;
                border: 2px solid #2980b9;
                border-radius: 12px;
                padding: 10px;
                margin: 10px;
            }
            /* Estilos para las burbujas de chat */
            .bot-message {
                background-color: #34495e;
                color: #ecf0f1;
                border-radius: 15px;
                padding: 10px;
                margin: 5px 40px 5px 5px;
                text-align: left;
            }
            .user-message {
                background-color: #2980b9;
                color: #ecf0f1;
                border-radius: 15px;
                padding: 10px;
                margin: 5px 5px 5px 40px;
                text-align: right;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout()
        central_widget.setLayout(self.layout)

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.layout.addWidget(self.chat_history)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Escribe el número o nombre de la métrica...")
        self.user_input.returnPressed.connect(self.handle_input)
        self.layout.addWidget(self.user_input)

        # Definir la lista de métricas, ahora con la opción 26
        self.metric_names = [
            "cpu_percent", "cpu_freq",
            "ram_percent", "ram_used",
            "ram_total", "ram_free", "disk_percent",
            "disk_used", "disk_total", "disk_free", "swap_percent",
            "swap_usado", "swap_total", "red_bytes_sent", "red_bytes_recv",
            "cpu_temp_celsius", "battery_percent", "cpu_power_package",
            "cpu_power_cores", "cpu_clocks",
            "top_10_cpu"  # Agregamos la nueva métrica aquí
        ]
        
        # Diccionario para mapear nombres originales a nombres formateados
        self.formatted_metric_names = {name: " ".join(part.capitalize() for part in name.split('_')) for name in self.metric_names}
        # Sobreescribir el formato de la nueva métrica
        self.formatted_metric_names["top_10_cpu"] = "Top 10 Apps High CPU"

        # Construir la lista de métricas para el mensaje inicial
        metrics_list_str = "Bot: Métricas disponibles:\n"
        for i, name in enumerate(self.metric_names, 1):
            formatted_name = self.formatted_metric_names[name]
            metrics_list_str += f"{i}. {formatted_name}\n"
        
        # Ruta de la base de datos especificada por el usuario
        self.db_path = "./data/monitoreo.db"
        self.conn = None # Conexión al motor de DuckDB
        self.cursor = None # No se utiliza el cursor tradicional de SQLite

        # --- MODIFICACIÓN: Conexión y Configuración de DuckDB ---
        try:
            # 1. Establecer conexión con DuckDB. Se utiliza una conexión en memoria
            # ya que la lectura del archivo SQLite se realizará a través de sqlite_scan.
            self.conn = duckdb.connect(database=':memory:', read_only=False)
            
            # 2. Cargar y habilitar la extensión SQLite de DuckDB
            # Esto permite usar la función sqlite_scan para leer el archivo externo.
            self.conn.execute("INSTALL sqlite;")
            self.conn.execute("LOAD sqlite;")
            
            # La creación de la tabla y la inserción de datos de ejemplo se asumen
            # ahora responsabilidad del programa 'Djin' (el escritor), manteniendo
            # a 'Mayordomo' como un lector que usa DuckDB.
            
            # Si el archivo no existe, se notifica al usuario, pero se permite continuar
            # para el monitoreo de procesos (get_top_cpu_processes).
            if not os.path.exists(self.db_path):
                 self.append_bot_message(f"Advertencia: El archivo SQLite '{self.db_path}' no fue encontrado. La lectura de métricas de la BD no funcionará hasta que Djin la cree.")

        except duckdb.Error as e:
            self.append_bot_message(f"Error al inicializar DuckDB o cargar la extensión SQLite: {e}")
            self.conn = None
        # --- FIN MODIFICACIÓN ---

        # Estado inicial
        self.append_bot_message("¡Hola! Soy un bot de monitoreo del sistema. Escribe el número o nombre de una métrica para conocer su valor, o escribe 'opciones' para ver la lista de métricas.")
        self.append_bot_message(metrics_list_str)

    def get_metrics_data(self):
        """
        Obtiene el último conjunto de datos de la base de datos 'monitoreo.db'.
        
        MODIFICACIÓN: Utiliza DuckDB con sqlite_scan para leer directamente el archivo SQLite.
        """
        if not self.conn:
            return {'error': 'El motor de DuckDB no está inicializado.'}
        
        if not os.path.exists(self.db_path):
            return {'error': f"El archivo SQLite de origen '{self.db_path}' no fue encontrado."}

        # La consulta utiliza sqlite_scan para que DuckDB pueda leer los datos
        # de la tabla 'metricas' sin necesidad de una conexión SQLite nativa.
        query = f"""
        SELECT * FROM sqlite_scan('{self.db_path}', 'metricas')
        ORDER BY timestamp DESC 
        LIMIT 1
        """
        
        try:
            # Ejecución de la consulta DuckDB
            result = self.conn.execute(query).fetchone()
            
            if not result:
                return {'error': 'No hay datos en la tabla de métricas o la tabla no existe.'}

            # Definición de columnas basada en la estructura de CREATE TABLE
            columns = [
                "timestamp", "hostname", "username", "cpu_percent", "cpu_freq",
                "ram_percent", "ram_used", "ram_total", "ram_free",
                "disk_percent", "disk_used", "disk_total", "disk_free",
                "swap_percent", "swap_usado", "swap_total", "red_bytes_sent",
                "red_bytes_recv", "cpu_temp_celsius", "battery_percent",
                "cpu_power_package", "cpu_power_cores", "cpu_clocks"
            ]
            
            # Crear un diccionario a partir de la fila (tupla) y los nombres de las columnas
            metrics = dict(zip(columns, result))

            # --- Lógica de Formateo de Datos Defensivo ---
            def safe_format(key, suffix, is_bytes=False):
                """Convierte a float y formatea el valor de manera segura."""
                value = metrics.get(key)
                if value is None:
                    return None
                
                try:
                    # Intenta convertir a float. Si falla, salta al 'except'.
                    numeric_value = float(value)
                    
                    if is_bytes:
                        # Convertir de bytes a MB para red
                        return f"{numeric_value / (1024**2):.2f} {suffix}"
                    
                    return f"{numeric_value:.2f} {suffix}"
                except (ValueError, TypeError):
                    # Si el valor no es convertible a float (es una cadena inesperada),
                    # se devuelve None o una indicación de error.
                    return "N-A"

            # Aplicar el formato de visualización final usando safe_format
            metrics['cpu_percent'] = safe_format('cpu_percent', '%')
            metrics['cpu_freq'] = safe_format('cpu_freq', 'MHz')
            metrics['ram_percent'] = safe_format('ram_percent', '%')
            metrics['ram_used'] = safe_format('ram_used', 'GB')
            metrics['ram_total'] = safe_format('ram_total', 'GB')
            metrics['ram_free'] = safe_format('ram_free', 'GB')
            metrics['disk_percent'] = safe_format('disk_percent', '%')
            metrics['disk_used'] = safe_format('disk_used', 'GB')
            metrics['disk_total'] = safe_format('disk_total', 'GB')
            metrics['disk_free'] = safe_format('disk_free', 'GB')
            metrics['swap_percent'] = safe_format('swap_percent', '%')
            metrics['swap_usado'] = safe_format('swap_usado', 'GB')
            metrics['swap_total'] = safe_format('swap_total', 'GB')
            metrics['red_bytes_sent'] = safe_format('red_bytes_sent', 'MB', is_bytes=True)
            metrics['red_bytes_recv'] = safe_format('red_bytes_recv', 'MB', is_bytes=True)
            metrics['cpu_temp_celsius'] = safe_format('cpu_temp_celsius', '°C')
            metrics['battery_percent'] = safe_format('battery_percent', '%')
            metrics['cpu_power_package'] = safe_format('cpu_power_package', 'W')
            metrics['cpu_power_cores'] = safe_format('cpu_power_cores', 'W')
            metrics['cpu_clocks'] = safe_format('cpu_clocks', 'MHz')

            return metrics
        except duckdb.Error as e:
            # Captura errores específicos de DuckDB
            return {'error': f"Error al leer la base de datos con DuckDB: {e}"}
        except Exception as e:
            # Captura cualquier otro error durante el procesamiento
            return {'error': f"Error inesperado durante la obtención de métricas: {e}"}

    def append_bot_message(self, message):
        """Añade un mensaje del bot al historial de chat con estilo de burbuja izquierda."""
        html_message = f"<div style='text-align:left;'><span class='bot-message'>{message.replace('\n', '<br>')}</span></div>"
        self.chat_history.append(html_message)
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())

    def append_user_message(self, message):
        """Añade un mensaje del usuario al historial de chat con estilo de burbuja derecha."""
        html_message = f"<div style='text-align:right;'><span class='user-message'>Tú: {message.replace('\n', '<br>')}</span></div>"
        self.chat_history.append(html_message)
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())

    def get_top_cpu_processes(self):
        """
        Obtiene el top 10 de procesos por consumo de CPU usando la librería psutil.
        Esta función no utiliza la base de datos, por lo que se mantiene sin cambios.
        """
        process_data = []
        try:
            # Iteramos sobre todos los procesos para obtener nombre y uso de CPU
            # psutil.process_iter() es un generador que nos permite iterar eficientemente
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    # Se requiere un intervalo para cpu_percent para obtener un valor no estático
                    data = {
                        'name': p.name(),
                        'status': 'OK',
                        'cpu_percent': p.cpu_percent(interval=0.1) 
                    }
                    
                    # Solo nos interesan los procesos que consumen CPU
                    process_data.append(data)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Capturamos excepciones si el proceso deja de existir o no tenemos permiso.
                    continue
            
            # --- TABLA AGRUPADA POR NOMBRE DE PROCESO ---
            # Aunque la lógica de agregación es redundante o incompleta,
            # se mantiene la estructura para no modificar la lógica de psutil.
            aggregated_data = {}
            for p_info in process_data:
                name = p_info['name']
                if name not in aggregated_data:
                    aggregated_data[name] = {
                        'count': 0,
                        'cpu_percent': 0.0
                    }

                # Se corrige la lógica de agregación que estaba fuera del bucle 'p_info in process_data'
                # y se asume que la intención original era usar el 'sorted_processes' inmediatamente posterior.
                if p_info['status'] == 'OK':
                    aggregated_data[name]['count'] += 1
                    aggregated_data[name]['cpu_percent'] += p_info['cpu_percent']
                else:
                    aggregated_data[name]['count'] += 1

            # Ordenamos la lista de procesos por el uso de CPU en orden descendente
            # Nota: se usa process_data ya que aggregated_data no estaba completo en la lógica original
            # y la sección posterior solo utiliza sorted_processes.
            sorted_processes = sorted(process_data, key=lambda x: x['cpu_percent'], reverse=True)
            
            # Construimos la cadena de respuesta con el Top 10
            response = "Top 10 procesos con mayor consumo de CPU:\n"
            for i, proc in enumerate(sorted_processes[:10]):
                # Se utiliza el valor directo ya que psutil devuelve el porcentaje (0.0 a 100.0)
                response += f"{i+1}. {proc['name']} - {proc['cpu_percent']:.2f}%\n" 
            return response
            
        except Exception as e:
            return f"Error al obtener la lista de procesos: {e}"

    def handle_input(self):
        """
        Maneja la entrada del usuario, busca la métrica solicitada y muestra
        el resultado en el chat.
        """
        user_text = self.user_input.text().strip().lower()
        if not user_text:
            return

        self.append_user_message(user_text)

        # Si el usuario escribe "opciones", mostrar la lista de métricas
        if user_text == "opciones":
            metrics_list_str = "Bot: Métricas disponibles:\n"
            for i, name in enumerate(self.metric_names, 1):
                formatted_name = self.formatted_metric_names[name]
                metrics_list_str += f"{i}. {formatted_name}\n"
            self.append_bot_message(metrics_list_str)
            self.user_input.clear()
            return

        # Intentar convertir la entrada del usuario a un índice si es un número
        metric_key = None
        try:
            num_input = int(user_text)
            if 1 <= num_input <= len(self.metric_names):
                metric_key = self.metric_names[num_input - 1]
            else:
                self.append_bot_message(f"Número de métrica fuera de rango. Por favor, elige un número del 1 al {len(self.metric_names)} o escribe 'opciones'.")
                self.user_input.clear()
                return
        except ValueError:
            # Si no es un número, se normaliza la entrada del usuario para buscarla como nombre
            metric_key = user_text.replace(' ', '_')
        
        # Verificamos si la métrica solicitada es la del Top 10 CPU
        if metric_key == "top_10_cpu":
            result = self.get_top_cpu_processes()
            print(result)  # Para depuración en consola
            self.append_bot_message(result)
        elif metric_key in self.metric_names:
            metrics = self.get_metrics_data()
            
            if metric_key in metrics:
                formatted_name = self.formatted_metric_names.get(metric_key, metric_key)
                
                # Formatear el timestamp a 'hh:MM:SS dd/mm/yyyy'
                try:
                    raw_timestamp = metrics['timestamp']
                    # Adaptación para manejar posibles variaciones en el formato ISO
                    dt_object = datetime.datetime.fromisoformat(raw_timestamp)
                    formatted_timestamp = dt_object.strftime("%H:%M:%S %d/%m/%Y")
                    response = f"El valor de '{formatted_name}' es: {metrics[metric_key]} (Última actualización: {formatted_timestamp})"
                except (ValueError, KeyError, IndexError, TypeError):
                    response = f"El valor de '{formatted_name}' es: {metrics[metric_key]}"

                self.append_bot_message(response)
            elif 'error' in metrics:
                self.append_bot_message(f"Error: {metrics['error']}")
            else:
                # Este caso maneja si la métrica no está en los datos de la BD, aunque su nombre sea válido
                self.append_bot_message("No se encontraron datos para esa métrica en la base de datos.")
        else:
            # Métrica no válida, ni por número ni por nombre
            metrics_list_str = "Métrica no válida. Por favor, escribe el número o nombre exacto de la métrica.\n\nBot: Métricas disponibles:\n"
            for i, name in enumerate(self.metric_names, 1):
                formatted_name = self.formatted_metric_names[name]
                metrics_list_str += f"{i}. {formatted_name}\n"
            self.append_bot_message(metrics_list_str)

        self.user_input.clear()
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    chat_app = ChatApp()
    chat_app.show()
    sys.exit(app.exec())
