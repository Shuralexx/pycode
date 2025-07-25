from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QTextEdit, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(900, 600)
        tab_widget = QTabWidget()
        self.setCentralWidget(tab_widget)

        # Tab 1: 寄存器
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        tab1_layout.addWidget(QLabel("寄存器操作区"))
        tab_widget.addTab(tab1, "寄存器操作")

        # Tab 2: UDP
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        tab2_layout.addWidget(QLabel("UDP配置区"))
        tab_widget.addTab(tab2, "UDP与采集")

        # Tab 3: 日志
        tab3 = QWidget()
        tab3_layout = QVBoxLayout(tab3)
        tab3_layout.addWidget(QTextEdit("日志输出..."))
        tab_widget.addTab(tab3, "日志")

app = QApplication([])
win = MainWindow()
win.show()
app.exec_()
