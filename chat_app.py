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

NOTA IMPORTANTE SOBRE DUCKDB:
Esta versión del código implementa una conexión transaccional (abrir-ejecutar-cerrar)
en modo de solo lectura (read_only=True) para cada consulta. Esto asegura que el 
archivo 'monitoreo.duckdb' se libere inmediatamente después de la lectura,
permitiendo que otro programa pueda escribir en él de forma periódica sin conflictos
de bloqueo de archivos.

Uso:
1. Asegúrate de tener Python instalado.
2. Instala PyQt6, psutil y duckdb usando pip.
3. Ejecuta este script desde la línea de comandos: python chat_app.py
"""

import sys
import time
import random
import psutil
import duckdb # Importación de DuckDB
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
        Inicializa la interfaz de usuario y establece la configuración de la ruta 
        de la base de datos DuckDB. La conexión se gestiona de forma transaccional 
        en las funciones de lectura.
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
        
        # --- Configuración de DuckDB (Solo ruta) ---
        # Ruta de la base de datos DuckDB especificada por el usuario
        db_path = "./data/monitoreo.duckdb"
        
        # Aseguramos que el directorio 'data' exista para la BD
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Almacenar la ruta; la conexión se gestionará de forma transaccional (abrir-ejecutar-cerrar).
        self.db_path = db_path
        
        # Se elimina la conexión persistente y las llamadas a create_table e insert_sample_data.

        # Estado inicial
        self.append_bot_message("¡Hola! Soy un bot de monitoreo del sistema. Escribe el número o nombre de una métrica para conocer su valor, o escribe 'opciones' para ver la lista de métricas.")
        self.append_bot_message(metrics_list_str)

    # --- FUNCIONES DE DUCKDB MODIFICADAS/AÑADIDAS ---

    def _duckdb_execute(self, query):
        """
        Gestiona la conexión transaccional (abrir-ejecutar-cerrar) y de solo lectura 
        a la base de datos DuckDB para ejecutar una consulta y obtener resultados.
        Esto asegura que el archivo .duckdb se libere inmediatamente para el proceso de escritura externo.
        
        :param query: Consulta SQL a ejecutar.
        :return: Resultado de la consulta como una lista de tuplas, o un diccionario de error.
        """
        try:
            # Conexión transaccional y de solo lectura. El bloque 'with' garantiza el cierre de la conexión.
            with duckdb.connect(database=self.db_path, read_only=True) as conn:
                result = conn.execute(query).fetchall()
                return result
        except duckdb.Error as e:
            # Captura errores específicos de DuckDB (ej. archivo no encontrado, tabla no existe, corrupción).
            error_msg = f"Error de DuckDB al ejecutar consulta: {e}. Confirme la existencia del archivo 'monitoreo.duckdb' y la tabla 'metricas'."
            self.append_bot_message(error_msg)
            return {'error': error_msg}

    def get_metrics_data(self):
        """
        Obtiene el último conjunto de datos de la tabla 'metricas' utilizando una 
        conexión transaccional (abrir-ejecutar-cerrar) de solo lectura.
        """
        query = "SELECT * FROM metricas ORDER BY timestamp DESC LIMIT 1"
        result_set = self._duckdb_execute(query) # Llama a la función transaccional
        
        # Verificar si _duckdb_execute retornó un error
        if isinstance(result_set, dict) and 'error' in result_set:
            # La función de ejecución ya notificó el error, solo retornamos el estado de error
            return result_set
            
        if not result_set or not result_set[0]:
            return {'error': 'No hay datos en la tabla de métricas.'}

        row = result_set[0]
        
        # Definición de columnas para mapear los resultados (se asume que la estructura de la tabla es conocida)
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
            raw_timestamp = metrics['timestamp']
            try:
                dt_object = datetime.datetime.strptime(raw_timestamp.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                metrics['timestamp'] = dt_object.strftime("%H:%M:%S %d/%m/%Y")
            except (ValueError, IndexError):
                metrics['timestamp'] = raw_timestamp # Deja el valor crudo si no se puede parsear

        return metrics
    
    # --- FUNCIONES DE ESCRITURA ELIMINADAS ---
    # Se han eliminado: create_table, insert_sample_data, y generate_random_data.

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
        Esta función no interactúa con DuckDB.
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
            
            # Si se encuentra un error en la lectura de DuckDB, se detiene
            if 'error' in metrics:
                # El mensaje de error ya fue mostrado por _duckdb_execute o get_metrics_data
                self.user_input.clear()
                return

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
