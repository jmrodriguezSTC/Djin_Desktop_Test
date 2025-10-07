# -*- coding: utf-8 -*-
# Título: Monitor de Métricas del Sistema Interactivo (Usando DuckDB y Parquet)

"""
Este script crea una aplicación de escritorio con PyQt6 que actúa como un
monitor de sistema interactivo. El usuario puede escribir el nombre de una
métrica de sistema para obtener un valor almacenado en archivos Parquet
utilizando DuckDB.

Para su correcto funcionamiento, necesitas instalar las librerías:
pip install pyqt6
pip install psutil
pip install duckdb
pip install pandas # DuckDB a menudo se usa con pandas, aunque aquí es opcional.

Uso:
1. Asegúrate de tener Python instalado.
2. Instala PyQt6, psutil y duckdb usando pip.
3. Ejecuta este script desde la línea de comandos: python chat_app.py
"""

import sys
import os
import datetime
import psutil
import duckdb # Importación de DuckDB
# Importaciones de PyQt6
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                             QWidget, QTextEdit, QLineEdit, QLabel)
from PyQt6.QtCore import Qt

class ChatApp(QMainWindow):
    """
    Clase principal de la aplicación que crea la ventana y gestiona la lógica
    del chat para mostrar las métricas del sistema, leyendo desde archivos Parquet
    con DuckDB.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador de Chat de Métricas (DuckDB)")
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

        # -------------------------------------------------------------------
        # Inicialización de DuckDB y configuración de rutas
        # -------------------------------------------------------------------
        self.duck_conn = None
        # La ruta de búsqueda de DuckDB para los archivos Parquet
        # El patrón '*' permite leer todos los archivos parquet en la carpeta.
        self.parquet_path = os.path.join(os.getcwd(), 'data', 'metricas', '*.parquet')
        
        try:
            # Conexión a DuckDB en modo en memoria.
            # DuckDB se usará para consultar los archivos Parquet directamente.
            self.duck_conn = duckdb.connect(database=':memory:', read_only=False)
            self.duck_conn.execute("SET enable_progress_bar=false;")
            self.append_bot_message("Conexión a DuckDB establecida. Leyendo datos desde archivos Parquet.")
            
            # Verificación inicial de la existencia de archivos
            if not self._check_parquet_files():
                 self.append_bot_message(f"Advertencia: No se encontraron archivos Parquet en la ruta: {os.path.dirname(self.parquet_path)}")
                 self.append_bot_message("Por favor, asegúrese de que el programa 'Djin' haya generado métricas.")

        except Exception as e:
            self.append_bot_message(f"Error al inicializar DuckDB: {e}")
            self.duck_conn = None
        
        # Definir la lista de métricas (incluyendo las nuevas columnas y top_10_cpu)
        self.metric_names = [
            "hostname", "username", "cpu_percent", "cpu_freq",
            "ram_percent", "ram_used",
            "ram_total", "ram_free", "disk_percent",
            "disk_used", "disk_total", "disk_free", "swap_percent",
            "swap_usado", "swap_total", "red_bytes_sent", "red_bytes_recv",
            "cpu_temp_celsius", "battery_percent", "cpu_power_package",
            "cpu_power_cores", "cpu_clocks",
            "top_10_cpu"  # Métrica de procesos en vivo
        ]
        
        # Diccionario para mapear nombres originales a nombres formateados
        self.formatted_metric_names = {name: " ".join(part.capitalize() for part in name.split('_')) for name in self.metric_names}
        # Sobreescribir el formato de la nueva métrica
        self.formatted_metric_names["top_10_cpu"] = "Top 10 Apps High CPU (Live)"

        # Construir la lista de métricas para el mensaje inicial
        metrics_list_str = "Bot: Métricas disponibles:\n"
        for i, name in enumerate(self.metric_names, 1):
            formatted_name = self.formatted_metric_names[name]
            metrics_list_str += f"{i}. {formatted_name}\n"
        
        # Estado inicial
        self.append_bot_message("¡Hola! Soy Mayordomo, un bot de monitoreo del sistema. Escribe el número o nombre de una métrica para conocer su valor, o escribe 'opciones' para ver la lista de métricas.")
        self.append_bot_message(metrics_list_str)

    def _check_parquet_files(self):
        """Verifica si existen archivos Parquet en la ruta configurada."""
        import glob
        return bool(glob.glob(self.parquet_path))

    def get_metrics_data(self):
        """
        Obtiene el último conjunto de datos leyendo los archivos Parquet
        mediante una consulta SQL de DuckDB.
        """
        if not self.duck_conn:
            return {'error': 'No se pudo conectar a DuckDB.'}
        
        # Definición de columnas esperadas (ajustada para incluir hostname y username)
        columns = [
            "timestamp", "hostname", "username", "cpu_percent", "cpu_freq",
            "ram_percent", "ram_used", "ram_total", "ram_free", "disk_percent",
            "disk_used", "disk_total", "disk_free", "swap_percent",
            "swap_usado", "swap_total", "red_bytes_sent", "red_bytes_recv",
            "cpu_temp_celsius", "battery_percent", "cpu_power_package",
            "cpu_power_cores", "cpu_clocks"
        ]

        # La consulta DuckDB utiliza el operador de tabla virtual read_parquet
        # para escanear todos los archivos en el patrón.
        # Luego ordena por timestamp (TEXT) y toma el último registro.
        query = f"""
        SELECT *
        FROM read_parquet('{self.parquet_path}')
        ORDER BY timestamp DESC
        LIMIT 1
        """

        try:
            result = self.duck_conn.execute(query).fetchone()
            
            if not result:
                return {'error': f'No hay datos en los archivos Parquet en {os.path.dirname(self.parquet_path)}.'}

            # Crear un diccionario a partir de la fila y los nombres de las columnas
            metrics = dict(zip(columns, result))

            # --- Lógica de Formateo de Datos Defensivo ---
            def safe_format(key, suffix, is_bytes=False):
                """Convierte a float y formatea el valor de manera segura."""
                value = metrics.get(key)
                # Manejar valores de texto (hostname, username, timestamp)
                if isinstance(value, str):
                    return value
                
                if value is None:
                    return None
                
                try:
                    # Intenta convertir a float, si ya es numérico, funciona igual.
                    numeric_value = float(value)
                    
                    if is_bytes:
                        # Convertir de bytes a MB para red
                        # Se usa 1024**2 para conversión a MiB (Mebibytes)
                        return f"{numeric_value / (1024**2):.2f} {suffix}"
                    
                    # Formateo general con 2 decimales
                    return f"{numeric_value:.2f} {suffix}"
                except (ValueError, TypeError):
                    # Si el valor no es convertible a numérico
                    return "N/A"

            # Aplicar el formato de visualización final usando safe_format
            metrics['hostname'] = safe_format('hostname', '')
            metrics['username'] = safe_format('username', '')
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
            
        except duckdb.ParserException:
             # DuckDB lanza esta excepción si la consulta falla (ej. archivos corruptos)
             return {'error': 'Error de DuckDB al parsear la consulta o leer los archivos Parquet. Verifique que los archivos no estén corruptos.'}
        except Exception as e:
            return {'error': f"Error general al leer los datos de métricas con DuckDB: {e}"}

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
        Obtiene el top 10 de procesos por consumo de CPU usando la librería psutil (Lógica en vivo).
        Esta función se mantiene sin cambios ya que lee datos del sistema operativo en tiempo real.
        """
        process_data = []
        try:
            # Obtenemos la información de los procesos
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    # Obtenemos el porcentaje de CPU con un intervalo de 0.1 segundos
                    data = {
                        'name': p.name(),
                        'cpu_percent': p.cpu_percent(interval=0.1)
                    }
                    process_data.append(data)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Capturamos excepciones si el proceso deja de existir o no tenemos permiso.
                    continue
            
            # Agrupamos los procesos por nombre y sumamos el uso de CPU
            aggregated_data = {}
            for p_info in process_data:
                name = p_info['name']
                if name not in aggregated_data:
                    aggregated_data[name] = 0.0
                aggregated_data[name] += p_info['cpu_percent']

            # Convertimos a lista para ordenar
            sorted_processes = sorted(aggregated_data.items(), key=lambda item: item[1], reverse=True)
            
            # Construimos la cadena de respuesta con el Top 10
            response = "Top 10 procesos con mayor consumo de CPU (en vivo):\n"
            if not sorted_processes:
                 response += "No se pudieron obtener datos de procesos."
            else:
                for i, (name, cpu_percent) in enumerate(sorted_processes[:10]):
                    # Formateamos el porcentaje para mostrarlo limpiamente
                    response += f"{i+1}. {name} - {cpu_percent:.2f}%\n"
            
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

        # Lógica de manejo de entrada... (sin cambios aquí)
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
                # Caso especial para métricas de texto que no requieren timestamp
                if metric_key in ["hostname", "username"]:
                    response = f"El valor de '{self.formatted_metric_names.get(metric_key, metric_key)}' es: {metrics[metric_key]}"
                else:
                    formatted_name = self.formatted_metric_names.get(metric_key, metric_key)
                    
                    # Formatear el timestamp a 'hh:MM:SS dd/mm/yyyy'
                    try:
                        raw_timestamp = metrics.get('timestamp')
                        if raw_timestamp:
                            # Intenta convertir el timestamp (asumiendo formato ISO 8601)
                            dt_object = datetime.datetime.fromisoformat(raw_timestamp.split('+')[0]) # Manejar zonas horarias opcionales
                            formatted_timestamp = dt_object.strftime("%H:%M:%S %d/%m/%Y")
                            response = f"El valor de '{formatted_name}' es: {metrics[metric_key]} (Última actualización: {formatted_timestamp})"
                        else:
                            response = f"El valor de '{formatted_name}' es: {metrics[metric_key]} (Última actualización: N/A)"
                    except (ValueError, KeyError, IndexError):
                        # Manejar el caso de error en el timestamp
                        response = f"El valor de '{formatted_name}' es: {metrics[metric_key]}"

                self.append_bot_message(response)
            elif 'error' in metrics:
                self.append_bot_message(f"Error al obtener métrica: {metrics['error']}")
            else:
                self.append_bot_message("No se encontraron datos recientes para esa métrica. Verifique si hay archivos Parquet disponibles.")
        else:
            # Métrica no válida, ni por número ni por nombre
            metrics_list_str = "Métrica no válida. Por favor, escribe el número o nombre exacto de la métrica.\n\nBot: Métricas disponibles:\n"
            for i, name in enumerate(self.metric_names, 1):
                formatted_name = self.formatted_metric_names[name]
                metrics_list_str += f"{i}. {formatted_name}\n"
            self.append_bot_message(metrics_list_str)

        self.user_input.clear()
        
if __name__ == '__main__':
    # Aseguramos que la carpeta data/metricas exista para evitar errores de DuckDB si es necesario
    os.makedirs(os.path.join('data', 'metricas'), exist_ok=True)
    
    app = QApplication(sys.argv)
    chat_app = ChatApp()
    chat_app.show()
    sys.exit(app.exec())
