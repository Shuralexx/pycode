import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                             QLabel, QComboBox, QLineEdit, QTextEdit)
from Serial_class import SerialAchieve  
import numpy as np
from ad9643 import ad9643  
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QRegExp
import time
import threading
from Udp_class import UdpAchieve

class ad9643:
    def __init__(self):
        self.busy_status = 0
        self.connect_status = 0
        self.myserial = SerialAchieve()
        self.myudp = UdpAchieve()
        self.regname = ['SPI', 'CHIPID', 'CHIPGRADE', 'CHANNELINDEX', 'TRANSFER', 'POWERMODES', 'GLOBALCLOCK', 'CLOCKDIVIDE', 'TESTMODE', 'OFFSETADJUST','OUTPUTMODE','OUTPUTADJUST','CLOCKPHASE','DCOOUTPUT','INPUTSPAN','USER1','USER2','USER3','USER4','USER5','USER6','USER7','USER8','SYNC']
        self.regaddr = [0x00,0x01,0x02,0x05,0xFF,0x08,0x09,0x0B,0x0D,0x10,0x14,0x15,0x16,0x17,0x18,0x19,0x1A,0x1B,0x1C,0x1D,0x1E,0x1F,0x20,0x3A]
        self.reg_mode = ['R/W', 'R', 'R', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W']
        # ADC 默认寄存器配置
        self.config_default = [0x18, 0x82, None, 0x03, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,0x05,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
        self.config_current = [0x18, 0x82, None, 0x03, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,0x05,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]

    def crc(self, data):
        crc = 0
        for byte in data:
            crc ^= int(byte)
        return crc

    def auto_open_serial_and_handshake(self):
        """
        自动遍历所有可用串口，尝试握手，直到找到目标板卡并打开
        返回：成功的串口号或None
        """
        from serial.tools import list_ports

        for port_info in list_ports.comports():
            port = port_info.device
            try:
                # 关闭之前的连接
                if self.myserial.ser and self.myserial.ser.is_open:
                    self.myserial.ser.close()
                self.myserial.port = port
                self.myserial.open_port()
                time.sleep(0.2)  # 确保串口稳定
                print(f"尝试串口: {port}")
                self.hand_shake()
                # 判断是否握手成功（你有connect_status变量）
                if self.connect_status == 1:
                    print(f"成功打开并握手的串口：{port}")
                    return port
            except Exception as e:
                print(f"串口{port}打开或握手失败: {e}")
        return None


    def hand_shake(self):
        self.busy_status = 1
        while self.myserial.ser.in_waiting > 0:
            self.myserial.ser.read()
        command_handshake = [0xAA,0xFE,0x00,0x01,0x00,0x00,0x55]
        command_rev = [0x55,0xFE,0x00,0x15,0x00,0x43,0x4D,0x33,0x34,0x33,0x32,0x5F,0x44,0x45,0x4D,0x4F,0x5F,0x56,0x30,0x31,0xE2]
        self.myserial.ser.write(command_handshake)
        rx=[]
        for i in range(0, 21):
            rx.append(self.myserial.ser.read())
        if rx:
            rx_asc_array = np.frombuffer(np.array(rx), dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            if rx_asc == command_rev:
                print('success hand shake, device connected!')
            else:
                print(rx_asc)
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
        #self.config[addr] = para
        #length = len(addr)+len(para) addr和para都是int，没有len()
        self.busy_status = 1
        while self.myserial.ser.in_waiting > 0:
            self.myserial.ser.read()

        self.config_current[self.regaddr.index(addr)]=para
        command_reg_write = [0xAA, 0x1B, 0x00, 0x02,0x00,addr,para]
        command_reg_Write =[0xAA, 0x1B, 0x00, 0x02,0x00,addr,para,self.crc(command_reg_write)]

        command_rev = [0x55, 0x1B,0x00,0x07,0x00,0x00]
        command_Rev = command_rev + [self.crc(command_rev)]

        self.myserial.ser.write(bytes(command_reg_Write))
        rx = self.myserial.ser.read(7)
        if rx and len(rx) == 7:
            rx_list = list(rx)
            print(f"写寄存器期望回包: {command_Rev}")
            print(f"实际收到回包: {rx_list}")
            if rx_list == command_Rev:
                print(f"寄存器0x{addr:02X}写入值0x{para:02X}成功")
                print('successfully config the device', addr, 'register')
            else:
                print('wrong received command')
        else:
            print('data wrong')
        self.busy_status = 0
        return self


    def ad9643_read_reg(self, addr, timeout=1.0):
        """
        读取ad9643指定寄存器的值
        :param addr: 1字节，寄存器地址
        ：param timeout：超时时间
        :return: 读到的数据值或None
        """
        self.busy_status = 1
        #清空串口接收缓存区（读到为空为止，确保不会读到历史脏数据）
        while(1):
            rx = self.myserial.ser.read()
            if rx:
                continue
            else:
                break
        data =self.config_current[self.regaddr.index(addr)]
        print(data)
        command_reg_write = [0xAA, 0x1A,0x00,0x01,0x00,addr]
        command_reg_Write = command_reg_write+[self.crc(command_reg_write)]
        command_rev = [0x55,0x1A,0x00, 0x07,0x00, data]
        command_Rev = command_rev+[self.crc(command_rev)]

        rx = []
        self.myserial.ser.write(command_reg_Write)
        #循环7次，从串口读取7个字节作为应答帧。
        for i in range(0, 7):
            rx.append(self.myserial.ser.read())
        if rx:
            rx_asc_array = np.frombuffer(np.array(rx), dtype=np.uint8)
            rx_asc = rx_asc_array.tolist() #转成int数组
            print(rx_asc)
            if (rx_asc[0] == command_Rev[0])and(rx_asc[1] == command_rev[1])and(rx_asc[2] == command_rev[2])and(rx_asc[3] == command_rev[3])and(rx_asc[4] == command_rev[4]):
                print('The data is', rx_asc[5])
                self.busy_status = 0
                return rx_asc[5] #打印读到的字节
            else:
                print(f"期望回包: {command_Rev}")
                print(f"实际回包: {rx_asc}")
                print('wrong received command')
                self.busy_status = 0
                return None
        else:
            print('Wrong')
            self.busy_status = 0
            return None
        
        

    def udp_Connect(self, local_ip_str, remote_ip_str):
        while self.myserial.ser.in_waiting > 0:
            self.myserial.ser.read()
        def ip_to_bytes(ipstr):
            return [int(x) for x in ipstr.split('.')]

        def send_and_check(cmd, ip_bytes, tag=""):
            # 组包并发送
            command = [0xAA, cmd, 0x00, 0x04, 0x00] + ip_bytes
            crc = self.crc(command)
            command.append(crc)
            self.myserial.ser.write(bytes(command))
            rx = self.myserial.ser.read(7)
            ok = False
            if rx is not None and len(rx) == 7:
                rx_prefix = [int(x) for x in rx[:6]]
                rx_crc = int(rx[6])
                expect_crc = self.crc(rx_prefix)
                print(f"{tag}回包前缀: {rx_prefix}, 回包CRC: {rx_crc}, 计算CRC: {expect_crc}")
                ok = (rx_crc == expect_crc)
            else:
                print(f"{tag}未收到回包或长度异常, rx={rx}")
            return ok, rx

        # 本地IP配置
        local_ip = ip_to_bytes(local_ip_str)
        local_ok, rx = send_and_check(0x30, local_ip, "本地IP")
        while self.myserial.ser.in_waiting > 0:
            self.myserial.ser.read()

        # 远端IP配置
        remote_ip = ip_to_bytes(remote_ip_str)
        remote_ok, rx2 = send_and_check(0x31, remote_ip, "远端IP")

        return local_ok, rx, remote_ok, rx2



    def usermode(self):
        self.busy_status =1
        while self.myserial.ser.in_waiting > 0:
            self.myserial.ser.read()
        command_usermode =[0xAA,0x01,0x02,0x01,0x00,0x00]
        command_userMode =[0xAA,0x01,0x02,0x01,0x00,0x00,self.crc(command_usermode)]
        command_rev = [0x55,0x01,0x02,0x07,0x00,0x00]
        command_Rev = [0x55,0x01,0x02,0x07,0x00,0x00,self.crc(command_rev)]
        self.myserial.ser.write(command_userMode)
        time.sleep(1)
        rx=[]
        for i in range (0,7):
            rx.append(self.myserial.ser.read())
        if rx:
            rx_asc_array = np.frombuffer(np.array(rx), dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            print(f"实际回包: {rx_asc}")
            print(f"期望回包: {command_Rev}")
            if rx_asc == command_Rev:
                print('成功重上电')
                print("准备写0x17, 0x8E")
                self.ad9643_write_reg(0x17,0x8E)
                print("准备写0xFF, 0x01")
                self.ad9643_write_reg(0xFF,0x01)
                print("usermode finish")
            else:
                print('wrong')
        else:
            print('no data back!')

        self.busy_status = 0
        return self
    

    def sample(self):
        self.busy_status = 1
        while self.myserial.ser.in_waiting>0:
            self.myserial.ser.read()
        command_sample =[0xAA,0x35,0x01,0x04,0x00,0x00,0x00,0x80,0x00]
        command_Sample =[0xAA,0x35,0x01,0x04,0x00,0x00,0x00,0x80,0x00,self.crc(command_sample)]
        command_rev=[0x55,0x35,0x01,0x07,0x00,0x00]
        command_Rev=command_rev + [self.crc(command_rev)]
        time.sleep(1)
        self.myserial.ser.write(command_Sample)
        Rx=[]
        for i in range(0,7):
            Rx.append(self.myserial.ser.read())
        if Rx:
            Rx_asc_array = np.frombuffer(np.array(Rx), dtype=np.uint8)
            Rx_asc = Rx_asc_array.tolist()
            if Rx_asc == command_Rev:
                print('Successfully sample')
            else:
                print('wrong')
        else:
            print('no data back!')
        self.busy_status = 0
        return self
    

    def datacollect(self):
        self.busy_status = 1
        while self.myserial.ser.in_waiting>0:
            self.myserial.ser.read()
        command_collect=[0xAA,0x35,0x07,0x04,0x00,0x00,0x00,0x80,0x00]
        command_Collect=command_collect + [self.crc(command_collect)]
        command_rev =[0x55,0x35,0x07,0x07,0x00,0x00]
        command_Rev =[0x55,0x35,0x07,0x07,0x00,0x00,self.crc(command_rev)]

        self.myserial.ser.write(command_Collect)
        rx=[]
        for i in range(0,7):
            rx.append(self.myserial.ser.read())
        if rx:
            rx_asc_array = np.frombuffer(np.array(rx), dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            if rx_asc == command_Rev:
                print('Successfully transmit')
                self.busy_status = 0
                return True
            else:
                print('wrong')
                self.busy_status = 0
                return False
        else:
            print('no data back!')
            self.busy_status = 0
            return False


    def flash(self):
        for i in range(0,24):
            self.ad9643_write_reg(self.regaddr[i],self.config_default[i])
        
        return self
    #刷新每个寄存器的默认值

    def udp_data_transmit(self):
        
        self.sample()
        self.datacollect()
        def udp_run():
            self.myudp.open()
            self.myudp.read()
        thread = threading.Thread(target=udp_run,daemon=True)
        thread.start()

    def reset_fpga(self):
        # 组包 [0xAA, 0x32, 0x00, 0x01, 0x00, 0x00, CRC]
        command = [0xAA, 0x32, 0x00, 0x01, 0x00, 0x00]
        crc = self.crc(command)
        command.append(crc)
        self.myserial.ser.write(bytes(command))
        rx = self.myserial.ser.read(7)
        ok = False
        if rx is not None and len(rx) == 7:
            rx_prefix = [int(x) for x in rx[:6]]
            rx_crc = int(rx[6])
            expect_crc = self.crc(rx_prefix)
            print(f"FPGA复位回包前缀: {rx_prefix}, 回包CRC: {rx_crc}, 计算CRC: {expect_crc}")
            ok = (rx_crc == expect_crc) and (rx_prefix[-1] == 0x00)
        else:
            print(f"FPGA复位未收到回包或长度异常, rx={rx}")
        return ok, rx




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
        #input_layout.addWidget(self.addr_edit)
        #input_layout.addWidget(self.data_edit)
        #layout.addLayout(input_layout)

        # 设置 QValidator，只允许输入0-9、A-F、a-f
        hex_regexp = QRegExp("[0-9A-Fa-f]{1,2}")  # 最多输入2位
        hex_validator = QRegExpValidator(hex_regexp)
        self.addr_edit.setValidator(hex_validator)
        self.data_edit.setValidator(hex_validator)

        input_layout.addWidget(QLabel("地址:"))
        input_layout.addWidget(self.addr_edit)
        input_layout.addWidget(QLabel("数据:"))
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

        # FPGA复位按钮
        reset_btn = QPushButton("FPGA复位")
        reset_btn.clicked.connect(self.reset_fpga)
        layout.addWidget(reset_btn)

        # 自动检测按钮
        auto_btn = QPushButton("自动识别串口并握手")
        auto_btn.clicked.connect(self.auto_find_and_open_serial)
        layout.addWidget(auto_btn)

        '''
        # 握手按钮
        handshake_btn = QPushButton("设备握手")
        handshake_btn.clicked.connect(self.handshake)
        layout.addWidget(handshake_btn)
        '''

        # IP配置区
        ip_layout = QHBoxLayout()
        self.local_ip_edit = QLineEdit()
        self.local_ip_edit.setPlaceholderText("本地IP(如10.32.30.50)")
        self.remote_ip_edit = QLineEdit()
        self.remote_ip_edit.setPlaceholderText("远端IP(如10.32.30.51)")
        ip_layout.addWidget(QLabel("本地IP:"))
        ip_layout.addWidget(self.local_ip_edit)
        ip_layout.addWidget(QLabel("远端IP:"))
        ip_layout.addWidget(self.remote_ip_edit)
        layout.addLayout(ip_layout)

        # UDP连接按钮
        udp_btn = QPushButton("UDP连接")
        udp_btn.clicked.connect(self.udp_connect)
        layout.addWidget(udp_btn)
        self.udp_status_label = QLabel("UDP未连接")
        layout.addWidget(self.udp_status_label)

        # 用户模式按钮
        sample_btn = QPushButton("启动用户模式")
        sample_btn.clicked.connect(self.usermode)
        layout.addWidget(sample_btn)

        # 数据采集按钮
        collect_btn = QPushButton("数据采集")
        collect_btn.clicked.connect(self.udp_transmit)
        layout.addWidget(collect_btn)

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
        """
        for i in range(len(self.device.regaddr)):
            if self.device.config_default[i] is not None:
                self.device.ad9643_write_reg(self.device.regaddr[i], self.device.config_default[i])
        self.append_text("寄存器初始化完成。")
        """
    def close_serial(self):
        self.device.myserial.close_port()
        self.append_text("串口已关闭。")

    def write_reg(self):
        addr_str = self.addr_edit.text().strip()
        value_str = self.data_edit.text().strip()
        if not addr_str or not value_str:
            self.append_text("请先填写完整的寄存器地址和数据！")
            return
        try:
            addr = int(addr_str, 16)
            value = int(value_str, 16)
            self.device.ad9643_write_reg(addr, value)
            self.append_text(f"写寄存器0x{addr:02X}，值0x{value:02X}")
        except Exception as e:
            self.append_text(f"写寄存器失败: {e}")

    def read_reg(self):
        addr_str = self.addr_edit.text()
        addr_str = self.addr_edit.text().strip()
        if not addr_str :
            self.append_text("请先填写寄存器地址！")
            return
        try:
            addr = int(addr_str, 16)
            val = self.device.ad9643_read_reg(addr)
            if val is not None:
                self.append_text(f"读取寄存器0x{addr:02X}，值=0x{val:02X}")
            else:
                self.append_text(f"读取寄存器0x{addr:02X}失败！")
        except Exception as e:
            self.append_text(f"读取寄存器失败: {e}")
    
    def auto_find_and_open_serial(self):
        port = self.device.auto_open_serial_and_handshake()
        if port:
            self.append_text(f"自动识别并握手成功，串口为：{port}")
            # 选中combobox对应项
            index = self.combobox.findText(port)
            if index != -1:
                self.combobox.setCurrentIndex(index)
        else:
            self.append_text("自动识别失败，未找到可用的串口设备")

    def handshake(self):
        self.device.hand_shake()
        self.append_text("已发送握手命令。")

    def udp_connect(self):
        local_ip = self.local_ip_edit.text().strip()
        remote_ip = self.remote_ip_edit.text().strip()
        if not local_ip or not remote_ip:
            self.append_text("请填写本地和远端IP！")
            self.udp_status_label.setText("UDP未连接")
            return
        try:
            local_ok, rx, remote_ok, rx2 = self.device.udp_Connect(local_ip, remote_ip)
            self.append_text(f"本地IP配置回包: {list(rx) if rx else rx}")
            self.append_text(f"远端IP配置回包: {list(rx2) if rx2 else rx2}")
            if local_ok and remote_ok:
                self.udp_status_label.setText("UDP连接成功")
                self.append_text("UDP连接成功！")
            else:
                self.udp_status_label.setText("UDP连接失败")
                self.append_text("UDP连接失败，请检查回包内容或硬件连线。")
        except Exception as e:
            self.udp_status_label.setText("UDP连接失败")
            self.append_text(f"UDP配置失败: {e}")

    def usermode(self):
        try:
            self.device.usermode()
            self.append_text("用户模式指令已发送。")
        except Exception as e:
            self.append_text(f"用户模式失败: {e}")

    def udp_transmit(self):
        try:
            self.device.udp_data_transmit()
            self.append_text("数据采集指令已发送。")
        except Exception as e:
            self.append_text(f"数据采集失败: {e}")

    def reset_fpga(self):
        try:
            ok, rx = self.device.reset_fpga()
            if ok:
                self.append_text("FPGA复位成功！")
            else:
                self.append_text(f"FPGA复位失败，回包: {list(rx) if rx else rx}")
        except Exception as e:
            self.append_text(f"FPGA复位异常: {e}")



    def append_text(self, msg):
        self.text_edit.append(msg)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())