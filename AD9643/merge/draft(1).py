from Serial_class import SerialAchieve
import numpy as np
import time



class cm1348_dev:
    
   
    def __init__(self):
        self.regname = ['SPI', 'CHIPID', 'CHIPGRADE', 'CHANNELINDEX', 'TRANSFER', 'POWERMODES', 'GLOBALCLOCK', 'CLOCKDIVIDE', 'TESTMODE', 'OFFSETADJUST','OUTPUTMODE','OUTPUTADJUST','CLOCKPHASE','DCOOUTPUT','INPUTSPAN','USER1','USER2','USER3','USER4','USER5','USER6','USER7','USER8','SYNC']

        self.regaddr = [0x00,0x01,0x02,0x05,0xFF,0x08,0x09,0x0B,0x0D,0x10,0x14,0x15,0x16,0x17,0x18,0x19,0x1A,0x1B,0x1C,0x1D,0x1E,0x1F,0x20,0x3A]
        self.reg_mode = ['R/W', 'R', 'R', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W','R/W']
        self.config_default = [0x18, 0x82, None, 0x03, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,0x05,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
        self.connect_status = 0
        self.busy_status = 0
        self.sample_num = 7000
        self.myserial = SerialAchieve()

    def crc(self,command_reg_write:list):
        crc = 0
    
        for byte in command_reg_write:
            crc ^=byte
            #发送包生成crc
        return crc
    def crc2(self,command_rev:list):
        crc =0
        for i in range(0,len(command_rev)-1):
            crc ^=command_rev[i]
            #接受包生成crc
        return crc
  
    def cgf_write(self, addr, para):
        self.busy_status = 1
        # while(1):  #这套清空串口缓存的方法运行效率太低，导致界面过于卡顿
        #     rx = self.myserial.ser.read()
        #     if rx:
        #         continue
        #     else:
        #         break        
        command_reg_write = [0xAA, 0x1B, 0x00, 0x02,0x00,addr,para]
        #没有crc的命令
        command_reg_Write =[0xAA, 0x1B, 0x00, 0x02,0x00,addr,para,self.crc(command_reg_write)]
        #给命令生成一个crc进去
        command_rev = [0x55, 0x1B,0x00,0x01,0x00,0x00]
        
        rx = []
        self.myserial.ser.write(command_reg_Write)
        for i in range(0, 6):
            rx.append(self.myserial.ser.read())
        if rx:
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
        for i in range(0, 6):
            rx.append(self.myserial.ser.read())
        if rx:
            rx_asc_array = np.frombuffer(np.array(rx), dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            if (rx_asc[0] == command_rev[0])and(rx_asc[1] == command_rev[1])and(rx_asc[2] == command_rev[2])and(rx_asc[3] == command_rev[3])and(rx_asc[4] == command_rev[4]):
                print(f'The data is {rx_asc[5]}')
            else:
                print('wrong received command')
        else:
            print('Wrong')
        self.busy_status = 0
        return self
    # def cgf_read(self, addr):
    #     self.busy_status = 1
    #     while(1):
    #         rx = self.myserial.ser.read()
    #         if rx:
    #             continue
    #         else:
    #             break
    #     data = 0
    #     command_reg_write = [0x55, 0xAA, 0x02, addr, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]
    #     command_rev = [0x55, 0xAA, 0x20, addr, data, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]
    #     rx = []
    #     self.myserial.ser.write(command_reg_write)
    #     for i in range(0, 11):
    #         rx.append(self.myserial.ser.read())
    #     if rx:
    #         rx_asc_array = np.frombuffer(np.array(rx), dtype=np.uint8)
    #         rx_asc = rx_asc_array.tolist()
    #         if rx_asc == command_rev:
    #             print('successfully config the device', addr, 'register')
    #         else:
    #             print('wrong received command')
    #     else:
    #         print('no data back!')
    #     self.busy_status = 0
    #     return self

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
        
        self.busy_status = 0
        return self
    def sample(self):
        self.busy_status =1
        
        command_usermode =[0xAA,0x01,0x02,0x01,0x00,0x00]
        command_userMode =[0xAA,0x01,0x02,0x01,0x00,0x00,self.crc(command_usermode)]
        command_rev=[0x55,0x01,0x02,0x01,0x00,0x00]
        
        self.myserial.ser.write(command_userMode)
        rx=[]
        for i in range (0,6):
            rx.append(self.myserial.ser.read())
        if rx:
            rx_asc_array = np.frombuffer(rx, dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            if rx_asc == command_rev:
                print('Successfully set user mode')
            else:
                print('wrong')
        else:
            print('no data back!')
        self.cgf_write(self,0x17,0x8E)
        self.cgf_write(self,0xFF,0x01)
        self.busy_status = 0
        return self
    def dataCollect(self):
        self.busy_status = 1
        sample_Length=0x01 #具体采样长度不知道
        command_sample =[0xAA,0x35,0x01,0x04,0x00,sample_Length,0x00,0x00,0x00]
        command_Sample =[0xAA,0x35,0x01,0x04,0x00,sample_Length,0x00,0x00,0x00,self.crc(command_sample)]
        command_Rev=[0x55,0x35,0x01,0x01,0x00,0x00]
        time.sleep(1)
        self.myserial.ser.write(command_Sample)
        Rx=[]
        for i in range(0,6):
            Rx.append(self.myserial.ser.read())
        if Rx:
            Rx_asc_array = np.frombuffer(Rx, dtype=np.uint8)
            Rx_asc = Rx_asc_array.tolist()
            if Rx_asc == command_rev:
                print('Successfully sample')
            else:
                print('wrong')
        else:
            print('no data back!')
        
        
        command_collect=[0xAA,0x35,0x07,0x04,0x00,sample_Length,0x00,0x00,0x00]
        command_Collect=[0xAA,0x35,0x07,0x04,0x00,sample_Length,self.crc1(command_collect)]
        command_rev =[0x55,0x35,0x07,0x01,0x00,0x00]

        self.myserial.ser.write(command_Collect)
        rx=[]
        for i in range(0,6):
            rx.append(self.myserial.ser.read())
        if rx:
            rx_asc_array = np.frombuffer(rx, dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            if rx_asc == command_rev:
                print('Successfully transmit')
            else:
                print('wrong')
        else:
            print('no data back!')
        #接下来就是用upd类通信了
        self.busy_status = 0
        return self
    # def __init__(self):
    #     self.regname = ['SPI', 'CHIPID', 'CHIPGRADE', 'CHANNELINDEX', 'TRANSFER', 'POWERMODES', 'GLOBALCLOCK', 'CLOCKDIVIDE', 'TESTMODE', 'OFFSETADJUST','OUTPUTMODE','OUTPUTADJUST','CLOCKPHASE','DCOOUTPUT','INPUTSPAN','SYNC']

    #     self.regaddr = [0x00,0x01,0x02,0x05,0xFF,0x08,0x09,0x0B,0x0D,0x10,0x14,0x15,0x16,0x17,0x18,0x3A]
    #     self.reg_mode = ['R/W', 'R', 'R', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W', 'R/W','R/W','R/W','R/W','R/W','R/W','R/W']
    #     self.config_default = [0x18, 0x82, None, 0x03, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,0x05,0x01,0x00,0x00,0x00]
    #     self.connect_status = 0
    #     self.busy_status = 0
    #     self.sample_num = 7000
    #     self.myserial = SerialAchieve()
    def flash(self):
        for i in range(0,24):
            self.cgf_write(self.regaddr[i],self.config_default[i])
        
        return self
    #刷新每个寄存器的默认值

cm1348 =cm1348_dev()
cm1348.__init__()
cm1348.cgf_write(0x00,0x01)
cm1348.cgf_read(0x00)
    
    
