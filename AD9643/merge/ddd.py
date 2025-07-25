import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
                            QGroupBox, QPushButton, QComboBox, QLabel, QLineEdit, QTextEdit, QProgressBar
                            , QTableWidget, QTableWidgetItem, QAbstractItemView,QMessageBox,QSizePolicy,QTabWidget)
 #把Qtabwidget加到上面
from Serial_class import SerialAchieve  
import numpy as np
from ad9643 import ad9643  
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import Qt
import time
import threading
from Udp_class import UdpAchieve
import pyqtgraph as pg
class ad9643:
    def __init__(self):
        self.busy_status = 0
        self.connect_status = 0
        self.myserial = SerialAchieve()
        self.myudp = UdpAchieve()
        self.regname = ['SPI', 'CHIPID', 'CHIPGRADE', 'CHANNELINDEX', 'TRANSFER', 'POWERMODES', 'GLOBALCLOCK', 'CLOCKDIVIDE', 'TESTMODE', 'OFFSETADJUST','OUTPUTMODE','OUTPUTADJUST','CLOCKPHASE','DCOOUTPUT','INPUTSPAN','USER1','USER2','USER3','USER4','USER5','USER6','USER7','USER8','SYNC']
        self.regaddr =        [0x00, 0x01, 0x02, 0x05, 0xFF, 0x08, 0x09, 0x0B, 0x0D, 0x10, 0x14,0x15,0x16,0x17,0x18,0x19,0x1A,0x1B,0x1C,0x1D,0x1E,0x1F,0x20,0x3A]
        self.reg_mode = ['R/W', 'R', 'R', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W']
        # ADC 默认寄存器配置
        self.config_default = [0x18, 0x82, None, 0x03, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x05,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
        self.config_current = [0x18, 0x82, None, 0x03, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x05,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]

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




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ad9643 控制系统')
        self.resize(900, 550)
        self.device = ad9643()
        self.setup_ui()

    def setup_ui(self):
        # -------- 主部件/主布局 --------
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QGridLayout()
        main_widget.setLayout(main_layout)

        # -------- 1. 顶部串口区 --------
        serial_group = QGroupBox("串口控制")
        serial_layout = QHBoxLayout()
        serial_group.setLayout(serial_layout)
        self.combobox = QComboBox()
        self.refresh_btn = QPushButton("刷新串口")
        self.refresh_btn.clicked.connect(self.refresh_ports) 
        self.open_btn = QPushButton("打开串口")
        self.open_btn.clicked.connect(self.open_serial)
        self.close_btn = QPushButton("关闭串口")
        self.close_btn.clicked.connect(self.close_serial)
        #self.status_label = QLabel("串口未连接")
        self.progress_bar = QProgressBar()
        serial_layout.addWidget(QLabel("串口选择:"))
        serial_layout.addWidget(self.combobox)
        serial_layout.addWidget(self.refresh_btn)
        serial_layout.addWidget(self.open_btn)
        serial_layout.addWidget(self.close_btn)
        #serial_layout.addWidget(self.status_label)
        serial_layout.addWidget(self.progress_bar)
        main_layout.addWidget(serial_group, 0, 0, 1, 4)

        # -------- 2. 左侧设备操作/功能控制 --------
        ctrl_group = QGroupBox("设备操作")
        ctrl_layout = QVBoxLayout()
        ctrl_group.setLayout(ctrl_layout)
        self.handshake_btn = QPushButton("握手")
        self.handshake_btn.clicked.connect(self.handshake)
        self.reset_btn = QPushButton("FPGA复位")
        self.reset_btn.clicked.connect(self.reset_fpga)
        self.auto_btn = QPushButton("自动识别串口并握手")
        self.auto_btn.clicked.connect(self.auto_find_and_open_serial)
        self.usermode_btn = QPushButton("启动用户模式")
        self.usermode_btn.clicked.connect(self.usermode)
        ctrl_layout.addWidget(self.handshake_btn)
        ctrl_layout.addWidget(self.reset_btn)
        ctrl_layout.addWidget(self.auto_btn)
        ctrl_layout.addWidget(self.usermode_btn)
        main_layout.addWidget(ctrl_group, 1, 0, 2, 1)#放在第1行第0列（row=1, column=0），占2行1列

        # -------- 3. 中央寄存器读写与UDP配置 --------
        op_group = QGroupBox("寄存器/UDP配置")
        op_layout = QVBoxLayout()
        op_group.setLayout(op_layout)
        op_group.setFixedWidth(500)

        # 3.1 地址/数据输入区
        reg_layout = QHBoxLayout()
        self.addr_edit = QLineEdit()
        self.addr_edit.setPlaceholderText("地址(16进制)")
        self.data_edit = QLineEdit()
        self.data_edit.setPlaceholderText("数据(16进制)")
        reg_layout.addWidget(QLabel("寄存器地址:"))
        reg_layout.addWidget(self.addr_edit)
        reg_layout.addWidget(QLabel("写入数据:"))
        reg_layout.addWidget(self.data_edit)
        op_layout.addLayout(reg_layout)
        # 3.2 读写按钮
        rw_layout = QHBoxLayout()
        self.write_btn = QPushButton("写寄存器")
        self.write_btn.clicked.connect(self.write_reg)
        self.read_btn = QPushButton("读寄存器")
        self.read_btn.clicked.connect(self.read_reg)
        rw_layout.addWidget(self.write_btn)
        rw_layout.addWidget(self.read_btn)
        op_layout.addLayout(rw_layout)
        # 3.3 UDP配置
        ip_layout = QHBoxLayout()
        self.local_ip_edit = QLineEdit()
        self.local_ip_edit.setPlaceholderText("本地IP")
        self.remote_ip_edit = QLineEdit()
        self.remote_ip_edit.setPlaceholderText("远端IP")
        ip_layout.addWidget(QLabel("本地IP:"))
        ip_layout.addWidget(self.local_ip_edit)
        ip_layout.addWidget(QLabel("远端IP:"))
        ip_layout.addWidget(self.remote_ip_edit)
        op_layout.addLayout(ip_layout)
        # 3.4 UDP按钮与状态
        self.udp_btn = QPushButton("UDP连接")
        self.udp_btn.clicked.connect(self.udp_connect)
        self.udp_status_label = QLabel("UDP未连接")
        op_layout.addWidget(self.udp_btn)
        op_layout.addWidget(self.udp_status_label)
        # 3.5 采集相关
        self.sample_btn = QPushButton("数据采样")
        self.sample_btn.clicked.connect(self.udp_transmit)
        op_layout.addWidget(self.sample_btn)

        # 3.6 批量写入寄存器按钮
        self.write_all_btn = QPushButton("批量写入全部寄存器")
        self.write_all_btn.clicked.connect(self.write_all_regs)
        op_layout.addWidget(self.write_all_btn)

        # 3.7 刷新寄存器显示按钮
        self.refresh_reg_btn = QPushButton("刷新寄存器显示")
        self.refresh_reg_btn.clicked.connect(self.refresh_reg_table)
        op_layout.addWidget(self.refresh_reg_btn)
        main_layout.addWidget(op_group, 1, 1, 2, 1) #放在第1行第1列（row=1, column=1），占2行1列

        # -------- 4. 信息显示区（QTextEdit） --------
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        main_layout.addWidget(self.text_edit, 3, 0, 1, 4)  # 放在底部横跨全行

        # -------- 5. 寄存器列表区（QTableWidget） --------
        # self.reg_table = QTableWidget()
        # self.reg_table.setColumnCount(5)
        # self.reg_table.setHorizontalHeaderLabels(["寄存器名", "地址", "当前值", "默认值", "R/W"])
        # self.reg_table.setEditTriggers(QAbstractItemView.DoubleClicked)  # 只允许双击编辑
        # self.reg_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # self.reg_table.verticalHeader().setVisible(False)
        # self.reg_table.setMinimumHeight(240)
        # self.reg_table.setMinimumWidth(600)  # 可根据实际需求设定
        # self.reg_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 自动扩展
        # self.refresh_reg_table()  # 初始化表格内容
        # self.reg_table.cellChanged.connect(self.reg_cell_changed)
        # # (row, column, rowSpan, colSpan)
        # main_layout.addWidget(self.reg_table, 1, 2, 3, 2)  #放在第1行第2列（row=1, column=2），占3行2列

        #
        self.graph_diaplay=QTabWidget()
        self.graphTab1=QWidget()
        self.graphTab1_Layout=QGridLayout()
        self.graphTab1.setLayout(self.graphTab1_Layout)
        self.tab1_Label = QLabel('时域图', self)
        self.graphTab1_Layout.addWidget(self.tab1_Label, 1, 1, 1, 6)
        self.tab1_measure_label = QLabel('Measurements')
        self.tab1_measure = QTableWidget()
        self.tab1_measure.setFixedHeight(120)
        self.tab1_measure.setColumnCount(5)
        self.tab1_measure.setRowCount(1)
        self.tab1_measure.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tab1_measure.setHorizontalHeaderLabels(['Channel', 'Min', 'Max', 'Sigma', 'Mean'])
        self.tab1_measure.horizontalHeader().setStyleSheet('QHeaderView::section{background:grey;color:white;font:bold}') #设置表头格式
        self.tab1_measure.setFixedWidth(700)
        # 设置两个checkbox, 选择显示的曲线，设置输出的单位
        self.tab1_plt = pg.PlotWidget()  # 实例化一个绘图部件
        self.tab1_plt.showGrid(x=True, y=False)  # 显示图形网格
        self.tab1_plt.setBackground(background=None)
        self.graphTab1_Layout.addWidget(self.tab1_plt, 2, 1, 1, 6)
        self.graphTab1_Layout.addWidget(self.tab1_measure_label,4,1,1,6)
        self.graphTab1_Layout.addWidget(self.tab1_measure,5,1,1,6)
        
        self.graphTab2=QWidget()
        self.graphTab2_Layout=QGridLayout()
        self.graphTab2.setLayout(self.graphTab2_Layout)
        self.tab2_Label=QLabel('码值直方图',self)
        self.graphTab2_Layout.addWidget(self.tab2_Label, 1, 1, 1, 6)
        self.tab2_plt = pg.PlotWidget()  # 实例化一个绘图部件
        self.tab2_plt.showGrid(x=False, y=True)  # 显示图形网格
        self.tab2_plt.setBackground(background=None)
        self.graphTab2_Layout.addWidget(self.tab2_plt, 2, 1, 1, 6)
        self.tab2_measure_label = QLabel('Measurements')
        self.tab2_measure = QTableWidget()
        self.tab2_measure.setFixedHeight(120)
        self.tab2_measure.setColumnCount(7)
        self.tab2_measure.setRowCount(1)
        self.tab2_measure.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tab2_measure.setHorizontalHeaderLabels(['Channel', 'Min', 'Max', 'Sigma', 'Mean','Peak to Peak','ENOB'])
        self.tab2_measure.horizontalHeader().setStyleSheet('QHeaderView::section{background:grey;color:white;font:bold}') #设置表头格式
        self.tab2_measure.setFixedWidth(700)
        self.graphTab2_Layout.addWidget(self.tab2_measure_label,4,1,1,6)
        self.graphTab2_Layout.addWidget(self.tab2_measure,5,1,1,6)
        self.graphTab3=QWidget()
        self.graphTab3_Layout=QGridLayout()
        self.graphTab3.setLayout(self.graphTab3_Layout)

        self.tab3_Label = QLabel('频谱图', self)
        
        self.tab3_plt = pg.PlotWidget()  # 实例化一个绘图部件
        self.tab3_plt.showGrid(x=False, y=True)  # 显示图形网格
        self.tab3_plt.setBackground(background=None)
         # 设置统计值表格
        self.tab3_measure_label = QLabel('Measurements')
        self.tab3_measure = QTableWidget()
        self.tab3_measure.setFixedHeight(120)
        self.tab3_measure.setColumnCount(6)
        self.tab3_measure.setRowCount(1)
        self.tab3_measure.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tab3_measure.setHorizontalHeaderLabels(['Channel','dBFS', 'SINAD', 'SNR', 'THD', 'SFDR'])
        self.tab3_measure.horizontalHeader().setStyleSheet('QHeaderView::section{background:grey;color:white;font:bold}') #设置表头格式
        self.tab3_measure.setFixedWidth(700)
        self.graphTab3_Layout.addWidget(self.tab3_Label, 1, 1, 1, 6)
        self.graphTab3_Layout.addWidget(self.tab3_plt, 2, 1, 1, 6)
        self.graphTab3_Layout.addWidget(self.tab3_measure_label,4,1,1,6)
        self.graphTab3_Layout.addWidget(self.tab3_measure,5,1,1,6)
        

        #
        self.graphTab4=QWidget()
        self.graphTab4_Layout=QGridLayout()
        self.graphTab4.setLayout(self.graphTab4_Layout)
        self.tab4_Label = QLabel('寄存器列表', self)
        self.tab4_table = QTableWidget()  # 实例化一个表格
        self.tab4_table.setColumnCount(5) # 设置共有5列数据： 寄存器名/寄存器地址/寄存器默认值/寄存器能力/寄存器当前值
        self.tab4_table.setHorizontalHeaderLabels(['Register Name', 'Address', 'Default', 'Mode', 'Value'])
        self.tab4_table.horizontalHeader().setStyleSheet('QHeaderView::section{background:grey;color:white;font:bold}') #设置表头格式
        self.tab4_table.setRowCount(10)
        self.tab4_table.setMinimumWidth(600)
        self.tab4_table.setMinimumHeight(240)
        self.tab4_table.verticalHeader().setVisible(False)
        self.tab4_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.refresh_reg_table()  # 初始化表格内容
        self.tab4_table.cellChanged.connect(self.reg_cell_changed)  # 自动扩展
        self.graphTab4_Layout.addWidget(self.tab4_Label, 1, 1, 1, 6)
        self.graphTab4_Layout.addWidget(self.tab4_table, 2, 1, 6, 6)
        
        self.graph_diaplay.addTab(self.graphTab1,'Time Domain Display')
        self.graph_diaplay.addTab(self.graphTab2,'Sample Histogram Analysis')
        self.graph_diaplay.addTab(self.graphTab3,'Spectral Analysis')
        self.graph_diaplay.addTab(self.graphTab4,'Register Config')
        main_layout.addWidget(self.graph_diaplay,1,2,3,2)

    def write_all_regs(self):
        # 先全部检查一遍，确保每一行都是合法16进制或为空或None
        for i in range(self.tab4_table.rowCount()):
            item = self.tab4_table.item(i, 2)
            if item is None:
                continue
            txt = item.text().replace("0x", "").strip()
            # 跳过空值或 None
            if not txt or txt.lower() == "none":
                continue
            try:
                _ = int(txt, 16)
            except Exception:
                self.tab4_table.setCurrentCell(i, 2)
                QMessageBox.warning(self, "输入错误", f"第{i+1}行当前值非法，请输入合法16进制数")
                return  # 只弹一次，直接终止！

        # 检查通过，才真正批量写入
        count = 0
        for i, (addr, val) in enumerate(zip(self.device.regaddr, self.device.config_current)):
            cell_item = self.tab4_table.item(i, 2)
            if cell_item is None:
                continue
            cell_str = cell_item.text().replace("0x", "").strip()
            # 跳过空值或 None
            if not cell_str or cell_str.lower() == "none":
                continue
            val = int(cell_str, 16)
            self.device.ad9643_write_reg(addr, val)
            count += 1
        self.append_text(f"批量写入完成，共写入{count}个寄存器。")
        self.refresh_reg_table()




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

    
        # 刷新寄存器表格的方法
    def refresh_reg_table(self):
        self.tab4_table.blockSignals(True)  # 暂停cellChanged信号
        self.tab4_table.setRowCount(len(self.device.regaddr))
        for i, (name, addr, val, dft, mode) in enumerate(zip(
                self.device.regname, self.device.regaddr,
                self.device.config_current, self.device.config_default,
                self.device.reg_mode)):
            self.tab4_table.setItem(i, 0, QTableWidgetItem(str(name)))
            self.tab4_table.setItem(i, 1, QTableWidgetItem(f"0x{addr:02X}"))
            vitem = QTableWidgetItem("" if val is None else f"0x{val:02X}")
            if mode == 'R':
                vitem.setFlags(vitem.flags() & ~Qt.ItemIsEditable)
            self.tab4_table.setItem(i, 2, vitem)
            self.tab4_table.setItem(i, 3, QTableWidgetItem("" if dft is None else f"0x{dft:02X}"))
            self.tab4_table.setItem(i, 4, QTableWidgetItem(mode))
        self.tab4_table.blockSignals(False)  # 恢复信号


    # 双击编辑"当前值"后，保存到config_current
    def reg_cell_changed(self, row, col):
        if col != 2:
            return
        item = self.tab4_table.item(row, col)
        new_val_str = item.text().replace("0x", "").strip()
        if not new_val_str or new_val_str.lower() == "none":
            self.device.config_current[row] = None
            return
        try:
            new_val = int(new_val_str, 16)
            self.device.config_current[row] = new_val
            self.append_text(f"修改 {self.device.regname[row]}(0x{self.device.regaddr[row]:02X}) 为 0x{new_val:02X}")
        except Exception:
            QMessageBox.warning(self, "输入错误", "请输入合法16进制数")
            self.refresh_reg_table()  # 恢复原值



if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

    


    