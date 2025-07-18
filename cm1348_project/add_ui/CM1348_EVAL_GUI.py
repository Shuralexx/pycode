import sys
from collections import defaultdict
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QMutex, QMutexLocker, Qt
from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout,QHBoxLayout, QMainWindow, QPushButton, QLCDNumber, QLabel, QComboBox, \
    QTabWidget, QProgressBar, QGroupBox, QStatusBar, QScrollArea, QVBoxLayout, QCheckBox, QLineEdit, QTableWidget,\
        QTableWidgetItem, QTextBrowser,QAbstractItemView
import pandas as pd
import struct
import pyqtgraph as pg
import numpy as np
from scipy import fftpack, stats, signal
import psutil
import time
import serial.tools.list_ports_windows
from Serial_class import SerialAchieve
from cm1348_dev import cm1348_dev


class Serial_Worker(QThread):
    dev = cm1348_dev()
    code_list = []
    finished = pyqtSignal()
    bartimer_signal = pyqtSignal(float)
    command = 'hand_shake'
    command_dic = defaultdict(int)

    def __init__(self, mutex, main_window,command, **kwargs):
        super().__init__()
        self.command = command
        self.mutex = mutex
        self.main_window = main_window
        for k,v in kwargs.items():
            self.command_dic[k] = int(v)

    def run(self):
        with QMutexLocker(self.mutex):
            self.run_command(self.command)

    # def run(self,command):
    def run_command(self, command):
        if command == 'cgf_write':
            print('thread in: addr=0x'+format(self.command_dic['addr'],'02X')+' value=0x'+format(self.command_dic['value'],'02X'))
            self.dev.cgf_write(self.command_dic['addr'], self.command_dic['value'])
        if command == 'hand_shake':
            self.dev.hand_shake()
        if command == 'capture':            
            print('thread in: wait for data!')
            self.dev.get_sample()
        if command == 'dev_reset':
            self.dev.dev_reset()
        if command == 'sample_num_set':
            self.dev.sample_num_set(self.dev.deep)
        self.finished.emit()


class MainUi(QMainWindow):

    def __init__(self):
        self.mutex = QMutex() # 定义进程锁对象
        super().__init__()
        # 完成结构体的初始化操作，需要保存内容的结构体都保存在UI自身内存中        
        self.dev0 = cm1348_dev()
        self.ser = SerialAchieve()
        self.mode_count = 0
        self.setWindowTitle("CM1348 EVALUATION SYSTEM REV0.0")
        self.bar_value = 0
        self.bar_flag = 0
        self.main_widget = QWidget()  # 所有界面都在 main widget 之上
        self.main_layout = QGridLayout()  # 创建一个网格布局
        self.main_widget.setLayout(self.main_layout)  # 设置主部件的布局为网格
        self.setCentralWidget(self.main_widget)  # 设置窗口默认部件
        self.setWindowIcon(QtGui.QIcon('cimo_icon.ico'))
        self.connected_status = 0
        self.ch_reference_flag = 0
        self.display_unit = 0 # 显示单位 0：LSB 1: volts
        self.cap_ch_count = [] # 这个变量用来表示当前采样值对应多少个通道
        self.data_plt = None
        # 在主界面之上添加3个 QWidget 分别作为串口控制区，配置区和显示区
        # serial_widget, config_widget and display_widget
        self.serial_widget = QWidget()
        self.serial_widget_layout = QGridLayout()
        self.config_widget = QWidget()
        self.config_widget_layout = QGridLayout()
        self.display_widget_tab = QTabWidget()
        # display widget之下，设置4个display tab;
        # time_tab, histogram_tab, fft_tab and reg_tab        
        self.time_tab = QWidget()
        self.histogram_tab = QWidget()
        self.fft_tab = QWidget()
        self.reg_tab = QWidget()
        self.display_widget_tab.addTab(self.time_tab, 'Time Domain Display')
        self.display_widget_tab.addTab(self.histogram_tab, 'Sample Histogram Analysis')
        self.display_widget_tab.addTab(self.fft_tab, 'Spectral Analysis')
        self.display_widget_tab.addTab(self.reg_tab, 'Register Config')
        self.display_widget_tab.setFixedWidth(700)
        # 为tab新建两个绘图画布
        self.time_tab_UI()
        self.hist_tab_UI()
        self.fft_tab_UI()
        self.reg_tab_UI()
        # 在main layout上添加三个主要的widget区
        self.main_layout.addWidget(self.serial_widget, 1, 2, 1, 8)
        self.serial_widget.setLayout(self.serial_widget_layout)
        self.main_layout.addWidget(self.config_widget, 1, 1, 11, 1)
        self.config_widget.setLayout(self.config_widget_layout)
        self.main_layout.addWidget(self.display_widget_tab, 2, 2, 10, 8)

        self.plot_widget = QWidget()  # 实例化一个widget部件作为K线图部件
        self.plot_layout = QGridLayout()  # 实例化一个网格布局层
        self.plot_widget.setLayout(self.plot_layout)  # 设置线图部件的布局层

        # serial Widget 部件添加
        #self.myserial = SerialAchieve()
        self.ser_list = []
        self.ser_combox = QComboBox()
        self.serport_get_button = QPushButton('读取串口')
        self.serport_open_button = QPushButton('打开串口')
        self.serport_close_button = QPushButton('关闭串口')
        self.ser_combox.addItem("请选择串口！")
        # 进度条配置
        self.progress_bar = QProgressBar(self)
        # 设置进度条的定时器
        self.bar_timer = QtCore.QTimer(self)
        #self.bar_timer.timeout.connect(self.bar_update)
        # 前面两个数字是坐标（y,x）后面两个是大小（Δy，Δx）
        self.serial_widget_layout.addWidget(self.ser_combox, 1, 1, 1, 2)
        self.serial_widget_layout.addWidget(self.serport_get_button, 1, 3, 1, 1)
        self.serial_widget_layout.addWidget(self.serport_open_button, 1, 4, 1, 1)
        self.serial_widget_layout.addWidget(self.serport_close_button, 1, 5, 1, 1)
        self.serial_widget_layout.addWidget(self.progress_bar,2,1,1,5)
        # 这两个选项是选择要显示的图形的通道数的
        self.display_control = QGroupBox('选择通道数据')
        self.display_control_layout = QHBoxLayout()
        self.display_control.setLayout(self.display_control_layout)
        self.ch_combobox = QComboBox()
        self.unit_combobox = QComboBox()
        self.unit_combobox.addItems(['Codes(LSB)','Volte(V)'])
        self.display_control_layout.addWidget(self.ch_combobox)
        self.display_control_layout.addWidget(self.unit_combobox)
        self.serial_widget_layout.addWidget(self.display_control,3,1,2,3)

        # Config Widget 部件添加 Config Widget下先分为三个 group
        # config layout 先以三个 config group进行排版，三个group再进行各自排版
        # control group
        self.device_control_group = QGroupBox('Device Control')
        self.device_control_group_layout = QGridLayout()
        self.device_control_group.setLayout(self.device_control_group_layout)
        self.PWDN_button = QPushButton('Power Down')
        self.RESET_button = QPushButton('Device Reset')
        self.Device_SYNC_button = QPushButton('Device Reg SYNC')
        self.connect_status = QPushButton()
        # self.connect_status.setStyleSheet('''QPushButton{background:#6DDF6D;border-radius:5px;}QPushButton:hover{background:green;}''')
        self.connect_status.setStyleSheet('''QPushButton{background:#FF3030;border-radius:5px;}QPushButton:hover{background:red;}''')
        self.connect_status_text = QLabel('disconnected')
        self.device_control_group_layout.addWidget(self.PWDN_button, 1, 1, 1, 2)
        self.device_control_group_layout.addWidget(self.RESET_button, 2, 1, 1, 2)
        self.device_control_group_layout.addWidget(self.connect_status, 3, 1, 1, 1)
        self.device_control_group_layout.addWidget(self.connect_status_text, 3, 2, 1, 1)
        self.device_control_group_layout.addWidget(self.Device_SYNC_button, 4, 1, 1, 2)
        
        # configuration group
        self.interface_configuration_group = QGroupBox('Interface Configuration')
        self.interface_configuration_group_layout = QGridLayout()
        self.interface_configuration_group.setLayout(self.interface_configuration_group_layout)
        self.mode_label = QLabel('Mode')
        self.mode_combobox = QComboBox()
        self.mode_combobox.addItems(['Auto-Scan', 'Fixed Channel'])
        self.dr_label = QLabel('Data Rate(SPS)')
        self.dr_combobox = QComboBox()
        self.dr_list_autoscan = ['1831','6168', '15123', '23739']
        self.dr_list_fixchannel = ['1953', '7813', '31250', '125000']
        self.dr_combobox.addItems(self.dr_list_autoscan)
        self.dr_combobox.setCurrentIndex(3)
        self.muxout_label = QLabel('MUXOUT Connection')
        self.muxout_combobox = QComboBox()
        self.muxout_combobox.addItems(['Disabled', 'Enabled'])
        self.muxout_combobox.setCurrentIndex(0)
        self.switch_delay_label = QLabel('Switch Time Delay')
        self.switch_delay_combobox = QComboBox()
        self.switch_delay_combobox.addItems(['No delay', '8us', '16us', '32us', '64us', '128us', '356us', '384us'])
        self.interface_configuration_group_layout.addWidget(self.mode_label, 1, 1, 1, 1)
        self.interface_configuration_group_layout.addWidget(self.mode_combobox, 2, 1, 1, 1)
        self.interface_configuration_group_layout.addWidget(self.dr_label, 3, 1, 1, 1)
        self.interface_configuration_group_layout.addWidget(self.dr_combobox, 4, 1, 1, 1)
        self.interface_configuration_group_layout.addWidget(self.muxout_label, 5, 1, 1, 1)
        self.interface_configuration_group_layout.addWidget(self.muxout_combobox, 6, 1, 1, 1)
        self.interface_configuration_group_layout.addWidget(self.switch_delay_label, 7, 1, 1, 1)
        self.interface_configuration_group_layout.addWidget(self.switch_delay_combobox, 8, 1, 1, 1)
        self.channel_selection = QScrollArea()        
        self.channel_selection.setFixedHeight(120)
        self.channel_selection_inner = QWidget()
        self.channel_selection_inner_layout = QVBoxLayout()
        self.channel_selection_inner.setLayout(self.channel_selection_inner_layout)   
        self.channel0 = QCheckBox('DIFF0(AIN0-1)')
        self.channel1 = QCheckBox('DIFF1(AIN2-3)')
        self.channel2 = QCheckBox('DIFF2(AIN4-5)')
        self.channel3 = QCheckBox('DIFF3(AIN6-7)')
        self.channel4 = QCheckBox('DIFF4(AIN8-9)')
        self.channel5 = QCheckBox('DIFF5(AIN10-11)')
        self.channel6 = QCheckBox('DIFF6(AIN12-13)')
        self.channel7 = QCheckBox('DIFF7(AIN14-15)')
        self.channel8 = QCheckBox('SE0(AIN0)')
        self.channel9 = QCheckBox('SE1(AIN1)')
        self.channel10 = QCheckBox('SE2(AIN2)')
        self.channel11 = QCheckBox('SE3(AIN3)')
        self.channel12 = QCheckBox('SE5(AIN4)')
        self.channel13 = QCheckBox('SE5(AIN5)')
        self.channel14 = QCheckBox('SE6(AIN6)')
        self.channel15 = QCheckBox('SE7(AIN7)')
        self.channel16 = QCheckBox('SE8(AIN8)')
        self.channel17 = QCheckBox('SE9(AIN9)')
        self.channel18 = QCheckBox('SE10(AIN10)')
        self.channel19 = QCheckBox('SE11(AIN11)')
        self.channel20 = QCheckBox('SE12(AIN12)')
        self.channel21 = QCheckBox('SE13(AIN13)')
        self.channel22 = QCheckBox('SE14(AIN14)')
        self.channel23 = QCheckBox('SE15(AIN15)')
        self.channel24 = QCheckBox('OFFSET')
        self.channel25 = QCheckBox('AVDD-AVSS')
        self.channel26 = QCheckBox('Temperature')
        self.channel27 = QCheckBox('Gain')
        self.channel28 = QCheckBox('REF')
        for i in range(29):
            self.channel_selection_inner_layout.addWidget(getattr(self, 'channel'+str(i)))
            if i>7 and i<24:
                getattr(self, 'channel'+str(i)).setChecked(True)
        self.channel_selection.setWidget(self.channel_selection_inner)
        self.basic_info_layout = QGridLayout()
        self.basic_info_group = QGroupBox('ADC Basic Info')
        self.basic_info_group.setLayout(self.basic_info_layout)        
        self.ref_label = QLabel('Vref(V)')
        self.ref_text = QLineEdit('2.5')
        self.sample_label = QLabel('Samples')
        self.sample_depth = QComboBox()
        self.sample_depth.addItems(['7000','4096','2048','1024','512','256','128','64','32','16', '8', '4', '2', '1'])
        self.capture_button = QPushButton('Capture')
        self.sclk_label = QLabel('SCLK')
        self.sclk_text = QLineEdit('8.00MHz')
        self.mclk_label = QLabel('MCLK')
        self.mclk_text = QLineEdit('16.00MHz')
        self.basic_info_layout.addWidget(self.ref_label,1,1,1,1)
        self.basic_info_layout.addWidget(self.ref_text,1,2,1,1)
        self.basic_info_layout.addWidget(self.sample_label,2,1,1,1)
        self.basic_info_layout.addWidget(self.sample_depth,2,2,1,1)
        self.basic_info_layout.addWidget(self.capture_button,3,1,1,3)
        self.basic_info_layout.addWidget(self.sclk_label,4,1,1,1)   
        self.basic_info_layout.addWidget(self.sclk_text,4,2,1,1)
        self.basic_info_layout.addWidget(self.mclk_label,5,1,1,1)
        self.basic_info_layout.addWidget(self.mclk_text,5,2,1,1)

        self.config_widget_layout.addWidget(self.device_control_group,1,1,1,1)
        self.config_widget_layout.addWidget(self.interface_configuration_group,2,1,1,1)
        self.config_widget_layout.addWidget(self.channel_selection,3,1,1,1)
        self.config_widget_layout.addWidget(self.basic_info_group,4,1,1,1)
        
        # 串口控制模块配置
        self.serport_get_button.pressed.connect(lambda: self.ser_port_read(self.dev0))
        self.serport_open_button.pressed.connect(lambda: self.ser_connect(self.dev0))
        self.serport_close_button.pressed.connect(lambda: self.ser_close(self.dev0))
        self.ser_combox.activated.connect(lambda: self.ser_port_select(self.dev0))

        # 连续采样模式配置
        self.setCentralWidget(self.main_widget)
        self.data_list = []
        self.timer = QtCore.QTimer(self)
        #######################################
        # 交互设计
        #######################################
        
        self.action_init()

    def time_tab_UI(self):
        self.tab1_Label = QLabel('时域图', self)
        # 设置统计值表格
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

        self.tab1_layout = QGridLayout()
        self.tab1_plt = pg.PlotWidget()  # 实例化一个绘图部件
        self.tab1_plt.showGrid(x=True, y=False)  # 显示图形网格
        self.tab1_plt.setBackground(background=None)
        self.tab1_layout.addWidget(self.tab1_Label, 1, 1, 1, 6)
        self.tab1_layout.addWidget(self.tab1_plt, 2, 1, 1, 6)
        self.tab1_layout.addWidget(self.tab1_measure_label,4,1,1,6)
        self.tab1_layout.addWidget(self.tab1_measure,5,1,1,6)
        self.time_tab.setLayout(self.tab1_layout)

    def hist_tab_UI(self):
        self.tab2_Label = QLabel('码值直方图', self)
        self.tab2_layout = QGridLayout()
        self.tab2_plt = pg.PlotWidget()  # 实例化一个绘图部件
        self.tab2_plt.showGrid(x=False, y=True)  # 显示图形网格
        self.tab2_plt.setBackground(background=None)
         # 设置统计值表格
        self.tab2_measure_label = QLabel('Measurements')
        self.tab2_measure = QTableWidget()
        self.tab2_measure.setFixedHeight(120)
        self.tab2_measure.setColumnCount(7)
        self.tab2_measure.setRowCount(1)
        self.tab2_measure.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tab2_measure.setHorizontalHeaderLabels(['Channel', 'Min', 'Max', 'Sigma', 'Mean','Peak to Peak','ENOB'])
        self.tab2_measure.horizontalHeader().setStyleSheet('QHeaderView::section{background:grey;color:white;font:bold}') #设置表头格式
        self.tab2_measure.setFixedWidth(700)
        self.tab2_layout.addWidget(self.tab2_Label, 1, 1, 1, 6)
        self.tab2_layout.addWidget(self.tab2_plt, 2, 1, 1, 6)
        self.tab2_layout.addWidget(self.tab2_measure_label,4,1,1,6)
        self.tab2_layout.addWidget(self.tab2_measure,5,1,1,6)
        self.histogram_tab.setLayout(self.tab2_layout)

    def fft_tab_UI(self):
        self.tab3_Label = QLabel('频谱图', self)
        self.tab3_layout = QGridLayout()
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
        self.tab3_layout.addWidget(self.tab3_Label, 1, 1, 1, 6)
        self.tab3_layout.addWidget(self.tab3_plt, 2, 1, 1, 6)
        self.tab3_layout.addWidget(self.tab3_measure_label,4,1,1,6)
        self.tab3_layout.addWidget(self.tab3_measure,5,1,1,6)
        self.fft_tab.setLayout(self.tab3_layout)

    def reg_tab_UI(self):
        self.tab4_Label = QLabel('寄存器列表', self)
        self.tab4_layout = QGridLayout()
        self.tab4_table = QTableWidget()  # 实例化一个表格
        self.tab4_table.setColumnCount(5) # 设置共有5列数据： 寄存器名/寄存器地址/寄存器默认值/寄存器能力/寄存器当前值
        self.tab4_table.setHorizontalHeaderLabels(['Register Name', 'Address', 'Default', 'Mode', 'Value'])
        self.tab4_table.horizontalHeader().setStyleSheet('QHeaderView::section{background:grey;color:white;font:bold}') #设置表头格式
        self.tab4_table.setRowCount(10)
        self.tab4_table.setFixedWidth(550)
        self.tab4_table.setFixedHeight(350)
        self.tab4_layout.addWidget(self.tab4_Label, 1, 1, 1, 6)
        self.tab4_layout.addWidget(self.tab4_table, 2, 1, 6, 6)
        self.reg_tab.setLayout(self.tab4_layout)
        self.description_label = QLabel('Register Description')
        self.description_text = QTextBrowser()
        self.description_text.setFixedHeight(120)
        #增加寄存器单独编辑框
        self.solo_group = QGroupBox('寄存器编辑')
        self.solo_group_layout = QVBoxLayout()
        self.solo_group.setLayout(self.solo_group_layout)
        self.solo_group.setFixedWidth(110)
        self.solo_reg = QLineEdit()
        self.solo_reg_write = QPushButton('Write to Reg')
        self.tab4_layout.addWidget(self.description_label, 8, 1, 1, 7)
        self.tab4_layout.addWidget(self.description_text, 9, 1, 1, 7)
        self.tab4_layout.addWidget(self.solo_group,2,7,1,1)
        self.solo_reg.setFixedSize(120,50)
        self.solo_reg_write.setFixedSize(100,30)
        self.solo_group_layout.addWidget(self.solo_reg)
        self.solo_group_layout.addWidget(self.solo_reg_write)
        # 设置表格是不可编辑的，防止任意编辑造成表格显示寄存器值不对
        self.tab4_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        row = 0
        for addr in self.dev0.regaddr:
            item = QTableWidgetItem(self.dev0.regname[row])
            # item.setFlags(Qt.ItemSelectionMode)
            self.tab4_table.setItem(row, 0, item)
            item = QTableWidgetItem('0x' + format(addr, '02X'))
            # item.setFlags(Qt.ItemIsEnabled)
            self.tab4_table.setItem(row, 1,item)
            item = QTableWidgetItem('0x' + format(self.dev0.config_default[row],'02X'))
            # item.setFlags(Qt.ItemSelectionMode)
            self.tab4_table.setItem(row, 2, item)
            item = QTableWidgetItem(self.dev0.reg_mode[row])
            # item.setFlags(Qt.ItemSelectionMode)
            self.tab4_table.setItem(row, 3, item)
            item = QTableWidgetItem('0x' + format(self.dev0.config[row], '02X'))
            # item.setFlags(Qt.ItemSelectionMode)
            self.tab4_table.setItem(row, 4, item)
            row = row+1

    def ser_port_read(self,dev):
        self.ser_list = dev.myserial.port_get()
        print("combox activated!")
        if len(self.ser_list) != 0:
            self.ser_combox.clear()
            for ser_num in self.ser_list:
                self.ser_combox.addItem(ser_num.description)
            self.ser_combox.addItem("no more")
            dev.myserial.port = dev.myserial.port_list[0].device
            # 如果串口中有CH340字样的串口，则自动选择该串口
            port_index = 0
            for port_num in dev.myserial.port_list:
                if "CH340" in port_num.description:
                    print(port_num.description)
                    self.ser_combox.setCurrentIndex(port_index)
                    dev.myserial.port = dev.myserial.port_list[port_index].device                    
                port_index=port_index+1 

    def ser_port_select(self,dev):
        num = self.ser_combox.currentIndex()
        dev.myserial.port = dev.myserial.port_list[num].device

    def ser_connect(self,dev):
        dev.myserial.open_port()
        dev.hand_shake()
        for i in range(4):
            dev.cgf_write(3+i,dev.config[3+i])
        if dev.connect_status == 1:
            self.connect_status_change(1)
        else:
            self.connect_status_change(0)

    def ser_close(self,dev):
        dev.myserial.close_port()
        dev.connect_status = 0
        self.connect_status_change(0)

    def disp_erase(self):
        self.data_list.clear()
        self.tab1_plt.clear()

    def timer_start(self):
        self.timer.start(1000)

    def timer_stop(self):
        self.timer.stop()

    def connect_status_change(self,on_off):
        if on_off == 0:
            self.connect_status.setStyleSheet('''QPushButton{background:#FF3030;border-radius:5px;}QPushButton:hover{background:red;}''')
            self.connected_status = 0
            self.connect_status_text.setText('disconnected')
        else:
            self.connect_status.setStyleSheet('''QPushButton{background:#6DDF6D;border-radius:5px;}QPushButton:hover{background:green;}''')
            self.connected_status = 1
            self.connect_status_text.setText('connected')
    
    def action_init(self):
        self.mode_combobox.currentIndexChanged.connect(self.mode_change) # ADC mode change event
        self.dr_combobox.currentIndexChanged.connect(self.dr_change) # ADC DR change event
        self.dr_update_flag = 0
        self.muxout_combobox.currentIndexChanged.connect(self.muxout_change)
        self.switch_delay_combobox.currentIndexChanged.connect(self.switch_delay_change)
        self.connect_status.clicked.connect(self.connect_status_click) # 点击连接状态指示灯，PC和MCU会握手
        #寄存器表页面交互逻辑
        self.solo_reg_write.clicked.connect(self.solo_config_write)
        self.tab4_table.clicked.connect(self.description_update) # 点击对应寄存器位置，显示寄存器描述
        self.channel0.stateChanged.connect(lambda:self.check_box_change(self.channel0))
        self.channel1.stateChanged.connect(lambda:self.check_box_change(self.channel1))
        self.channel2.stateChanged.connect(lambda:self.check_box_change(self.channel2))
        self.channel3.stateChanged.connect(lambda:self.check_box_change(self.channel3))
        self.channel4.stateChanged.connect(lambda:self.check_box_change(self.channel4))
        self.channel5.stateChanged.connect(lambda:self.check_box_change(self.channel5))
        self.channel6.stateChanged.connect(lambda:self.check_box_change(self.channel6))
        self.channel7.stateChanged.connect(lambda:self.check_box_change(self.channel7))
        self.channel8.stateChanged.connect(lambda:self.check_box_change(self.channel8))
        self.channel9.stateChanged.connect(lambda:self.check_box_change(self.channel9))
        self.channel10.stateChanged.connect(lambda:self.check_box_change(self.channel10))
        self.channel11.stateChanged.connect(lambda:self.check_box_change(self.channel11))
        self.channel12.stateChanged.connect(lambda:self.check_box_change(self.channel12))
        self.channel13.stateChanged.connect(lambda:self.check_box_change(self.channel13))
        self.channel14.stateChanged.connect(lambda:self.check_box_change(self.channel14))
        self.channel15.stateChanged.connect(lambda:self.check_box_change(self.channel15))
        self.channel16.stateChanged.connect(lambda:self.check_box_change(self.channel16))
        self.channel17.stateChanged.connect(lambda:self.check_box_change(self.channel17))
        self.channel18.stateChanged.connect(lambda:self.check_box_change(self.channel18))
        self.channel19.stateChanged.connect(lambda:self.check_box_change(self.channel19))
        self.channel20.stateChanged.connect(lambda:self.check_box_change(self.channel20))
        self.channel21.stateChanged.connect(lambda:self.check_box_change(self.channel21))
        self.channel22.stateChanged.connect(lambda:self.check_box_change(self.channel22))
        self.channel23.stateChanged.connect(lambda:self.check_box_change(self.channel23))
        self.channel24.stateChanged.connect(lambda:self.check_box_change(self.channel24))
        self.channel25.stateChanged.connect(lambda:self.check_box_change(self.channel25))
        self.channel26.stateChanged.connect(lambda:self.check_box_change(self.channel26))
        self.channel27.stateChanged.connect(lambda:self.check_box_change(self.channel27))
        self.channel28.stateChanged.connect(lambda:self.check_box_change(self.channel28))
        self.checkbox_clear_flag = 0 # 表示当前正在做通道 checkbox的清理，这时候checkbox state 的改变不要引发额外的信号槽连接
        self.check_flag = 0 # 表示是否至少有一个通道被选中了

        # 配置功能
        self.RESET_button.clicked.connect(self.reset_dev)
        self.Device_SYNC_button.clicked.connect(self.device_sync)

        # 采样控制功能
        self.sample_depth.currentIndexChanged.connect(self.set_sample_depth)
        self.capture_button.clicked.connect(self.capture)
        self.ch_combobox.currentIndexChanged.connect(self.capture_ch_select)
        self.unit_combobox.currentIndexChanged.connect(self.unit_change)
        
    def device_sync(self): # 这个功能是为了保证，当用额外的功能修改了寄存器后，保证设置被同步
        # 将 dev.config中的所有寄存器都配置一遍
        for i in range(10):
            self.dev0.cgf_write(i,self.dev0.config[i])

    def solo_config_write(self):
        self.dev0.config[self.tab4_table.currentRow()] = int(self.solo_reg.text()[-2:],16) # 首先将config0上 bit 5 置 0 
        print('CONFIG0 change to 0x'+format(int(self.solo_reg.text()[-2:],16),'02X'))
        worker_config_change = Serial_Worker(self.mutex, self,'cgf_write',addr=self.tab4_table.currentRow(),value=self.dev0.config[self.tab4_table.currentRow()])
        worker_config_change.dev = self.dev0  
        worker_config_change.start()
        worker_config_change.finished.connect(worker_config_change.quit)
        worker_config_change.finished.connect(worker_config_change.wait)
        worker_config_change.finished.connect(worker_config_change.deleteLater)
        self.reg_table_update(self.tab4_table.currentRow(),self.dev0.config[self.tab4_table.currentRow()])


    def description_update(self):
        #print(self.tab4_table.currentRow())
        self.description_text.setText(self.dev0.reg_description[self.tab4_table.currentRow()])
        self.solo_reg.setText(self.tab4_table.model().index(self.tab4_table.currentRow(),4).data())

    def set_sample_depth(self):
        print('set_sample_length')        
        if self.connected_status == 1:
            self.dev0.sample_num_set(13-self.sample_depth.currentIndex())
            # sample_set = Serial_Worker(self.mutex, self,'sample_num_set')
            # sample_set.command = 'sample_num_set'
            # sample_set.dev = self.dev0
            # sample_set.dev.deep = 13-self.sample_depth.currentIndex()
            # sample_set.start()
            # sample_set.finished.connect(sample_set.quit)
            # sample_set.finished.connect(sample_set.wait)
            # sample_set.finished.connect(sample_set.deleteLater)

    def mode_change(self):
        self.dr_combobox_update()
        self.checkbox_clear()
        self.dev0.config[0] = self.dev0.config[0] & 0b11011111 # 首先将config0上 bit 5 置 0 
        self.dev0.config[0] = self.dev0.config[0] | (self.mode_combobox.currentIndex()<<5)
        print('CONFIG0 change to 0x'+format(self.dev0.config[0],'02X'))
        if self.connected_status == 1:
            self.dev0.cgf_write(0,self.dev0.config[0])
            # worker_mode_change = Serial_Worker(self.mutex, self,'cgf_write',addr=0x00,value=self.dev0.config[0])
            # worker_mode_change.dev = self.dev0  
            # worker_mode_change.start()
            # worker_mode_change.finished.connect(worker_mode_change.quit)
            # worker_mode_change.finished.connect(worker_mode_change.wait)
            # worker_mode_change.finished.connect(worker_mode_change.deleteLater)
        self.reg_table_update(0x00,self.dev0.config[0])

    def dr_change(self):
        if self.dr_update_flag==0: # 没有在进行更新 dr的操作，才认为是真正的dr函数
            self.dev0.config[1] = self.dev0.config[1] & 0b11111100 # 首先将DRATE1/0两位置0
            self.dev0.config[1] = self.dev0.config[1] | (self.dr_combobox.currentIndex() & 0x03)
            print('CONFIG1 change to 0x'+format(self.dev0.config[1],'02X'))
            if self.connected_status:
                self.dev0.cgf_write(1,self.dev0.config[1])
                # worker_dr_change = Serial_Worker(self.mutex, self,'cgf_write',addr=0x01,value=self.dev0.config[1])
                # worker_dr_change.dev = self.dev0  
                # worker_dr_change.start()
                # worker_dr_change.finished.connect(worker_dr_change.quit)
                # worker_dr_change.finished.connect(worker_dr_change.wait)
                # worker_dr_change.finished.connect(worker_dr_change.deleteLater)
            self.reg_table_update(0x01,self.dev0.config[1])

    def muxout_change(self):        
        self.dev0.config[0] = self.dev0.config[0] & 0b11101111 # 首先将BYPAS bit置0
        self.dev0.config[0] = self.dev0.config[0] | (self.muxout_combobox.currentIndex() << 4)
        print('CONFIG0 change to 0x'+format(self.dev0.config[0],'02X'))
        if self.connected_status==1:
            self.dev0.cgf_write(0,self.dev0.config[0])
        # worker_mxu_change = Serial_Worker(self.mutex, self,'cgf_write',addr=0x00,value=self.dev0.config[0])
        # worker_mxu_change.dev = self.dev0  
        # worker_mxu_change.start()
        # worker_mxu_change.finished.connect(worker_mxu_change.quit)
        # worker_mxu_change.finished.connect(worker_mxu_change.wait)
        # worker_mxu_change.finished.connect(worker_mxu_change.deleteLater)
        self.reg_table_update(0x00,self.dev0.config[0])

    def switch_delay_change(self):        
        self.dev0.config[1] = self.dev0.config[1] & 0b10001111 # 首先将BYPAS bit置0
        self.dev0.config[1] = self.dev0.config[1] | (self.switch_delay_combobox.currentIndex() << 4)
        print('CONFIG0 change to 0x'+format(self.dev0.config[1],'02X'))
        if self.connected_status==1:
            self.dev0.cgf_write(1,self.dev0.config[1])
            # worker_DLY_change = Serial_Worker(self.mutex, self,'cgf_write',addr=0x01,value=self.dev0.config[1])
            # worker_DLY_change.dev = self.dev0  
            # worker_DLY_change.start()
            # worker_DLY_change.finished.connect(worker_DLY_change.quit)
            # worker_DLY_change.finished.connect(worker_DLY_change.wait)
            # worker_DLY_change.finished.connect(worker_DLY_change.deleteLater)
        self.reg_table_update(0x01,self.dev0.config[1])
    
    def check_box_change(self,ch):
        # 必须保证调用check box重置函数的时候，不触发
        if self.checkbox_clear_flag==0 : # 本函数只响应手动点击的check box状态变化
            if self.mode_combobox.currentIndex() == 0: # Auto Sacn Mode
                MUXDIF_temp = 0b00000000
                for i in range(8):
                    MUXDIF_temp = MUXDIF_temp | (getattr(self,'channel'+str(i)).isChecked() << i)
                print(format(MUXDIF_temp,'08b'))
                self.dev0.config[3] = MUXDIF_temp
                MUXSG0_temp = 0b00000000
                for i in range(8):
                    MUXSG0_temp = MUXSG0_temp | (getattr(self,'channel'+str(i+8)).isChecked() << i)
                print(format(MUXSG0_temp,'08b'))
                self.dev0.config[4] = MUXSG0_temp
                MUXSG1_temp = 0b00000000
                for i in range(8):
                    MUXSG1_temp = MUXSG1_temp | (getattr(self,'channel'+str(i+16)).isChecked() << i)
                print(format(MUXSG1_temp,'08b'))
                self.dev0.config[5] = MUXSG1_temp
                SYSRED_temp = 0b00000000
                SYSRED_temp = self.channel24.isChecked()
                for i in range(4):
                    SYSRED_temp = SYSRED_temp | (getattr(self,'channel'+str(i+25)).isChecked() << (i+2))
                print(format(SYSRED_temp,'08b'))
                self.dev0.config[6] = SYSRED_temp
                value_list = [MUXDIF_temp,MUXSG0_temp,MUXSG1_temp,SYSRED_temp]
                addr_list = [0x03,0x04,0x05,0x06]
                if self.connected_status==1:
                    # write all the 4 auto scan configs
                    # worker_ch_change = Serial_Worker(self.mutex, self,'unknow')
                    # worker_ch_change.dev = self.dev0
                    # worker_ch_change.command = 'cgf_write'
                    for i in range(4):
                        self.dev0.cgf_write(3+i,self.dev0.config[3+i])
                        # worker_ch_change.command_dic['addr'] = addr_list[i]
                        # worker_ch_change.command_dic['value'] = value_list[i]
                        # worker_ch_change.start()
                        # while not worker_ch_change.isFinished():
                        #     continue
                        self.reg_table_update(addr_list[i],value_list[i])
                    # worker_ch_change.finished.connect(worker_ch_change.quit)
                    # worker_ch_change.finished.connect(worker_ch_change.wait)
                    # worker_ch_change.finished.connect(worker_ch_change.deleteLater)
                    
            elif self.mode_combobox.currentIndex() == 1: # Fixed Channel Mode
                if ch.isChecked(): #从不选到选中
                    self.check_flag = 1 # 保证只有1个能被选中
                    channel_select = None
                    for i in range(8): # 每次将mode切换成 fix mode后，只有diff通道才允许选中
                        if getattr(self,'channel'+str(i)).isChecked():
                            channel_select = i
                        else:
                            getattr(self,'channel'+str(i)).setCheckable(False)
                    # 配置相应的 0x02 MUXSCH 寄存器
                    value_list = [0x01,0x23,0x45,0x67,0x89,0xAB,0xCD,0xEF]
                    print(format(value_list[channel_select],'08b'))
                    self.dev0.config[2] = value_list[channel_select]
                    if self.connected_status==1:
                        self.dev0.cgf_write(2,value_list[channel_select])
                    # worker_ch_change = Serial_Worker(self.mutex, self,'cgf_write',addr=0x02,value=value_list[channel_select])
                    # worker_ch_change.dev = self.dev0
                    # worker_ch_change.start()
                    # worker_ch_change.finished.connect(worker_ch_change.quit)
                    # worker_ch_change.finished.connect(worker_ch_change.wait)
                    # worker_ch_change.finished.connect(worker_ch_change.deleteLater)
                    self.reg_table_update(0x02,value_list[channel_select])
                else: # 从选中到不选
                    self.checkbox_clear()
                    self.check_flag = 0
                    # 清理当前checkbox状态，并重新等待选择
                    # worker_ch_change = Serial_Worker(self.mutex, self,'cgf_write',addr=0x02,value=0x00)
                    # worker_ch_change.dev = self.dev0
                    # worker_ch_change.start()
                    # worker_ch_change.finished.connect(worker_ch_change.quit)
                    # worker_ch_change.finished.connect(worker_ch_change.wait)
                    # worker_ch_change.finished.connect(worker_ch_change.deleteLater)
                    self.reg_table_update(0x02,0x00)

    def dr_combobox_update(self):
        self.dr_update_flag = 1
        dr_index_backup = self.dr_combobox.currentIndex()
        self.dr_combobox.clear()
        if self.mode_combobox.currentIndex() == 0: # 这里使用 currentIndex的话，需要后面接括号，它是一个方法，返回值是int，如果不加括号，返回值是函数地址
            self.dr_combobox.addItems(self.dr_list_autoscan)
        elif self.mode_combobox.currentIndex() == 1:
            self.dr_combobox.addItems(self.dr_list_fixchannel)
        self.dr_combobox.setCurrentIndex(dr_index_backup)
        self.dr_update_flag = 0
    
    def checkbox_clear(self): # 因为要限制fix channel mode下 选取通道数量；每次改变mode，需要将checkbox清空
        self.checkbox_clear_flag = 1
        if self.mode_combobox.currentIndex()==1: # fixed mode, 仅支持差分输入模式
            for i in range(29):
                if i<8:
                    getattr(self, 'channel'+str(i)).setCheckable(True)
                else:
                    getattr(self, 'channel'+str(i)).setCheckable(False)
                getattr(self, 'channel'+str(i)).setChecked(False)
            if self.connected_status==1:
                self.dev0.cgf_write(2,0x00)
            self.reg_table_update(2,self.dev0.config[2])
        elif self.mode_combobox.currentIndex() == 0: # Auto Scan mode, 所有输入选项都支持
            for i in range(29):
                getattr(self, 'channel'+str(i)).setCheckable(True)
                if i<2: # 默认使能DIFF0 和 DIFF1 通道
                    getattr(self, 'channel'+str(i)).setChecked(True)
                else:
                    getattr(self, 'channel'+str(i)).setChecked(False)
            if self.connected_status==1:
                self.dev0.cgf_write(3,0x03)
                self.dev0.cgf_write(4,0x00)
                self.dev0.cgf_write(5,0x00)
                self.dev0.cgf_write(6,0x00)
            for i in range(4):
                self.reg_table_update(3+i,self.dev0.config[3+i])
        # 这里就不配置相应的 0x02,03,04,05,06 MUX 寄存器了; 因为保证checkbox_clear_flag=1 下，没办法进行采样就好了
        self.checkbox_clear_flag = 0

    def connect_status_click(self):
        if self.connected_status == 1:
            self.worker = Serial_Worker(self.mutex,self,'hand_shake')
            self.worker.dev = self.dev0
            self.worker.start()
            self.worker.finished.connect(self.worker.quit)
            self.worker.finished.connect(self.worker.wait)
            self.worker.finished.connect(self.worker.deleteLater)
    
    def unit_change(self):
        self.display_unit = self.unit_combobox.currentIndex() # 选择对应的单位 0：code 1：volt
        self.capture_ch_select() # 更新绘图
    
    def capture_ch_select(self):
        if self.ch_reference_flag == 0: # 确定是人工的选择，防止采样前通道数据预处理造成错误引用
            self.adc_code = self.data_plt[self.ch_combobox.currentIndex(),:]
            if self.display_unit == 0: # code
                self.adc_data = self.data_plt[self.ch_combobox.currentIndex(),:] # 选择相应的通道   
                self.adc_data_plt = self.adc_data        
                styles = {'color':'r', 'font-size':'10px'}
                self.tab1_plt.setLabel('left', 'Code(LSB)', **styles)
                self.tab1_plt.setLabel('bottom', 'Samples', **styles)
                self.data_display() # 更新绘图
                # 更新下方表格中的名称和单位
            else: # volt mode
                if self.cap_ch_count[self.ch_combobox.currentIndex()]<25: # 8路差分+16路单端+offset
                    LSB = float(self.ref_text.text())/7864320 # 780000h
                    styles = {'color':'r', 'font-size':'10px'}
                    self.tab1_plt.setLabel('left', 'Voltage(V)', **styles)
                    self.tab1_plt.setLabel('bottom', 'Samples', **styles)
                    data_volt = self.data_plt[self.ch_combobox.currentIndex(),:]*LSB # 选择相应的通道
                    self.adc_data = data_volt
                    self.micro_mini = 0
                    self.adc_data_plt = data_volt
                    # 自适应显示的单位
                    if np.max(np.abs(data_volt))<0.1:
                        mini_volt = data_volt*1e3
                        self.adc_data_plt = mini_volt
                        styles = {'color':'r', 'font-size':'10px'}
                        self.tab1_plt.setLabel('left', 'Voltage(mV)', **styles)
                        self.tab1_plt.setLabel('bottom', 'Samples', **styles)
                        self.micro_mini = 1
                    elif np.max(np.abs(data_volt))<0.001:
                        micro_volt = data_volt*1e6
                        self.adc_data_plt = micro_volt
                        styles = {'color':'r', 'font-size':'10px'}
                        self.tab1_plt.setLabel('left', 'Voltage(uV)', **styles)
                        self.tab1_plt.setLabel('bottom', 'Samples', **styles)
                        self.micro_mini = 2
                elif self.cap_ch_count[self.ch_combobox.currentIndex()]==26 or self.cap_ch_count[self.ch_combobox.currentIndex()]==29: # 选取的是VCC和REF
                        data_volt = self.data_plt[self.ch_combobox.currentIndex(),:]/786432/2
                        self.adc_data = data_volt
                        self.adc_data_plt = data_volt
                        styles = {'color':'r', 'font-size':'10px'}
                        self.tab1_plt.setLabel('left', 'Voltage(V)', **styles)
                        self.tab1_plt.setLabel('bottom', 'Samples', **styles)
                        self.micro_mini = 0
                elif self.cap_ch_count[self.ch_combobox.currentIndex()]==28: # 选取Gain 通道
                        data_volt = self.data_plt[self.ch_combobox.currentIndex(),:]/7864320
                        self.adc_data = data_volt
                        self.adc_data_plt = data_volt
                        styles = {'color':'r', 'font-size':'10px'}
                        self.tab1_plt.setLabel('left', 'Voltage(V)', **styles)
                        self.tab1_plt.setLabel('bottom', 'Samples', **styles)
                        self.micro_mini = 0
                elif self.cap_ch_count[self.ch_combobox.currentIndex()]==27: # 选取Temp 通道
                        LSB = float(self.ref_text.text())*1.06/8388608
                        data_temp = (self.data_plt[self.ch_combobox.currentIndex(),:]*LSB*1e6-168000)/563+25
                        self.adc_data = data_temp
                        self.adc_data_plt = data_temp
                        styles = {'color':'r', 'font-size':'10px'}
                        self.tab1_plt.setLabel('left', 'Temperature(℃)', **styles)
                        self.tab1_plt.setLabel('bottom', 'Samples', **styles)
                        self.micro_mini = 0
            self.data_display() # 更新绘图



    def capture(self):
        fix_ch = ['AIN0-AIN1','AIN2-AIN3','AIN4-AIN5','AIN6-AIN7','AIN8-AIN9','AIN10-AIN11','AIN12-AIN13','AIN14-AIN15']
        # 根据 dev config的配置，配置通道选择图形配置 
        if self.mode_combobox.currentIndex() == 0: #auto Scan mode
            self.ch_reference()
        else:  # fixed channel mode
            self.ch_reference_flag = 1
            self.ch_combobox.clear()
            self.ch_combobox.addItem(fix_ch[(self.dev0.config[2] & 0x0F)>>1]) # 选择当下选择的固定的通道
            self.cap_ch_count.clear()
            self.cap_ch_count.append((self.dev0.config[2] & 0x0F)>>1)
            self.ch_reference_flag = 0
        # 正式开始采样
        if self.connected_status == 1:
            sample_capture_worker = Serial_Worker(self.mutex,self,'capture')
            sample_capture_worker.dev = self.dev0
            sample_capture_worker.start()
            sample_capture_worker.finished.connect(sample_capture_worker.quit)
            sample_capture_worker.finished.connect(sample_capture_worker.wait)
            sample_capture_worker.finished.connect(sample_capture_worker.deleteLater)
            sample_capture_worker.finished.connect(self.sample_manipulate)
            # 计算采样点对应每通道多少个点            
        else:
            # 生成假数据产生仿真效果
            fs = int(self.dr_combobox.currentText())
            fa = 1.19642857e3 # 相干采样频率 Fs/Fi = N/M
            N = self.dev0.sample_num
            sin_AMP = np.round(np.power(2,15)*np.random.randn())
            self.dev0.rx_data = self.sin_wave(sin_AMP-1,fa,fs,0,N)
            print(self.cap_ch_count)
            self.dev0.rx_status = self.cap_ch_count
            self.sample_manipulate()
            # self.data_display() 

    def sample_manipulate(self):
        if self.mode_combobox.currentIndex() == 0: # auto Scan mode 需要截位
            pos_idex = self.cap_ch_count.index(self.dev0.rx_status[0]&0x1f)
            print('first position:',pos_idex) # 判断这个通道是第几个通道：
            start_pos = len(self.cap_ch_count)-pos_idex # 从该位置开始是轮询采样的第一通道
            per_ch_length = np.floor((self.dev0.sample_num-start_pos)/len(self.cap_ch_count))
            end_pos = int(per_ch_length*len(self.cap_ch_count))
        else: # Fixed Mode 不需要截位
            start_pos = 0
            end_pos = len(self.dev0.rx_data)
            per_ch_length = len(self.dev0.rx_data)
        self.data_plt = np.empty(shape =(int(len(self.cap_ch_count)),int(per_ch_length)))
        self.data_plt = np.array(self.dev0.rx_data[start_pos:start_pos+end_pos]) # 截取数据，保证所有的通道数据等长
        # self.data_plt_status = np.empty(shape =(int(len(self.cap_ch_count)),int(per_ch_length)))
        # self.data_plt_status = np.array(self.dev0.rx_status[start_pos:start_pos+end_pos]) # 截取数据，保证所有的通道数据等长
        print(len(self.data_plt))
        # self.data_plt_status = np.reshape(self.data_plt_status,(int(per_ch_length),len(self.cap_ch_count)))
        # self.data_plt_status = self.data_plt_status.T # 将信号转秩
        self.data_plt = np.reshape(self.data_plt,(int(per_ch_length),len(self.cap_ch_count)))
        self.data_plt = self.data_plt.T # 将信号转秩
        self.adc_data = self.data_plt[0,:] # 默认选择第一通道s
        self.capture_ch_select()
        # self.data_display()

    def reset_dev(self):
        if self.connected_status == 1:
            self.dev0.dev_reset()
            self.mode_combobox.setCurrentIndex(0) # 默认就包含了通道选择 check box的初始化
            self.dr_combobox.setCurrentIndex(3)
            self.muxout_combobox.setCurrentIndex(0)
            self.switch_delay_combobox.setCurrentIndex(0)
            print('Reset Device to default state!')
        

    # 绘图函数 更新数据和表格等4个展示页面
    def reg_table_update(self,addr,value):
        self.tab4_table.setItem(addr, 4, QTableWidgetItem('0x' + format(value, '02X')))
        #print(self.dev0.regname[addr],'display change to 0x',format(value, '02X'))

    # 将数据转换为.2f 能显示的最合适的值，并返回对应的单位
    def unit_suite(self,data):
        if np.abs(data) < 0.0001:
            return [data*1e6,2]
        elif np.abs(data) < 0.1:
            return [data*1e3,1]
        else:
            return [data,0]
    
    # 数据绘图函数，将数据更新到所有的3个显示界面中
    def data_display(self):
        # time domain display
        self.tab1_plt.clear()
        self.tab1_plt.plot().setData(self.adc_data_plt,pen='r') # 绘图用 plt的数据作图； 统计还用原始数据
        print('length of data plot is:', len(self.adc_data_plt))
        unit_str = ['V','mV','uV']
        if self.unit_combobox.currentIndex() == 0: # 以码值显示形式
            self.tab1_measure.setItem(0, 0, QTableWidgetItem(self.ch_combobox.currentText()))
            self.tab1_measure.setItem(0, 1, QTableWidgetItem(format(np.min(self.adc_data),'.0f')))
            self.tab1_measure.setItem(0, 2, QTableWidgetItem(format(np.max(self.adc_data),'.0f')))
            self.tab1_measure.setItem(0, 3, QTableWidgetItem(format(np.std(self.adc_data),'.3f')))
            self.tab1_measure.setItem(0, 4, QTableWidgetItem(format(np.mean(self.adc_data),'.3f')))
        else: # 以电压形式
            self.tab1_measure.setItem(0, 0, QTableWidgetItem(self.ch_combobox.currentText()))
            # temp = self.unit_suite(np.min(self.adc_data))
            self.tab1_measure.setItem(0, 1, QTableWidgetItem(format(self.unit_suite(np.min(self.adc_data))[0],'.3f')\
                                                             +unit_str[self.unit_suite(np.min(self.adc_data))[1]])) # min
            self.tab1_measure.setItem(0, 2, QTableWidgetItem(format(self.unit_suite(np.max(self.adc_data))[0],'.3f')\
                                                             +unit_str[self.unit_suite(np.max(self.adc_data))[1]]))
            self.tab1_measure.setItem(0, 3, QTableWidgetItem(format(self.unit_suite(np.std(self.adc_data))[0],'.3f')\
                                                             +unit_str[self.unit_suite(np.std(self.adc_data))[1]]))
            self.tab1_measure.setItem(0, 4, QTableWidgetItem(format(self.unit_suite(np.mean(self.adc_data))[0],'.3f')\
                                                             +unit_str[self.unit_suite(np.mean(self.adc_data))[1]]))
        # histogram display
        # 设置bin的边界, 这里为了防止码值颗粒度分的太细，如果是正弦波类型的码值，最多满量程内保持200颗点
        max_bin_number = 100
        bin_range = np.max(self.adc_code)-np.min(self.adc_code)
        print('start bin_range:',bin_range)        
        if (bin_range)>max_bin_number:
            # 实际bin值显示过多，因此需要对bin进行压缩，保持最多200个bin
            print('too much bins')
            bin_gain = float(format(bin_range/max_bin_number,'.1f'))
            bin = np.arange(np.round(np.min(self.adc_code/bin_gain))-1,np.round(np.max(self.adc_code/bin_gain))+3)
            hist,bins = np.histogram(np.round(self.adc_code/bin_gain),bin)
        else:
            bin_gain = 1
            bin = np.arange(np.min(self.adc_code)-1,np.max(self.adc_code)+3)
            hist,bins = np.histogram(self.adc_code,bin)
        print ('end bin_range=',bin)
        barItem = pg.BarGraphItem(x=bins[0:-1]*bin_gain,height=hist,width = 0.9*bin_gain,brush='r')
        self.tab2_plt.clear()
        self.tab2_plt.addItem(barItem)
        self.tab2_measure.setItem(0, 0, QTableWidgetItem(self.ch_combobox.currentText()))
        self.tab2_measure.setItem(0, 1, QTableWidgetItem(format(np.min(self.adc_code),'.0f')+'LSB'))
        self.tab2_measure.setItem(0, 2, QTableWidgetItem(format(np.max(self.adc_code),'.0f')+'LSB'))
        # self.tab2_measure.setItem(0, 3, QTableWidgetItem(format(np.std(self.adc_code),'.2f')+'LSB'))
        noise_offset = np.mean(self.adc_code)
        noise_pow = [(x-noise_offset)**2 for x in self.adc_code]
        rms_pow = np.sqrt(np.mean(noise_pow))
        self.tab2_measure.setItem(0, 3, QTableWidgetItem(format(rms_pow,'.2f')+'LSB'))
        self.tab2_measure.setItem(0, 4, QTableWidgetItem(format(np.mean(self.adc_code),'.2f')+'LSB'))
        self.tab2_measure.setItem(0, 5, QTableWidgetItem(format(np.max(self.adc_code)-np.min(self.adc_code),'.0f')+'LSB'))
        ENOB = np.log2(np.power(2,24)/(rms_pow))
        self.tab2_measure.setItem(0, 6, QTableWidgetItem(format(ENOB,'.2f')+'bit'))
        # fft display
        if self.mode_combobox.currentIndex() : # Fix mode
            fs = int(self.dr_combobox.currentText())
        else:
            fs = int(self.dr_combobox.currentText())/int(len(self.cap_ch_count))
        N = len(self.adc_code)
        fft_window = signal.windows.kaiser(N,8,sym=True)
        data_fft = np.abs(fftpack.fft(self.adc_code*fft_window))/np.sum(fft_window)*2
        data_fft[0]=data_fft[0]/2
        # x_freq = np.arange(len(data))/len(data)
        # x_freq_half = x_freq[range(int(len(data)/2))]*fs
        # data_fft_abs = 20*np.log10(data_fft)-np.max(20*np.log10(data_fft)) # 最终显示的结果将和初始的幅值对应上；8192幅值的信号此处功率为 20*log(8192)≈78dB；
        # y_fft_half = data_fft_abs[range(int(len(data_fft)/2))]
        # self.tab3_plt.clear()
        # self.tab3_plt.plot(x_freq_half,y_fft_half,pen='r')
        [dBFS,SINAD,SNR,THD,SFDR] = self.fft_analysis(self.adc_code,fs)
        self.tab3_measure.setItem(0, 0, QTableWidgetItem(self.ch_combobox.currentText()))
        self.tab3_measure.setItem(0, 1, QTableWidgetItem(format(dBFS,'.2f')+'dB'))
        self.tab3_measure.setItem(0, 2, QTableWidgetItem(format(SINAD,'.2f')+'dB'))
        self.tab3_measure.setItem(0, 3, QTableWidgetItem(format(SNR,'.2f')+'dB'))
        self.tab3_measure.setItem(0, 4, QTableWidgetItem(format(THD,'.2f')+'dB'))
        self.tab3_measure.setItem(0, 5, QTableWidgetItem(format(SFDR,'.2f')+'dB'))

    def fft_analysis(self,data,fs):
        # 下一步要根据不同的长度数据去自定义cut的程度
        x_freq = np.arange(len(data))/len(data)
        x_freq_half = x_freq[range(int(len(data)/2))]*fs
        resolution = 24
        clip = 0.01    # INL DNL 误差排除比例
        sideBin = int(np.ceil(60/7000*len(data)))    # 信号谱线宽
        sideBin_thd = int(np.ceil(20/7000*len(data)))    # 信号谱线宽
        lowCut = int(np.ceil(60/7000*len(data)))     # 去除低频数据点数
        harmonic = 7  # THD 计算谐波数
        N = len(data)
        Nd2 = int(np.floor(N/2))
        window = signal.windows.kaiser(N,8,sym=True)
        # window = np.ones((N,))
        data_kaiser = data * window
        fdata = np.abs(fftpack.fft(data_kaiser))/np.sum(window)*2
        fdata[0] = fdata[0]/2  # 这里的fdata在信号上的幅值等于输入正弦信号的幅值 A
        fdata_half = fdata[range(int(len(fdata)/2))]
        fdata_half[0:lowCut-1] = fdata_half[lowCut]
        fdata_half_log = 20*np.log10(fdata_half)-np.max(20*np.log10(fdata_half))
        self.tab3_plt.clear()
        self.tab3_plt.plot(x_freq_half,fdata_half_log,pen='r')
        if lowCut<len(fdata):
            sig_max = np.max(fdata[lowCut:]) # 这里最大值应该是 2^23
        else:
            print('Too Few Sample Point!')
            sig_max = np.max(fdata[1:])
        dBFS = 20*np.log10(sig_max/np.power(2,resolution-1))
        spec = np.power(fdata,2)
        spec = spec[0:Nd2-1]
        spec = spec/(N^2)*resolution
        if lowCut<len(spec) and lowCut>1:
            spec[0:lowCut-1] = spec[lowCut]
        else:
            print('Too Few Sample Point!')
            spec[0:1] = spec[1]
        # 找到输入信号基频        
        bin = list(spec).index(np.max(spec))
        bin_list = np.arange(int(np.max([bin-sideBin,1])),int(np.min([bin+sideBin,Nd2])),1)
        sig = np.sum(spec[bin_list])
        thd1=0
        pwr = 10*np.log10(sig)
        for i in np.arange(2,harmonic):
            b=self.fclip((bin-1)*i,N)
            thd_bin_list = np.arange(int(np.max([b+1-sideBin_thd,1])),int(np.min([b+1+sideBin_thd,Nd2])),1)
            thd1 = thd1+np.sum(spec[thd_bin_list])
        spec[np.arange(np.max([bin-sideBin,1]),np.min([bin+sideBin,Nd2]))] = 0
        thdn=np.sum(spec)
        sbin = list(spec).index(np.max(spec))
        spur = np.sum(spec[np.arange(np.max([sbin-sideBin_thd,1]),np.min([sbin+sideBin_thd,Nd2]))])
        noi=thdn-thd1
        SINAD = 10*np.log10(sig/thdn)
        SNR = 10*np.log10(sig/noi)
        THD = 10*np.log10(thd1/sig)
        SFDR = 10*np.log10(sig/spur)
        return [dBFS,SINAD,SNR,THD,SFDR]
        
    def fclip(self,J,N):
        if np.mod(np.floor(J/N*2),2)==0:
            bin=J-np.floor(J/N)*N
        else:
            bin=N-J+np.floor(J/N)*N
        return bin
    
    def ch_reference(self):
        self.checkbox_clear_flag = 1 # 表示正在对界面进行更改，不要触发connect函数
        self.ch_reference_flag = 1 # 表示正在对ch选择界面进行更改，不要重新触发绘图函数
        self.ch_combobox.clear()
        self.cap_ch_count = []
        for j in range(3):
            for i in range(8):
                if (self.dev0.config[3+j]>>i)&0x01 == 0x01:
                    self.ch_combobox.addItem(self.dev0.channel_name[j*8+i])
                    self.cap_ch_count.append(j*8+i) # 将通道序号标记好
                    getattr(self, 'channel'+str(j*8+i)).setChecked(True)
                else:
                    getattr(self, 'channel'+str(j*8+i)).setChecked(False)
        if self.dev0.config[6]&0x01 == 0x01:
            self.ch_combobox.addItem('OFFSET')
            getattr(self, 'channel'+str(24)).setChecked(True)
            self.cap_ch_count.append(24)
        else:
            getattr(self, 'channel'+str(24)).setChecked(False)
        for i in range(4):
            if (self.dev0.config[6]>>(2+i))&0x01 == 0x01:
                self.ch_combobox.addItem(self.dev0.channel_name[25+i])
                getattr(self, 'channel'+str(25+i)).setChecked(True)
                self.cap_ch_count.append(26+i)
            else:
                getattr(self, 'channel'+str(25+i)).setChecked(False)
        if len(self.cap_ch_count) == 0: # 没有选取任何一个通道
            self.ch_combobox.addItem(self.dev0.channel_name[0]) # 那么选取通道1
            self.cap_ch_count.append(0)
        self.checkbox_clear_flag = 0
        self.ch_reference_flag = 0


    def sin_wave(self, A, f, fs, phi, n):
        '''
        :params A:    振幅
        :params f:    信号频率
        :params fs:   采样频率
        :params phi:  相位
        :params n:    数据长度
        '''
        # 若时间序列长度为 t=1s, 
        # 采样频率 fs=1000 Hz, 则采样时间间隔 Ts=1/fs=0.001s
        # 对于时间序列采样点个数为 n=t/Ts=1/0.001=1000, 即有1000个点,每个点间隔为 Ts
        Ts = 1/fs
        n = np.arange(n)
        y = A*np.sin(2*np.pi*f*n*Ts + phi*(np.pi/180))
        y_code = np.round(y)
        y_normal = np.round(np.random.normal(size=16384)*10)
        return y_code

    def UI_test(self): # 测试用脚本
        self.ser_port_read(self.dev0)
        self.ser_combox.setCurrentIndex(1)
        self.ser_port_select(self.dev0)
        self.ser_connect(self.dev0)
        self.mode_combobox.setCurrentIndex(1)
        self.channel0.setChecked(1)
        self.sample_depth.setCurrentIndex(1)


def main():
    app = QApplication(sys.argv)
    gui = MainUi()
    gui.show()
    # gui.reset_dev()
    # gui.UI_test()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
