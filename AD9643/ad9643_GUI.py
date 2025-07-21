import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                             QLabel, QComboBox, QLineEdit, QTextEdit)
from Serial_class import SerialAchieve  
import numpy as np
from ad9643 import ad9643  


class ad9643:
    def __init__(self):
        self.busy_status = 0
        self.connect_status = 0
        self.myserial = SerialAchieve()
        #self.regname = ['CONFIG0', 'CONFIG1', 'MUXSCH', 'MUXDIF', 'MUXSG0', 'MUXSG1', 'SYSRED', 'GPIOC', 'GPIOD', 'ID']
        #self.regaddr = [0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09]
        self.reg_mode = ['R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R']
        self.TD = [0,8,16,32,64,128,256,384]
        self.config = [0x0A, 0x83, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0x00, 0x8b]  # ADC 当前寄存器值
        self.config_default = [0x0A, 0x83, 0x00, 0x00, 0xff, 0xff, 0x00, 0xff, 0x00, 0x8b]  # ADC 内部默认寄存器配置
    

    def crc(command_reg_write:list):
        crc = 0

        for byte in command_reg_write:
            crc ^=byte
        return crc
    def crc2(command_rev:list):
        crc =0
        for i in range(0,len(command_rev)-1):
            crc ^=command_rev[i]
        return crc
    

    def hand_shake(self):
        self.busy_status = 1
        command_handshake = [0xAA,0xFE,0x00,0x01,0x00,0x00,0x55]
        command_rev = [0x55,0xFE,0x00,0x15,0x00,0x43,0x4D,0x33,0x34,0x33,0x32,0x5F,0x44,0x45,0x4D,0x4F,0x5f,0x56,0x31,0x31,0xE2]
        self.myserial.ser.write(command_handshake)
        rx = self.myserial.ser.readline()

  
        if rx:
            rx_asc_array = np.frombuffer(rx, dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            if rx_asc == command_rev:
                print('success hand shake, device connected!')
            else:
                print('wrong received command')
        else:
            print('no data back!')
        self.connect_status = 1
        self.busy_status = 0
        return self
    

    def ad9643_write_reg(self, addr, para):
        """
        向ad9643指定寄存器地址写入数据
        :param addr: 1字节，寄存器地址
        :param value: 1字节，要写入的数据
        """
        self.config[addr] = para
        length = len(addr)+len(para)
        length_bytes = length.to_bytes(2,byteorder='big')
        command_reg_write = [0xAA, 0x1B, 0x00, 0x02,0x00,addr,para]
        command_reg_Write =[0xAA, 0x1B, 0x00, 0x02,0x00,addr,para,self.crc(command_reg_write)]

        command_rev = [0x55, 0x1B,0x00,0x01,0x00,0x00]
        command_Rev = [0x55, 0x1B,0x00,0x01,0x00,0x00,self.crc2(command_rev)]

        rx = []
        self.myserial.ser.write(command_reg_Write)
        for i in range(0, 7):
            rx.append(self.myserial.ser.read())
        if rx[6]==command_Rev[6]:
            rx_asc_array = np.frombuffer(np.array(rx), dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            if rx_asc == command_rev:
                print('successfully config the device', addr, 'register')
            else:
                print('wrong received command')
        else:
            print('data wrong')
        self.busy_status = 0
        return self 


    def ad9643_read_reg(self, addr):
        """
        读取ad9643指定寄存器的值
        :param addr: 1字节，寄存器地址
        :return: 读到的数据值
        """
        self.busy_status = 1
        while(1):
            rx = self.myserial.ser.read()
            if rx:
                continue
            else:
                break
        data =0
        command_reg_write = [0xAA, 0x1A,0x00,0x01,0x00,addr]
        command_reg_Write = [0xAA, 0x1A,0x00,0x01,0x00,addr,self.crc(command_reg_write)]
        command_rev = [0x55,0x1A,0x00, 0x01,0x00, data]

        rx = []
        self.myserial.ser.write(command_reg_Write)
        for i in range(0, 7):
            rx.append(self.myserial.ser.read())
        if rx:
            rx_asc_array = np.frombuffer(np.array(rx), dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            if (rx_asc[0] == command_rev[0])and(rx_asc[1] == command_rev[1])and(rx_asc[2] == command_rev[2])and(rx_asc[3] == command_rev[3])and(rx_asc[4] == command_rev[4]):
                print('The data is', rx_asc[5])
            else:
                print('wrong received command')
        else:
            print('Wrong')
        self.busy_status = 0
        return self
    

    def udp_Connect(self):
        self.busy_status = 1
        command_handshake = [0xAA,0x30,0x00,0x04,0x00,0x0A,0x20,0x1E,0x32,0x00]
        command_rev = [0x55,0x30,0x00,0x01,0x00,0x00,0x62]
        self.myserial.ser.write(command_handshake)
        rx = self.myserial.ser.readline()
        if rx:
            rx_asc_array = np.frombuffer(rx, dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            if rx_asc == command_rev:
                print('Successfully configure local address')
            else:
                print('wrong received command')
        else:
            print('no data back!')
        command_handshake1 = [0xAA,0x31,0x00,0x04,0x00,0x0A,0x20,0x1E,0x33,0x00]
        command_rev1 = [0x55,0x31,0x00,0x01,0x00,0x00,0x63]
        self.myserial.ser.write(command_handshake1)
        rx = self.myserial.ser.readline()
        if rx:
            rx_asc_array = np.frombuffer(rx, dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            if rx_asc == command_rev1:
                print('Successfully configure pc address')
            else:
                print('wrong received command')
        else:
            print('no data back!')
        self.connect_status = 1
        self.busy_status = 0
        return self



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ad9643 串口控制GUI')
        self.resize(400, 300)
        self.device = ad9643()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 串口选择
        port_layout = QHBoxLayout()
        port_label = QLabel("选择串口：")
        self.combobox = QComboBox()
        self.refresh_ports()
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.combobox)

        # 打开/关闭按钮
        open_btn = QPushButton("打开串口")
        open_btn.clicked.connect(self.open_serial)
        close_btn = QPushButton("关闭串口")
        close_btn.clicked.connect(self.close_serial)
        port_layout.addWidget(open_btn)
        port_layout.addWidget(close_btn)
        layout.addLayout(port_layout)

        # 地址输入、数据输入
        input_layout = QHBoxLayout()
        self.addr_edit = QLineEdit()
        self.addr_edit.setPlaceholderText("寄存器地址(16进制,如0A)")
        self.data_edit = QLineEdit()
        self.data_edit.setPlaceholderText("写入数据(16进制,如FF)")
        input_layout.addWidget(self.addr_edit)
        input_layout.addWidget(self.data_edit)
        layout.addLayout(input_layout)

        # 读写按钮
        rw_layout = QHBoxLayout()
        write_btn = QPushButton("写寄存器")
        write_btn.clicked.connect(self.write_reg)
        read_btn = QPushButton("读寄存器")
        read_btn.clicked.connect(self.read_reg)
        rw_layout.addWidget(write_btn)
        rw_layout.addWidget(read_btn)
        layout.addLayout(rw_layout)

        # 握手按钮
        handshake_btn = QPushButton("设备握手")
        handshake_btn.clicked.connect(self.handshake)
        layout.addWidget(handshake_btn)

        # 信息显示
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        self.setLayout(layout)

    def refresh_ports(self):
        self.device.myserial.port_get()  # 获取串口列表
        self.combobox.clear()
        for port_info in self.device.myserial.port_list:
            self.combobox.addItem(port_info.device)

    def open_serial(self):
        port = self.combobox.currentText()
        self.device.myserial.port = port
        self.device.myserial.open_port()
        self.append_text(f"已打开串口：{port}")

    def close_serial(self):
        self.device.myserial.close_port()
        self.append_text("串口已关闭。")

    def write_reg(self):
        addr_str = self.addr_edit.text()
        value_str = self.data_edit.text()
        try:
            addr = int(addr_str, 16)
            value = int(value_str, 16)
            self.device.ad9643_write_reg(addr, value)
            self.append_text(f"写寄存器0x{addr:02X}，值0x{value:02X}")
        except Exception as e:
            self.append_text(f"写寄存器失败: {e}")

    def read_reg(self):
        addr_str = self.addr_edit.text()
        try:
            addr = int(addr_str, 16)
            val = self.device.ad9643_read_reg(addr)
            if val is not None:
                self.append_text(f"读取寄存器0x{addr:02X}，值=0x{val:02X}")
            else:
                self.append_text(f"读取寄存器0x{addr:02X}失败！")
        except Exception as e:
            self.append_text(f"读取寄存器失败: {e}")
    
    def handshake(self):
        self.device.hand_shake()
        self.append_text("已发送握手命令。")
    
    def append_text(self, msg):
        self.text_edit.append(msg)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
