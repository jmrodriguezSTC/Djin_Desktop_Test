# -*- coding: utf-8 -*-
# Título: Monitor de Métricas del Sistema Interactivo

"""
Este script crea una aplicación de escritorio con PyQt6 que actúa como un
monitor de sistema interactivo. El usuario puede escribir el nombre de una
métrica de sistema para obtener un valor almacenado en una base de datos SQLite.
Ahora también incluye la opción para obtener el Top 10 de procesos por consumo de CPU.

Para su correcto funcionamiento, necesitas instalar las librerías:
pip install pyqt6
pip install psutil

Uso:
1. Asegúrate de tener Python instalado.
2. Instala PyQt6 y psutil usando pip.
3. Ejecuta este script desde la línea de comandos: python chat_app.py
"""

import sys
import time
import random
import psutil
import sqlite3
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
            "cpu_percent", "cpu_load_percent", "cpu_freq",
            "ram_percent", "ram_load_percent", "ram_used", "ram_load_used",
            "ram_total", "ram_free", "ram_load_free", "disco_percent",
            "disk_used", "disk_total", "disk_free", "swap_percent",
            "swap_usado", "swap_total", "red_bytes_sent", "red_bytes_recv",
            "cpu_temp_celsius", "battery_percent", "cpu_power_package",
            "cpu_power_cores", "cpu_clocks", "hdd_used",
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
        
        # Conexión a la base de datos
        self.conn = None
        self.cursor = None
        
        # Ruta de la base de datos especificada por el usuario
        db_path = "C:/Users/jmrodriguez/Downloads/Projects/Tests/Djin_Test/build/Pruebas/exe.win-amd64-3.13/monitoreo.db"
        
        try:
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
            self.create_table()
            self.insert_sample_data() # Insertar datos de ejemplo
        except sqlite3.Error as e:
            self.append_bot_message(f"Error al conectar con la base de datos: {e}")
            self.conn = None

        # Estado inicial
        self.append_bot_message("¡Hola! Soy un bot de monitoreo del sistema. Escribe el número o nombre de una métrica para conocer su valor, o escribe 'opciones' para ver la lista de métricas.")
        self.append_bot_message(metrics_list_str)

    def create_table(self):
        """Crea la tabla de métricas si no existe."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS metricas (
            timestamp TEXT PRIMARY KEY,
            cpu_percent REAL,
            cpu_load_percent REAL,
            cpu_freq REAL,
            ram_percent REAL,
            ram_load_percent REAL,
            ram_used REAL,
            ram_load_used REAL,
            ram_total REAL,
            ram_free REAL,
            ram_load_free REAL,
            disco_percent REAL,
            disk_used REAL,
            disk_total REAL,
            disk_free REAL,
            swap_percent REAL,
            swap_usado REAL,
            swap_total REAL,
            red_bytes_sent INTEGER,
            red_bytes_recv INTEGER,
            cpu_temp_celsius REAL,
            battery_percent REAL,
            cpu_power_package REAL,
            cpu_power_cores REAL,
            cpu_clocks REAL,
            hdd_used REAL
        );
        """
        self.cursor.execute(create_table_query)
        self.conn.commit()

    def insert_sample_data(self):
        """
        Inserta datos de ejemplo en la tabla si está vacía.
        """
        self.cursor.execute("SELECT COUNT(*) FROM metricas")
        count = self.cursor.fetchone()[0]
        if count == 0:
            sample_data = self.generate_random_data()
            columns = ', '.join(sample_data.keys())
            placeholders = ', '.join('?' * len(sample_data))
            query = f"INSERT INTO metricas ({columns}) VALUES ({placeholders})"
            self.cursor.execute(query, tuple(sample_data.values()))
            self.conn.commit()
            self.append_bot_message("Se han insertado datos de ejemplo en la base de datos.")

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
            'cpu_load_percent': random.uniform(0.0, 100.0),
            'cpu_freq': random.uniform(0.8, 4.5),
            'ram_percent': ram_percent_val,
            'ram_load_percent': ram_percent_val,
            'ram_used': ram_total_gb * (ram_percent_val / 100),
            'ram_load_used': ram_total_gb * (ram_percent_val / 100),
            'ram_total': ram_total_gb,
            'ram_free': ram_total_gb * (1 - ram_percent_val / 100),
            'ram_load_free': ram_total_gb * (1 - ram_percent_val / 100),
            'disco_percent': disk_percent_val,
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
            'cpu_clocks': random.randint(1000000, 5000000),
            'hdd_used': random.uniform(0, disk_total_gb)
        }

    def get_metrics_data(self):
        """
        Obtiene el último conjunto de datos de la base de datos `monitoreo.db`.
        """
        if not self.conn:
            return {'error': 'No se pudo conectar a la base de datos.'}
        try:
            self.cursor.execute("SELECT * FROM metricas ORDER BY timestamp DESC LIMIT 1")
            row = self.cursor.fetchone()
            if not row:
                return {'error': 'No hay datos en la tabla de métricas.'}

            columns = [
                "timestamp", "cpu_percent", "cpu_load_percent", "cpu_freq",
                "ram_percent", "ram_load_percent", "ram_used", "ram_load_used",
                "ram_total", "ram_free", "ram_load_free", "disco_percent",
                "disk_used", "disk_total", "disk_free", "swap_percent",
                "swap_usado", "swap_total", "red_bytes_sent", "red_bytes_recv",
                "cpu_temp_celsius", "battery_percent", "cpu_power_package",
                "cpu_power_cores", "cpu_clocks", "hdd_used"
            ]
            
            # Crear un diccionario a partir de la fila y los nombres de las columnas
            metrics = dict(zip(columns, row))

            # Formatear los datos para una mejor visualización, convirtiendo a float o int
            # donde sea necesario.
            for key in metrics:
                # Si el valor es una cadena, limpiar el símbolo de '%' y convertir a float
                if isinstance(metrics[key], str) and metrics[key].endswith('%'):
                    metrics[key] = metrics[key].replace('%', '')
                
                if key in self.metric_names:
                    if metrics[key] is not None:
                        try:
                            if key in ['red_bytes_sent', 'red_bytes_recv']:
                                metrics[key] = int(metrics[key])
                            else:
                                metrics[key] = float(metrics[key])
                        except (ValueError, TypeError):
                             # Manejar casos donde la conversión falla
                             pass

            # Aplicar el formato deseado
            if 'cpu_percent' in metrics and metrics['cpu_percent'] is not None:
                metrics['cpu_percent'] = f"{metrics['cpu_percent']:.2f}%"
            if 'cpu_load_percent' in metrics and metrics['cpu_load_percent'] is not None:
                metrics['cpu_load_percent'] = f"{metrics['cpu_load_percent']:.2f}%"
            if 'cpu_freq' in metrics and metrics['cpu_freq'] is not None:
                metrics['cpu_freq'] = f"{metrics['cpu_freq']:.2f} MHz"
            if 'ram_percent' in metrics and metrics['ram_percent'] is not None:
                metrics['ram_percent'] = f"{metrics['ram_percent']:.2f}%"
            if 'ram_load_percent' in metrics and metrics['ram_load_percent'] is not None:
                metrics['ram_load_percent'] = f"{metrics['ram_load_percent']:.2f}%"
            if 'ram_used' in metrics and metrics['ram_used'] is not None:
                metrics['ram_used'] = f"{metrics['ram_used']:.2f} GB"
            if 'ram_load_used' in metrics and metrics['ram_load_used'] is not None:
                metrics['ram_load_used'] = f"{metrics['ram_load_used']:.2f} GB"
            if 'ram_total' in metrics and metrics['ram_total'] is not None:
                metrics['ram_total'] = f"{metrics['ram_total']:.2f} GB"
            if 'ram_free' in metrics and metrics['ram_free'] is not None:
                metrics['ram_free'] = f"{metrics['ram_free']:.2f} GB"
            if 'ram_load_free' in metrics and metrics['ram_load_free'] is not None:
                metrics['ram_load_free'] = f"{metrics['ram_load_free']:.2f} GB"
            if 'disco_percent' in metrics and metrics['disco_percent'] is not None:
                metrics['disco_percent'] = f"{metrics['disco_percent']:.2f}%"
            if 'disk_used' in metrics and metrics['disk_used'] is not None:
                metrics['disk_used'] = f"{metrics['disk_used']:.2f} GB"
            if 'disk_total' in metrics and metrics['disk_total'] is not None:
                metrics['disk_total'] = f"{metrics['disk_total']:.2f} GB"
            if 'disk_free' in metrics and metrics['disk_free'] is not None:
                metrics['disk_free'] = f"{metrics['disk_free']:.2f} GB"
            if 'swap_percent' in metrics and metrics['swap_percent'] is not None:
                metrics['swap_percent'] = f"{metrics['swap_percent']:.2f}%"
            if 'swap_usado' in metrics and metrics['swap_usado'] is not None:
                metrics['swap_usado'] = f"{metrics['swap_usado']:.2f} GB"
            if 'swap_total' in metrics and metrics['swap_total'] is not None:
                metrics['swap_total'] = f"{metrics['swap_total']:.2f} GB"
            if 'red_bytes_sent' in metrics and metrics['red_bytes_sent'] is not None:
                metrics['red_bytes_sent'] = f"{metrics['red_bytes_sent'] / (1024**2):.2f} MB"
            if 'red_bytes_recv' in metrics and metrics['red_bytes_recv'] is not None:
                metrics['red_bytes_recv'] = f"{metrics['red_bytes_recv'] / (1024**2):.2f} MB"
            if 'cpu_temp_celsius' in metrics and metrics['cpu_temp_celsius'] is not None:
                metrics['cpu_temp_celsius'] = f"{metrics['cpu_temp_celsius']:.2f} °C"
            if 'battery_percent' in metrics and metrics['battery_percent'] is not None:
                metrics['battery_percent'] = f"{metrics['battery_percent']:.2f}%"
            if 'cpu_power_package' in metrics and metrics['cpu_power_package'] is not None:
                metrics['cpu_power_package'] = f"{metrics['cpu_power_package']:.2f} W"
            if 'cpu_power_cores' in metrics and metrics['cpu_power_cores'] is not None:
                metrics['cpu_power_cores'] = f"{metrics['cpu_power_cores']:.2f} W"
            if 'hdd_used' in metrics and metrics['hdd_used'] is not None:
                metrics['hdd_used'] = f"{metrics['hdd_used']:.2f} %"
            if 'cpu_clocks' in metrics and metrics['cpu_clocks'] is not None:
                metrics['cpu_clocks'] = f"{metrics['cpu_clocks']:.2f} MHz"
            
            # El campo 'cpu_clocks' ya es un string en el ejemplo original, no necesita formato
            
            return metrics
        except sqlite3.Error as e:
            return {'error': f"Error al leer de la base de datos: {e}"}

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
            # psutil.process_iter() es un generador que nos permite iterar eficientemente
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    proc = psutil.Process(p.info['pid'])
                    # Recolección de datos
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
            aggregated_data = {}
            for p_info in process_data:
                name = p_info['name']
                if name not in aggregated_data:
                    aggregated_data[name] = {
                        'count': 0,
                        'cpu_percent': 0.0
                    }

            if p_info['status'] == 'OK':
                aggregated_data[name]['count'] += 1
                aggregated_data[name]['cpu_percent'] += p_info['cpu_percent']
            else:
                aggregated_data[name]['count'] += 1


            # Ordenamos la lista de procesos por el uso de CPU en orden descendente
            sorted_processes = sorted(process_data, key=lambda x: x['cpu_percent'], reverse=True)
            
            sort_key = lambda item: item[1]['cpu_percent']
            reverse = True
            sorted_items = sorted(aggregated_data.items(), key=sort_key, reverse=reverse)
            # Construimos la cadena de respuesta con el Top 10
            response = "Top 10 procesos con mayor consumo de CPU:\n"
            for i, proc in enumerate(sorted_processes[:10]):
                response += f"{i+1}. {proc['name']} - {proc['cpu_percent']/100:.2f}%\n"
            return response

            # Construimos la cadena de respuesta con el Top 10
            response = "Top 10 procesos con mayor consumo de CPU:\n"
            for i, proc in enumerate(sorted_processes[:10]):
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
                    dt_object = datetime.datetime.strptime(raw_timestamp.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                    formatted_timestamp = dt_object.strftime("%H:%M:%S %d/%m/%Y")
                    response = f"El valor de '{formatted_name}' es: {metrics[metric_key]} (Última actualización: {formatted_timestamp})"
                except (ValueError, KeyError, IndexError):
                    response = f"El valor de '{formatted_name}' es: {metrics[metric_key]}"

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
