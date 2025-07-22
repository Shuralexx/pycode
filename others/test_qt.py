import sys
import random
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QApplication
from PyQt5.QtGui import QFont
class MyWidget(QWidget):
    def close_window(self):
        self.close()
    def __init__(self):
        super().__init__()

        self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo", "Привет мир","你好世界", "こんにちは世界", "안녕하세요 세계", "Ciao mondo"]
        self.text =QLabel("Hello World")
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 文本居中显示
        self.text.setMinimumHeight(100)  # 增大文本高度

        self.button = QPushButton("Click me!")
        self.button.setMinimumHeight(40)  # 增大按钮高度
        self.button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.text.setStyleSheet("border: 2px solid #ccc; border-radius: 5px; padding: 10px;")  # 添加边框和内边距

 # 新增关闭按钮
        self.close_button = QPushButton("Close Window")
        self.close_button.setMinimumHeight(40)
        self.close_button.setStyleSheet("background-color: #f44336; color: white;")
        self.close_button.clicked.connect(self.close_window)  # 连接到窗口的close方法

        self.v_layout = QVBoxLayout(self)
        self.v_layout.addWidget(self.text)
        self.v_layout.addWidget(self.button)
        self.v_layout.addWidget(self.close_button)  # 添加关闭按钮到布局
        self.v_layout.setSpacing(20)

        self.button.clicked.connect(self.magic)
        self.setWindowTitle("Multi-language Greeting")  # 设置窗口标题

    @pyqtSlot()  # 装饰器从@Slot()改为@pyqtSlot()
    def magic(self):
        self.text.setText(random.choice(self.hello))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MyWidget()
    widget.resize(400,300)
    widget.show()
    sys.exit(app.exec())