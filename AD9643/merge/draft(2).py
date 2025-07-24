import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                             QLabel, QComboBox, QLineEdit, QTextEdit)
from Serial_class import SerialAchieve  
import numpy as np
from ad9643 import ad9643  
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QRegExp
import threading
import time
from Udp_class import UdpAchieve
from Serial_server import SerialServer
from Udp_client import Udpclient
class ad9643:
    def __init__(self):
        self.busy_status = 0
        self.connect_status = 0
        self.myserial = SerialAchieve()
        self.myserver = SerialServer()
        self.myudp = UdpAchieve()#新增类，用于udp接收数据
        self.myclient = Udpclient()#新增类，用于udp发送数据
        self.regname = ['SPI', 'CHIPID', 'CHIPGRADE', 'CHANNELINDEX', 'TRANSFER', 'POWERMODES', 'GLOBALCLOCK', 'CLOCKDIVIDE', 'TESTMODE', 'OFFSETADJUST','OUTPUTMODE','OUTPUTADJUST','CLOCKPHASE','DCOOUTPUT','INPUTSPAN','USER1','USER2','USER3','USER4','USER5','USER6','USER7','USER8','SYNC']
        self.regaddr = [0x00,0x01,0x02,0x05,0xFF,0x08,0x09,0x0B,0x0D,0x10,0x14,0x15,0x16,0x17,0x18,0x19,0x1A,0x1B,0x1C,0x1D,0x1E,0x1F,0x20,0x3A]
        self.reg_mode = ['R/W', 'R', 'R', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W']
        self.config_default = [0x18, 0x82, None, 0x03, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,0x05,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
        self.config_current = [0x18, 0x82, None, 0x03, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,0x05,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
        #新增当前值


    def crc(self,command_reg_write:list):
        crc = 0
        for byte in command_reg_write:
            crc ^=byte
        return crc
    

    def hand_shake(self):
        self.busy_status = 1
        command_handshake = [0xAA,0xFE,0x00,0x01,0x00,0x00,0x55]
        command_rev = [0x55,0xFE,0x00,0x15,0x00,0x43,0x4D,0x33,0x34,0x33,0x32,0x5F,0x44,0x45,0x4D,0x4F,0x5f,0x56,0x31,0x31,0xE2]
        self.myserial.ser.write(command_handshake)
        time.sleep(1)#新增，测试用
        rx = []#最好别用readline(),因为设备不一定会发换行符
        for i in range(0,21):
            rx.append(self.myserial.ser.read())

        if rx:
            rx_asc_array = np.frombuffer(np.array(rx), dtype=np.uint8)
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
        
        command_reg_write = [0xAA, 0x1B, 0x00, 0x02,0x00,addr,para]
        command_reg_Write =[0xAA, 0x1B, 0x00, 0x02,0x00,addr,para,self.crc(command_reg_write)]

        command_rev = [0x55, 0x1B,0x00,0x01,0x00,0x00]
        command_Rev = [0x55, 0x1B,0x00,0x01,0x00,0x00,self.crc(command_rev)]

        rx = []
        self.myserial.ser.write(command_reg_Write)
        time.sleep(1)
        for i in range(0, 7):
            rx.append(self.myserial.ser.read())
        if rx:
            rx_asc_array = np.frombuffer(np.array(rx), dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            if rx_asc == command_Rev:
                print('successfully config the device', addr, 'register')
                self.config_current[self.regaddr.index(addr)]=para
            else:
                print('wrong received command')
        else:
            print('data wrong')
        self.busy_status = 0
        return self 


    def ad9643_read_reg(self, addr,timeout=1.0):
        """
        读取ad9643指定寄存器的值
        :param addr: 1字节，寄存器地址
        ：param timeout：超时时间
        :return: 读到的数据值或None
        """
        self.busy_status = 1
        
        while(1):
            rx = self.myserial.ser.read()
            if rx:
                continue
            else:
                break
        data=0#
        command_reg_write = [0xAA, 0x1A,0x00,0x01,0x00,addr]
        command_reg_Write = command_reg_write+[self.crc(command_reg_write)]
        command_rev = [0x55,0x1A,0x00, 0x01,0x00, data]
        command_Rev = [0x55,0x1A,0x00, 0x01,0x00, data,self.crc(command_rev)]#
        print(command_Rev)

        rx = []
        self.myserial.ser.write(command_reg_Write)
        
        time.sleep(1)#新增测试用
        for i in range(0, 7):#
            rx.append(self.myserial.ser.read())
        if rx:
            print(rx)
            rx_asc_array = np.frombuffer(np.array(rx), dtype=np.uint8)
            rx_asc = rx_asc_array.tolist() 
            print(rx_asc)
            if (rx_asc[6] == command_Rev[6]):
                print('The data is', rx_asc[5])
                return rx_asc[5] 
            else:
                print('wrong received command')
                return None
        else:
            print('Wrong')
            return None

        

    def udp_Connect(self, local_ip_str, remote_ip_str):
        def ip_to_bytes(ipstr):
            return [int(x) for x in ipstr.split('.')]
        local_ip = ip_to_bytes(local_ip_str)
        remote_ip = ip_to_bytes(remote_ip_str)

        
        command_local = [0xAA, 0x30, 0x00, 0x04, 0x00] + local_ip
        command_local += [self.crc(command_local)]
        self.myserial.ser.write(bytes(command_local))
        time.sleep(1)#新增，测试用
        rx = self.myserial.ser.read(7)  
        
        local_ok = (rx is not None) and (len(rx) == 7) and (list(rx) == [0x55, 0x30, 0x00, 0x01, 0x00, 0x00, 0x62])

        
        command_remote = [0xAA, 0x31, 0x00, 0x04, 0x00] + remote_ip
        command_remote += [self.crc(command_remote)]
        self.myserial.ser.write(bytes(command_remote))
        time.sleep(1)
        rx2 = self.myserial.ser.read(7)
        
        remote_ok = (rx2 is not None) and (len(rx2) == 7) and (list(rx2) == [0x55, 0x31, 0x00, 0x01, 0x00, 0x00, 0x63])

        return local_ok, rx, remote_ok, rx2

    #原先的sample是usermode
    def usermode(self):
        self.busy_status =1
        command_usermode =[0xAA,0x01,0x02,0x01,0x00,0x00]
        command_userMode =[0xAA,0x01,0x02,0x01,0x00,0x00,self.crc(command_usermode)]
        command_rev=[0x55,0x01,0x02,0x01,0x00,0x00]
        command_Rev=[0x55,0x01,0x02,0x01,0x00,0x00,self.crc(command_rev)]#
        
        self.myserial.ser.write(command_userMode)
        time.sleep(1)#新增，测试用
        rx=[]
        for i in range (0,7):#
            rx.append(self.myserial.ser.read())
        if rx:
            rx_asc_array = np.frombuffer(np.array(rx), dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            if rx_asc == command_Rev:#
                print('Successfully set user mode')
            else:
                print('wrong')
        else:
            print('no data back!')
        self.ad9643_write_reg(self,0x17,0x8E)
        self.ad9643_write_reg(self,0xFF,0x01)
        self.busy_status = 0
        return self
    
    #原先的datacollect拆分成两个部分
    def sample(self):
        self.busy_status = 1
        while self.myserial.ser.in_waiting>0:
            self.myserial.ser.read()
        sample_Length=0x01 #具体采样长度不知道
        command_sample =[0xAA,0x35,0x01,0x04,0x00,sample_Length,0x00,0x00,0x00]
        command_Sample =[0xAA,0x35,0x01,0x04,0x00,sample_Length,0x00,0x00,0x00,self.crc(command_sample)]
        command_rev=[0x55,0x35,0x01,0x01,0x00,0x00]
        command_Rev=[0x55,0x35,0x01,0x01,0x00,0x00,self.crc(command_rev)]

        time.sleep(1)#这个是它要求的
        self.myserial.ser.write(command_Sample)
        time.sleep(1)#脚本测试用
        Rx=[]
        
        for i in range(0,7):
            Rx.append(self.myserial.ser.read())
        if Rx:
            Rx_asc_array = np.frombuffer(np.array(Rx), dtype=np.uint8)
            Rx_asc = Rx_asc_array.tolist()
            print(Rx_asc)
            if Rx_asc == command_Rev:
                print('Successfully sample')
            else:
                print('wrong')
        else:
            print('no data back!')
        self.busy_status = 0
        return self
    #原先的dataCollect拆成两个部分
    def datacollect(self):
        self.busy_status = 1
        while(self.myserial.ser.in_waiting>0):
            self.myserial.ser.read()
        sample_Length=0x01 #具体采样长度不知道
        command_collect=[0xAA,0x35,0x07,0x04,0x00,sample_Length,0x00,0x00,0x00]
        command_Collect=[0xAA,0x35,0x07,0x04,0x00,sample_Length,self.crc(command_collect)]
        command_rev =[0x55,0x35,0x07,0x01,0x00,0x00]
        command_Rev =[0x55,0x35,0x07,0x01,0x00,0x00,self.crc(command_rev)]

        self.myserial.ser.write(command_Collect)
        rx =[]
        time.sleep(1)#脚本测试用
        
        for i in range(0,7):
            rx.append(self.myserial.ser.read())
        if rx:
            rx_asc_array = np.frombuffer(np.array(rx), dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            print(rx_asc)
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
        #接下来就是用upd类通信了
        
    def flash(self):
        for i in range(0,24):
            self.ad9643_write_reg(self.regaddr[i],self.config_default[i])
        
        return self
    


    #新增功能，数据传输
    def udp_data_transmit(self):
        
        self.sample()
        time.sleep(2)
        bool =self.datacollect()
        def udp_run():
            self.myudp.open()
            self.myudp.read()
        def udp_client():
            self.myclient.send()
        thread = threading.Thread(target=udp_run,daemon=True)
        time.sleep(2)
        thread1 = threading.Thread(target=udp_client,daemon=True)
        if bool:
            thread.start()
            thread1.start()

    






class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ad9643 串口控制GUI')
        self.resize(400, 300)
        self.device = ad9643()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

       
        port_layout = QHBoxLayout()
        port_label = QLabel("选择串口：")
        self.combobox = QComboBox()
        self.refresh_ports()
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.combobox)

        
        open_btn = QPushButton("打开串口")
        open_btn.clicked.connect(self.open_serial)
        close_btn = QPushButton("关闭串口")
        close_btn.clicked.connect(self.close_serial)
        port_layout.addWidget(open_btn)
        port_layout.addWidget(close_btn)
        layout.addLayout(port_layout)

        
        input_layout = QHBoxLayout()
        self.addr_edit = QLineEdit()
        self.addr_edit.setPlaceholderText("寄存器地址(16进制,如0A)")
        self.data_edit = QLineEdit()
        self.data_edit.setPlaceholderText("写入数据(16进制,如FF)")
       
        hex_regexp = QRegExp("[0-9A-Fa-f]{1,2}")  
        hex_validator = QRegExpValidator(hex_regexp)
        self.addr_edit.setValidator(hex_validator)
        self.data_edit.setValidator(hex_validator)

        input_layout.addWidget(QLabel("地址:"))
        input_layout.addWidget(self.addr_edit)
        input_layout.addWidget(QLabel("数据:"))
        input_layout.addWidget(self.data_edit)
        layout.addLayout(input_layout)

        
        rw_layout = QHBoxLayout()
        write_btn = QPushButton("写寄存器")
        write_btn.clicked.connect(self.write_reg)
        read_btn = QPushButton("读寄存器")
        read_btn.clicked.connect(self.read_reg)
        rw_layout.addWidget(write_btn)
        rw_layout.addWidget(read_btn)
        layout.addLayout(rw_layout)

        
        handshake_btn = QPushButton("设备握手")
        handshake_btn.clicked.connect(self.handshake)
        layout.addWidget(handshake_btn)

        
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

        
        udp_btn = QPushButton("UDP连接")
        udp_btn.clicked.connect(self.udp_connect)
        layout.addWidget(udp_btn)
        self.udp_status_label = QLabel("UDP未连接")
        layout.addWidget(self.udp_status_label)

        


       
        sample_btn = QPushButton("启动采样")
        sample_btn.clicked.connect(self.sample)
        layout.addWidget(sample_btn)

        
        collect_btn = QPushButton("收集数据")
        collect_btn.clicked.connect(self.data_collect)
        layout.addWidget(collect_btn)

        #数据传输按钮
        transmit_btn =QPushButton("传输数据")
        transmit_btn.clicked.connect(self.data_transmit)
        layout.addWidget(transmit_btn)

        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        self.setLayout(layout)

    def refresh_ports(self):
        self.device.myserial.port_get() 
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
    #加入数据传输
    def data_transmit(self):
        self.device.udp_data_transmit()
        

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


    def sample(self):
        try:
            self.device.sample()
            self.append_text("采样指令已发送。")
        except Exception as e:
            self.append_text(f"采样失败: {e}")

    def data_collect(self):
        try:
            self.device.datacollect()
            self.append_text("数据收集指令已发送。")
        except Exception as e:
            self.append_text(f"数据收集失败: {e}")
    

    
    def append_text(self, msg):
        self.text_edit.append(msg)


#修改后的main函数用于模拟设备

if __name__ == '__main__':
    def crc(command:list):
        crc =0
        for i in range(0,len(command)):
            crc^=command[i]
        return crc
    AD9643 =ad9643()
    AD9643.myserver.port='COM2'
    AD9643.myserver.open_port()
    def server():
        print("Start listening on COM2...")
        while True:
            rx = AD9643.myserver.ser.readline()
            if rx:
                rx_asc_array = np.frombuffer(rx, dtype=np.uint8)
                rx_asc = rx_asc_array.tolist()
                
                print(rx_asc)
                if rx[1]==0x01:
                    AD9643.config_current[AD9643.regaddr.index(rx_asc[5])]==rx_asc[6]
                    command = [0x55,0x01,0x02,0x01,0x00,0x00]
                    crc_value=crc(command)
                    command.append(crc_value)
                    AD9643.myserver.ser.write(command)
                elif rx[1]==0x1A:
                    print(AD9643.config_current[AD9643.regaddr.index(rx_asc[5])])
                    print(AD9643.regaddr.index(rx_asc[5]))
                    print(rx_asc[5])
                    command_rev = [0x55,0x1A,0x00, 0x01,0x00,AD9643.config_current[AD9643.regaddr.index(rx_asc[5])]]
                    crc_value=crc(command_rev)
                    command_rev.append(crc_value)
                    AD9643.myserver.ser.write(command_rev)
                elif rx[1]==0x1B:
                    command_rev = [0x55, 0x1B,0x00,0x01,0x00,0x00]
                    crc_value=crc(command_rev)
                    command_rev.append(crc_value)
                    AD9643.myserver.ser.write(command_rev)
                elif rx[1]==0xFE:
                    command_rev = [0x55,0xFE,0x00,0x15,0x00,0x43,0x4D,0x33,0x34,0x33,0x32,0x5F,0x44,0x45,0x4D,0x4F,0x5f,0x56,0x31,0x31,0xE2]
                    crc_value=crc(command_rev)
                    command_rev.append(crc_value)

                    AD9643.myserver.ser.write(command_rev)
                elif rx[1]==0x30:
                    command_rev = [0x55,0x30,0x00,0x01,0x00,0x00,0x62]
                    crc_value=crc(command_rev)
                    command_rev.append(crc_value)
                    AD9643.myserver.ser.write(command_rev)
                elif rx[1]==0x31:
                    command_rev = [0x55,0x31,0x00,0x01,0x00,0x00,0x63]
                    crc_value=crc(command_rev)
                    command_rev.append(crc_value)
                    AD9643.myserver.ser.write(command_rev)
                elif rx[1]==0x35:
                    if rx[2]==0x01:
                        command_Rev=[0x55,0x35,0x01,0x01,0x00,0x00]
                        crc_value=crc(command_Rev)
                        command_Rev.append(crc_value)
                        AD9643.myserver.ser.write(command_Rev)
                    elif rx[2]==0x07:
                        command_Rev=[0x55,0x35,0x07,0x01,0x00,0x00]
                        crc_value=crc(command_Rev)
                        command_Rev.append(crc_value)
                        AD9643.myserver.ser.write(command_Rev)

    thread = threading.Thread(target=server,daemon=True)
    thread.start()                
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
    