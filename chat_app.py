# -*- coding: utf-8 -*-
# Título: Monitor de Métricas del Sistema Interactivo (DuckDB Backend)

"""
Este script crea una aplicación de escritorio con PyQt6 que actúa como un
monitor de sistema interactivo. El usuario puede escribir el nombre de una
métrica de sistema para obtener un valor almacenado en una base de datos DuckDB.
Ahora también incluye la opción para obtener el Top 10 de procesos por consumo de CPU.

Para su correcto funcionamiento, necesitas instalar las librerías:
pip install pyqt6
pip install psutil
pip install duckdb

Uso:
1. Asegúrate de tener Python instalado.
2. Instala PyQt6, psutil y duckdb usando pip.
3. Ejecuta este script desde la línea de comandos: python chat_app.py
"""

import sys
import time
import random
import psutil
import duckdb # Importación de DuckDB en reemplazo de sqlite3
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
        """
        Inicializa la interfaz de usuario y establece la conexión con la base de datos DuckDB.
        """
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
        
        # Conexión a la base de datos DuckDB
        self.conn = None
        
        # Ruta de la base de datos DuckDB especificada por el usuario
        # Modificación: Cambiado a monitoreo.duckdb
        db_path = "./data/monitoreo.duckdb"
        
        # Aseguramos que el directorio 'data' exista para la BD
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        try:
            # Conexión utilizando el API de DuckDB
            self.conn = duckdb.connect(database=db_path, read_only=True)
            self.create_table()
            self.insert_sample_data() # Insertar datos de ejemplo
        except duckdb.Error as e: # Manejo de errores específico de DuckDB
            self.append_bot_message(f"Error al conectar con la base de datos DuckDB: {e}")
            self.conn = None

        # Estado inicial
        self.append_bot_message("¡Hola! Soy un bot de monitoreo del sistema. Escribe el número o nombre de una métrica para conocer su valor, o escribe 'opciones' para ver la lista de métricas.")
        self.append_bot_message(metrics_list_str)

    def create_table(self):
        """
        Crea la tabla de métricas si no existe utilizando la conexión DuckDB.
        """
        if not self.conn:
            return
        
        create_table_query = """
                CREATE TABLE IF NOT EXISTS metricas (
                    timestamp TEXT PRIMARY KEY,
                    hostname TEXT,
                    username TEXT,
                    cpu_percent DOUBLE,
                    cpu_freq DOUBLE,
                    ram_percent DOUBLE,
                    ram_used DOUBLE,
                    ram_total DOUBLE,
                    ram_free DOUBLE,
                    disk_percent DOUBLE,
                    disk_used DOUBLE,
                    disk_total DOUBLE,
                    disk_free DOUBLE,
                    swap_percent DOUBLE,
                    swap_usado DOUBLE,
                    swap_total DOUBLE,
                    red_bytes_sent BIGINT,
                    red_bytes_recv BIGINT,
                    cpu_temp_celsius DOUBLE,
                    battery_percent DOUBLE,
                    cpu_power_package DOUBLE,
                    cpu_power_cores DOUBLE,
                    cpu_clocks DOUBLE
                )
        """
        try:
            self.conn.execute(create_table_query)
        except duckdb.Error as e:
            self.append_bot_message(f"Error al crear la tabla en DuckDB: {e}")

    def insert_sample_data(self):
        """
        Inserta datos de ejemplo en la tabla si está vacía, adaptado para DuckDB.
        """
        if not self.conn:
            return
        
        try:
            # 1. Verificar si hay datos
            count_result = self.conn.execute("SELECT COUNT(*) FROM metricas").fetchone()
            count = count_result[0] if count_result else 0
            
            if count == 0:
                sample_data = self.generate_random_data()
                columns = ', '.join(sample_data.keys())
                placeholders = ', '.join('?' * len(sample_data))
                query = f"INSERT INTO metricas ({columns}) VALUES ({placeholders})"
                
                # 2. Insertar datos con parámetros
                self.conn.execute(query, tuple(sample_data.values()))
                self.append_bot_message("Se han insertado datos de ejemplo en la base de datos DuckDB.")
        except duckdb.Error as e:
            self.append_bot_message(f"Error al insertar datos de ejemplo en DuckDB: {e}")

    def generate_random_data(self):
        """Genera un conjunto de datos aleatorios para la inserción."""
        ram_total_gb = 16
        disk_total_gb = 1000

        ram_percent_val = random.uniform(0.0, 100.0)
        disk_percent_val = random.uniform(0.0, 100.0)
        swap_percent_val = random.uniform(0.0, 100.0)

        return {
            'timestamp': datetime.datetime.now().isoformat(),
            'cpu_percent': random.uniform(0.0, 100.0),
            'cpu_freq': random.uniform(0.8, 4.5),
            'ram_percent': ram_percent_val,
            'ram_used': ram_total_gb * (ram_percent_val / 100),
            'ram_total': ram_total_gb,
            'ram_free': ram_total_gb * (1 - ram_percent_val / 100),
            'disk_percent': disk_percent_val,
            'disk_used': disk_total_gb * (disk_percent_val / 100),
            'disk_total': disk_total_gb,
            'disk_free': disk_total_gb * (1 - disk_percent_val / 100),
            'swap_percent': swap_percent_val,
            'swap_usado': 2 * (swap_percent_val / 100),
            'swap_total': 2,
            'red_bytes_sent': random.randint(100000, 100000000),
            'red_bytes_recv': random.randint(100000, 100000000),
            'cpu_temp_celsius': random.uniform(30.0, 80.0),
            'battery_percent': random.uniform(0.0, 100.0),
            'cpu_power_package': random.uniform(10.0, 100.0),
            'cpu_power_cores': random.uniform(5.0, 90.0),
            'cpu_clocks': random.randint(1000000, 5000000)
        }

    def get_metrics_data(self):
        """
        Obtiene el último conjunto de datos de la base de datos `monitoreo.duckdb`
        y aplica formato de visualización de manera defensiva.
        """
        if not self.conn:
            return {'error': 'No se pudo conectar a la base de datos DuckDB.'}
        try:
            # Ejecutar la consulta y obtener el último registro
            result = self.conn.execute("SELECT * FROM metricas ORDER BY timestamp DESC LIMIT 1")
            row = result.fetchone()
            
            if not row:
                return {'error': 'No hay datos en la tabla de métricas.'}

            # Definición de columnas para mapear los resultados
            columns = [
                "timestamp", "hostname", "username", "cpu_percent", "cpu_freq",
                "ram_percent", "ram_used",
                "ram_total", "ram_free", "disk_percent",
                "disk_used", "disk_total", "disk_free", "swap_percent",
                "swap_usado", "swap_total", "red_bytes_sent", "red_bytes_recv",
                "cpu_temp_celsius", "battery_percent", "cpu_power_package",
                "cpu_power_cores", "cpu_clocks"
            ]
            
            # Crear un diccionario a partir de la fila y los nombres de las columnas
            metrics = dict(zip(columns, row))

            # --- Lógica de Formateo de Datos Defensivo (Corrección de ValueError) ---
            # Aplicamos una conversión explícita a float antes de formatear,
            # y usamos un try/except para manejar cualquier valor no numérico con 'N/A'.

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
                    return "N/A"

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

            # Manejar el timestamp que no es numérico
            if 'timestamp' in metrics and metrics['timestamp'] is not None:
                # Se mantiene la lógica de formateo del timestamp
                raw_timestamp = metrics['timestamp']
                try:
                    dt_object = datetime.datetime.strptime(raw_timestamp.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                    metrics['timestamp'] = dt_object.strftime("%H:%M:%S %d/%m/%Y")
                except (ValueError, IndexError):
                    metrics['timestamp'] = raw_timestamp # Deja el valor crudo si no se puede parsear


            return metrics
        except duckdb.Error as e: # Manejo de errores de DuckDB
            return {'error': f"Error al leer de la base de datos DuckDB: {e}"}

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
        """
        process_data = []
        try:
            # Iteramos sobre todos los procesos para obtener nombre y uso de CPU
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    proc = psutil.Process(p.info['pid']) 
                    data = {
                        'name': p.name(),
                        'status': 'OK',
                        'cpu_percent': p.cpu_percent(interval=0.1)
                    }
                    
                    if data['cpu_percent'] > 0.0:
                        process_data.append(data)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # --- AGRUPACIÓN Y ORDENACIÓN ---
            aggregated_data = {}
            for p_info in process_data:
                name = p_info['name']
                cpu_p = p_info['cpu_percent']
                
                if name not in aggregated_data:
                    aggregated_data[name] = {
                        'count': 0,
                        'cpu_percent': 0.0
                    }
                
                aggregated_data[name]['count'] += 1
                aggregated_data[name]['cpu_percent'] += cpu_p

            # Ordenamos por el total de consumo de CPU agregado
            sort_key = lambda item: item[1]['cpu_percent']
            sorted_items = sorted(aggregated_data.items(), key=sort_key, reverse=True)
            
            # Construimos la cadena de respuesta con el Top 10
            response = "Top 10 procesos con mayor consumo de CPU (Agrupado por Nombre):\n"
            for i, (name, data) in enumerate(sorted_items[:10]):
                # Se utiliza el consumo total del grupo
                response += f"{i+1}. {name} - {data['cpu_percent']:.2f}% (Instancias: {data['count']})\n"
            
            if not sorted_items:
                response = "No se encontraron procesos activos con consumo de CPU significativo."
                
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
            self.append_bot_message(result)
        elif metric_key in self.metric_names:
            metrics = self.get_metrics_data()
            
            if metric_key in metrics:
                formatted_name = self.formatted_metric_names.get(metric_key, metric_key)
                
                # Ya que el formateo del valor se hizo en get_metrics_data, solo extraemos el valor
                metric_value = metrics[metric_key]
                formatted_timestamp = metrics.get('timestamp', 'Desconocida')
                
                # Comprobación de seguridad para los casos que get_metrics_data devuelve None o N/A
                if metric_value is None or metric_value == "N/A":
                    response = f"El valor de '{formatted_name}' no está disponible o no se pudo procesar."
                else:
                    response = f"El valor de '{formatted_name}' es: {metric_value} (Última actualización: {formatted_timestamp})"

                self.append_bot_message(response)
            elif 'error' in metrics:
                self.append_bot_message(f"{metrics['error']}")
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
