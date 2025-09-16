import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                             QWidget, QTextEdit, QLineEdit)

class ChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador de Chat")
        self.setGeometry(100, 100, 400, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Escribe un mensaje para comenzar...")
        self.user_input.returnPressed.connect(self.handle_input)
        layout.addWidget(self.user_input)

        # Estado inicial
        self.current_state = "initial"
        self.chat_history.append("Bot: Estoy a la espera de tu primer mensaje.")

    def show_welcome_message(self):
        self.chat_history.append("Bot: ¡Hola! Soy un bot de monitoreo. ¿Qué porcentaje de uso deseas conocer?")
        self.show_options()

    def show_options(self):
        self.chat_history.append("\nBot: Por favor, elige una de las siguientes opciones:")
        self.chat_history.append("1. CPU")
        self.chat_history.append("2. RAM")
        self.chat_history.append("3. Disco")
        self.user_input.clear()
        self.current_state = "options"

    def handle_input(self):
        user_text = self.user_input.text().strip().lower()
        if not user_text:
            return

        self.chat_history.append(f"Tú: {user_text}")
        
        # 🧠 Nueva lógica del flujo
        if self.current_state == "initial":
            self.show_welcome_message()
            return
        
        # Lógica de respuesta basada en la entrada del usuario
        response = ""
        if user_text in ["1", "cpu"]:
            response = "Bot: El uso de la CPU es del 75%."
        elif user_text in ["2", "ram"]:
            response = "Bot: El uso de la RAM es del 85%."
        elif user_text in ["3", "disco"]:
            response = "Bot: El uso del Disco es del 40%."
        else:
            response = "Bot: Opción no válida. Por favor, elige 1, 2 o 3."

        self.chat_history.append(response)
        self.show_options()
        self.user_input.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    chat_app = ChatApp()
    chat_app.show()
    sys.exit(app.exec())