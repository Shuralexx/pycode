from Serial_class import SerialAchieve
import numpy as np
import time
import serial
import serial.tools.list_ports


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
    def __init__(self): #初始化方法
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

    def cgf_write(self, addr, para):
        self.busy_status = 1
        # while(1):  #这套清空串口缓存的方法运行效率太低，导致界面过于卡顿
        #     rx = self.myserial.ser.read()
        #     if rx:
        #         continue
        #     else:
        #         break
        self.config[addr] = para
        command_reg_write = [0x55, 0xAA, 0x01, addr, para, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]#写寄存器的协议命令数组，包含头部、命令类型、寄存器地址、参数和结尾标志。
        command_rev = [0x55, 0xAA, 0x10, addr, para, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]
        rx = []
        # 读取返回的数据并进行检查
        self.myserial.ser.write(command_reg_write)#发送命令到设备
        for i in range(0, 11):
            rx.append(self.myserial.ser.read())
            # 检查返回的数据是否正确
        if rx:
            rx_asc_array = np.frombuffer(np.array(rx), dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            if rx_asc == command_rev:
                print('successfully config the device', addr, 'register')
            else:
                print('wrong received command')
        else:
            print('no data back!')
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
        data = 0
        command_reg_write = [0x55, 0xAA, 0x02, addr, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]
        command_rev = [0x55, 0xAA, 0x20, addr, data, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]
        rx = []
        self.myserial.ser.write(command_reg_write)#通过串口发送命令，然后读取设备返回的数据，并进行校验
        for i in range(0, 11):
            rx.append(self.myserial.ser.read())
        if rx:
            rx_asc_array = np.frombuffer(np.array(rx), dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            if rx_asc == command_rev:
                print('successfully config the device', addr, 'register')
            else:
                print('wrong received command')
        else:
            print('no data back!')
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
        command_handshake = [0x55, 0xAA, 0x0F, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]
        command_rev = [0x55, 0xAA, 0xF0, 0x01, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]
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

    def sample_num_set(self, deep):
        self.busy_status = 1
        command_num_set = [0x55, 0xAA, 0x03, deep, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]
        self.sample_num = np.power(2, deep)
        if self.sample_num >7000:
            self.sample_num = 7000
        command_rev = [0x55, 0xAA, 0x30, round(self.sample_num / 16777216), round((self.sample_num % 16777216) / 65536),
                       round((self.sample_num % 65536) / 256), self.sample_num % 256, 0x65, 0x6E, 0x64, 0x45, 0x4E,
                       0x44]
        self.myserial.ser.write(command_num_set)

        rx = self.myserial.ser.readline()
        if rx:
            rx_asc_array = np.frombuffer(rx, dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            if rx_asc == command_rev:
                print('successfully config the sample depth =', deep)
            else:
                print('wrong received command')
        else:
            print('no data back!')
        self.busy_status = 0
        return self
    
    # 增加一个采样通道配置的代码：
    # 主要用来将通道配置配置进ADC的相应寄存器，并且用来统计通道数

    def get_sample(self):
        self.busy_status = 1
        # while(1):
        #     rx = self.myserial.ser.read()
        #     if rx:
        #         continue
        #     else:
        #         break
        self.rx_status.clear()
        self.rx_data.clear()        
        command_get_sample = [0x55, 0xAA, 0xE1, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]
        command_rev = [0x55, 0xAA, 0x1E, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]
        self.myserial.ser.write(command_get_sample)
        rx = []
        rev_length = 9 + self.sample_num*4+5
        fclk = 16e6
        if self.config[0] & self.MUXMOD_MASK == self.MUXMOD_MASK: # fix mode
            data_rate = fclk/128/(np.power(4,(3-self.config[1] & self.DR_MASK))+((self.config[0]&self.CHOP_MASK)>>2)*(4.265625+self.TD[(self.config[1]&self.TD_MASK)>>4]))/np.power(2,(self.config[0]&self.CHOP_MASK)>>2)
        else: # auto scan mode
            data_rate = fclk/128/(np.power(4,(3-self.config[1]&0x03))+4.265625+self.TD[(self.config[1]&self.TD_MASK)>>4])/np.power(2,(self.config[0]&self.CHOP_MASK)>>2)
        delay_time = self.sample_num/data_rate
        time.sleep(delay_time)
        for i in range(0, rev_length):
            rx.append(self.myserial.ser.read())
        if np.frombuffer(np.array(rx[-4:]), dtype=np.uint8).tolist()==[0xff,0xff,0xff,0xff]:
            if np.frombuffer(np.array(rx[9]), dtype=np.uint8).tolist() == [0xff]:
                rx_asc_array = np.frombuffer(np.array(rx[0:9]), dtype=np.uint8)
                rx_asc = rx_asc_array.tolist()
                if rx_asc == command_rev:
                    print('successfully receive the data')
                    self.rx_temp = np.frombuffer(np.array(rx[10:-4]), dtype=np.uint8)
                    for i in range(0,self.sample_num):
                        self.rx_status.append(self.rx_temp[i*4])
                        temp = self.rx_temp[i*4+1]*65536+self.rx_temp[i*4+2]*256+self.rx_temp[i*4+3]
                        if temp>8388607:
                            temp = -1*(16777215-temp)
                        self.rx_data.append(temp)
                                                                     
                    print(self.rx_data)                    
                else:
                    print('wrong received command')
            else:
                print('wrong start word:',str(rx[9]))           
        else:
            print('wrong end words:',str(rx[-4:]))
        self.busy_status = 0
        return self

    def config_write(self, config):#配置设备寄存器，并解析配置参数
        self.busy_status = 1
        # while(1):
        #     rx = self.myserial.ser.read()
        #     if rx:
        #         continue
        #     else:
        #         break
        config0 = round(config / 256)
        config1 = config % 256              #把 config 拆分为高8位和低8位，分别用于两个寄存器
        #通过掩码和位移操作，从 config0 提取各个功能位（如 CHOP、STAT、CLKENB 等），这些通常代表硬件的不同配置选项。
        self.CHOP = (config0 & self.CHOP_MASK) >> self.CHOP_POS  #先用掩码取出相关位，再右移到最低位
        # Chopper Enable）控制斩波稳零功能。作用：开启后可降低低频噪声和失调，提高精度，适合高精度测量。0：关闭斩波；1：开启斩波
        self.STAT = (config0 & self.STAT_MASK) >> self.STAT_POS
        #Status Output Enable）控制状态输出引脚是否使能。作用：用于外部监控 ADC 状态，调试或同步时用。0：禁用状态输出；1：使能状态输出
        self.CLKENB = (config0 & self.CLKENB_MASK) >> self.CLKENB_POS
        #Clock Enable）控制时钟输出引脚是否使能。作用：用于外部时钟同步或其他用途。0：禁用时钟输出；1：使能时钟输出
        self.BYPAS = (config0 & self.BYPAS_MASK) >> self.BYPAS_POS
        #Bypass MUXOUT 控制 MUXOUT 是否旁路。作用：决定模拟多路复用器输出是否直接连接到 ADC 输入，影响信号路径。0：正常模式；1：旁路 MUXOUT
        self.MUXMOD = (config0 & self.MUXMOD_MASK) >> self.MUXMOD_POS  #MUXMOD位用于采集模式，=0 Auto-scan, =1 Fix channel
        self.SPIRST = (config0 & self.SPIRST_MASK) >> self.SPIRST_POS
        #SPI Reset）控制 SPI 接口复位。作用：用于初始化或复位 SPI 接口，确保通信正常。0：正常工作；1：复位 SPI 接口
        print(self.CHOP)
        self.cgf_write(0x00, config0)#分别把高低8位写入设备的两个寄存器
        self.cgf_write(0x01, config1)
        self.busy_status = 0
        return self
    
    def dev_reset(self):
        self.busy_status = 1
        # while(1): 
        #     rx = self.myserial.ser.read()
        #     if rx:
        #         continue
        #     else:
        #         break   
        command_reset = [0x55, 0xAA, 0x0E, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]
        command_rev = [0x55, 0xAA, 0xE0, 0x01, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]
        self.myserial.ser.write(command_reset)
        rx = self.myserial.ser.readline()
        if rx:
            rx_asc_array = np.frombuffer(rx, dtype=np.uint8)
            rx_asc = rx_asc_array.tolist()
            if rx_asc == command_rev:
                print('success reset device, device connected!')
                self.config = self.config_default
            else:
                print('wrong received command')
        else:
            print('no data back!')
        self.busy_status = 0
        return self


def main():
    cm1348_dev01 = cm1348_dev()# 创建设备实例
    cm1348_dev01.myserial.port_get()# 获取可用串口列表
    for port_num in cm1348_dev01.myserial.port_list:
        print(port_num.description)# 打印所有串口的描述信息
    cm1348_dev01.myserial.port = cm1348_dev01.myserial.port_list[1].device
    print(cm1348_dev01.myserial.port)# 打印选中的串口
    cm1348_dev01.myserial.open_port()# 打开串口连接
    cm1348_dev01 = cm1348_dev01.hand_shake() # 握手验证设备连接
    cm1348_dev01 = cm1348_dev01.sample_num_set(4)# 设置采样点数为2^4=16
    cm1348_dev01 = cm1348_dev01.get_sample()# 获取采样数据1
    cm1348_dev01 = cm1348_dev01.get_sample()# 获取采样数据2
    cm1348_dev01 = cm1348_dev01.config_write(0x0A01)# 配置寄存器CONFIG0=0x0A, CONFIG1=0x01
    print(cm1348_dev01.config)# 打印配置寄存器0的值
    cm1348_dev01 = cm1348_dev01.config_write(0x0E01)# 修改配置为CONFIG0=0x0E, CONFIG1=0x01
    print(cm1348_dev01.config)# 打印配置寄存器1的值
    cm1348_dev01.myserial.close_port()# 关闭串口连接


if __name__ == '__main__':#当脚本作为主程序直接运行时，执行 main()；作为模块导入时，不执行
    main()
