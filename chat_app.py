# -*- coding: utf-8 -*-
# Título: Monitor de Métricas del Sistema Interactivo

"""
Este script crea una aplicación de escritorio con PyQt6 que actúa como un
monitor de sistema interactivo. El usuario puede escribir el nombre de una
métrica de sistema para obtener un valor simulado en tiempo real.

Este script utiliza psutil para mantener la compatibilidad, pero genera
valores aleatorios para las métricas.

Para su correcto funcionamiento, necesitas instalar la librería psutil:
pip install psutil

Uso:
1. Asegúrate de tener Python instalado.
2. Instala PyQt6 y psutil usando pip.
3. Ejecuta este script desde la línea de comandos: python system_monitor.py
"""

import sys
import time
import random
import psutil # Se mantiene la importación según la solicitud
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

        # Definir la lista de métricas para mostrar y validar
        self.metric_names = [
            "timestamp", "cpu_percent", "cpu_load_percent", "cpu_freq",
            "ram_percent", "ram_load_percent", "ram_used", "ram_load_used",
            "ram_total", "ram_free", "ram_load_free", "disco_percent",
            "disk_used", "disk_total", "disk_free", "swap_percent",
            "swap_usado", "swap_total", "red_bytes_sent", "red_bytes_recv",
            "cpu_temp_celsius", "battery_percent", "cpu_power_package",
            "cpu_power_cores", "cpu_clocks", "hdd_used"
        ]
        
        # Diccionario para mapear nombres originales a nombres formateados
        self.formatted_metric_names = {name: " ".join(part.capitalize() for part in name.split('_')) for name in self.metric_names}

        # Construir la lista de métricas para el mensaje inicial, con el formato nuevo
        metrics_list_str = "Bot: Métricas disponibles:\n"
        for i, name in enumerate(self.metric_names, 1):
            formatted_name = self.formatted_metric_names[name]
            metrics_list_str += f"{i}. {formatted_name}\n"

        # Estado inicial
        self.append_bot_message("¡Hola! Soy un bot de monitoreo del sistema. Escribe el número o nombre de una métrica para conocer su valor.")
        self.append_bot_message(metrics_list_str)

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

    def get_metrics_data(self):
        """
        Genera valores aleatorios para todas las métricas del sistema.
        """
        try:
            # Valores fijos para simular un sistema con 16 GB de RAM y 1 TB de disco
            ram_total_gb = 16
            disk_total_gb = 1000

            # Métricas de CPU
            cpu_percent_val = random.uniform(0.0, 100.0)
            cpu_load_percent_val = random.uniform(0.0, 100.0)
            cpu_freq_val = random.uniform(0.8, 4.5)
            cpu_clocks_val = random.randint(1000000, 5000000)
            
            # Métricas de RAM
            ram_percent_val = random.uniform(0.0, 100.0)
            ram_used_gb = ram_total_gb * (ram_percent_val / 100)
            ram_free_gb = ram_total_gb - ram_used_gb
            
            # Métricas de disco
            disk_percent_val = random.uniform(0.0, 100.0)
            disk_used_gb = disk_total_gb * (disk_percent_val / 100)
            disk_free_gb = disk_total_gb - disk_used_gb
            
            # Métricas de swap
            swap_total_gb = 2
            swap_percent_val = random.uniform(0.0, 100.0)
            swap_usado_gb = swap_total_gb * (swap_percent_val / 100)

            # Métricas de red
            red_bytes_sent_val = random.randint(100000, 100000000)
            red_bytes_recv_val = random.randint(100000, 100000000)

            # Métricas de hardware
            cpu_temp_celsius_val = random.uniform(30.0, 80.0)
            battery_percent_val = random.uniform(0.0, 100.0)
            cpu_power_package_val = random.uniform(10.0, 100.0)
            cpu_power_cores_val = random.uniform(5.0, 90.0)
            
            # Métrica adicional
            hdd_used_gb = random.uniform(0, disk_total_gb)

            # Diccionario de métricas para un acceso rápido
            metrics = {
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'cpu_percent': f"{cpu_percent_val:.2f}%",
                'cpu_load_percent': f"{cpu_load_percent_val:.2f}%",
                'cpu_freq': f"{cpu_freq_val:.2f} GHz",
                'cpu_clocks': f"{cpu_clocks_val}",
                'ram_percent': f"{ram_percent_val:.2f}%",
                'ram_load_percent': f"{ram_percent_val:.2f}%",
                'ram_used': f"{ram_used_gb:.2f} GB",
                'ram_load_used': f"{ram_used_gb:.2f} GB",
                'ram_total': f"{ram_total_gb:.2f} GB",
                'ram_free': f"{ram_free_gb:.2f} GB",
                'ram_load_free': f"{ram_free_gb:.2f} GB",
                'disco_percent': f"{disk_percent_val:.2f}%",
                'disk_used': f"{disk_used_gb:.2f} GB",
                'disk_total': f"{disk_total_gb:.2f} GB",
                'disk_free': f"{disk_free_gb:.2f} GB",
                'swap_percent': f"{swap_percent_val:.2f}%",
                'swap_usado': f"{swap_usado_gb:.2f} GB",
                'swap_total': f"{swap_total_gb:.2f} GB",
                'red_bytes_sent': f"{red_bytes_sent_val / (1024**2):.2f} MB",
                'red_bytes_recv': f"{red_bytes_recv_val / (1024**2):.2f} MB",
                'cpu_temp_celsius': f"{cpu_temp_celsius_val:.2f} °C",
                'battery_percent': f"{battery_percent_val:.2f}%",
                'cpu_power_package': f"{cpu_power_package_val:.2f} W",
                'cpu_power_cores': f"{cpu_power_cores_val:.2f} W",
                'hdd_used': f"{hdd_used_gb:.2f} GB",
            }
            return metrics
        except Exception as e:
            return {'error': f"Error al generar métricas: {e}"}

    def handle_input(self):
        """
        Maneja la entrada del usuario, busca la métrica solicitada y muestra
        el resultado en el chat.
        """
        user_text = self.user_input.text().strip().lower()
        if not user_text:
            return

        self.append_user_message(user_text)

        # Intentar convertir la entrada del usuario a un índice si es un número
        try:
            num_input = int(user_text)
            if 1 <= num_input <= len(self.metric_names):
                metric_key = self.metric_names[num_input - 1]
            else:
                self.append_bot_message("Número de métrica fuera de rango. Por favor, elige un número del 1 al 26.")
                self.user_input.clear()
                return
        except ValueError:
            # Si no es un número, se normaliza la entrada del usuario para buscarla como nombre
            metric_key = user_text.replace(' ', '_')
        
        metrics = self.get_metrics_data()
        
        if metric_key in metrics:
            formatted_name = self.formatted_metric_names.get(metric_key, metric_key)
            response = f"El valor de '{formatted_name}' es: {metrics[metric_key]}"
            self.append_bot_message(response)
        elif 'error' in metrics:
            self.append_bot_message(f"{metrics['error']}")
        else:
            self.append_bot_message("Métrica no válida. Por favor, escribe el número o nombre exacto de la métrica.")

        self.user_input.clear()
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    chat_app = ChatApp()
    chat_app.show()
    sys.exit(app.exec())
