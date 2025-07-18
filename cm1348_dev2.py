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