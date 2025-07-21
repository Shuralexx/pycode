from Serial_class import SerialAchieve
import numpy as np
import time



class cm1348_dev:
    reg_description = ['CONFIG0: Configuration Register 0\r\n 0 | SPIRST | MUXMOD | BYPAS | CLKENB | CHOP | STAT | 0 \r\n\
配置寄存器0',
    'CONFIG1: Configuration Register 1\r\n IDLMOD | DLY2 | DLY1 | DLY0 | SBCS1 | SBCS0 | DRATE1 | DRATE0 \r\n\
IDLMOD: 0-Select Standby Mode; 1-Select Sleep Mode\r\n\
DLY[2:0]: Set the Switch Time Delay\r\n\
SBCS[1:0]: 0-Sensor Bias Current Source Off(default); 1-1.5uA Source; 3-24uA Source\r\n\
DRATE[1:0]: Set the Data Rate, the actual data rate also depend on the MUXMOD bit',
    'MUXSCH: Channel configuration register in fixed channel mode\r\n Note that the AINCOM input and the internal system The ADS1258 provides 16 analog inputs, which can registers cannot be referenced in this mode', 
    'MUXDIF:\r\n This Register selects the input channels of multiplexer to be used in the Auto-Scan mode', 
    'MUXSG0:\r\n This Register selects the input channels of multiplexer to be used in the Auto-Scan mode\r\nAll Single-Ended inputs are measured with respect to the AINCOM input\r\nAINCOM may be set to any level within ±100mV of the analog supply range', 
    'MUXSG1:\r\n This Register selects the input channels of multiplexer to be used in the Auto-Scan mode\r\nAll Single-Ended inputs are measured with respect to the AINCOM input\r\nAINCOM may be set to any level within ±100mV of the analog supply range', 
    'SYSRED:\r\n System reading for diagnostics, these channels could only be used in Auto-Scan mode', 
    'GPIOC:\r\nThis register configures the GPIO pins as inputs or as outputs.\r\nNote that the default configurations of the port pins are inputs and as such they should not be left floating.', 
    'GPIOD:\r\nThis register is used to read and write data to the GPIO port pins.\r\nWhen reading this register, the data returned corresponds to the state of the GPIO external pins\r\n\
As inputs, a write to the GPIOD has no effect.\r\nAs outputs, a write to the GPIOD sets the output value.', 
    'ID:\r\nFactory programmed ID bits, Read-only.']
    channel_name = ['DIFF0(AIN0-1)','DIFF1(AIN2-3)','DIFF2(AIN4-5)','DIFF3(AIN6-7)','DIFF4(AIN8-9)','DIFF5(AIN10-11)','DIFF6(AIN12-13)','DIFF7(AIN14-15)',\
    'SE0(AIN0)','SE1(AIN1)','SE2(AIN2)','SE3(AIN3)','SE4(AIN4)','SE5(AIN5)','SE6(AIN6)','SE7(AIN7)','SE8(AIN8)','SE9(AIN9)','SE10(AIN10)','SE11(AIN11)','SE12(AIN12)','SE13(AIN13)','SE14(AIN14)','SE15(AIN15)',\
    'OFFSET','AVDD-AVSS','Temperature','Gain','REF']



    def __init__(self):
        self.SPIRST = 0
        self.MUXMOD = 0
        self.BYPAS = 0
        self.CLKENB = 1
        self.CHOP = 0
        self.STAT = 1
        self.STAT_POS = 1
        self.CHOP_POS = 2
        self.CLKENB_POS = 3
        self.BYPAS_POS = 4
        self.MUXMOD_POS = 5
        self.SPIRST_POS = 6
        self.STAT_MASK = 0x02
        self.CHOP_MASK = 0x04
        self.CLKENB_MASK = 0x08
        self.BYPAS_MASK = 0x10
        self.MUXMOD_MASK = 0x20
        self.SPIRST_MASK = 0x40
        self.DR_MASK = 0x03
        self.TD_MASK = 0x70
        self.rx_data = []
        self.rx_status = []
        self.regname = ['CONFIG0', 'CONFIG1', 'MUXSCH', 'MUXDIF', 'MUXSG0', 'MUXSG1', 'SYSRED', 'GPIOC', 'GPIOD', 'ID']
        self.regaddr = [0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09]
        self.reg_mode = ['R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R']
        self.TD = [0,8,16,32,64,128,256,384]
        self.config = [0x0A, 0x83, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0x00, 0x8b]  # ADC 当前寄存器值
        self.config_default = [0x0A, 0x83, 0x00, 0x00, 0xff, 0xff, 0x00, 0xff, 0x00, 0x8b]  # ADC 内部默认寄存器配置
        self.connect_status = 0
        self.busy_status = 0
        self.deep = 13
        self.sample_num = 7000
        self.myserial = SerialAchieve()

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





    def cgf_write(self, addr, para):
        self.busy_status = 1
        # while(1):  #这套清空串口缓存的方法运行效率太低，导致界面过于卡顿
        #     rx = self.myserial.ser.read()
        #     if rx:
        #         continue
        #     else:
        #         break
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

    def cgf_read(self, addr):
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

    def hand_shake(self):
        self.busy_status = 1
        # while(1):
        #     rx = self.myserial.ser.read()
        #     if rx:
        #         continue
        #     else:
        #         break 
        command_handshake = [0xAA,0xFE,0x00,0x01,0x00,0x00,0x55]
        command_rev = [0x55,0xFE,0x00,0x15,0x00,0x43,0x4D,0x33,0x34,0x33,0x32,0x5F,0x44,0x45,0x4D,0x4F,0x5f,0x56,0x30,0x31,0xE2]
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
    def udp_Connect(self):
        self.busy_status = 1
        # while(1):
        #     rx = self.myserial.ser.read()
        #     if rx:
        #         continue
        #     else:
        #         break 
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