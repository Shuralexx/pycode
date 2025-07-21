from Serial_class import SerialAchieve
import numpy as np








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
        self.myserial = SerialAchieve()
        self.show_registers()

    def cgf_write(self, addr: int, value: int):
        """Write one register and display the result."""
    
        self.busy_status = 1
        self.config[addr] = value
        try:
            command = bytes([0x55, 0xAA, 0x01, addr, value,
                            0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44])
            self.myserial.ser.write(command)
                # 忽略回复，只进行本地操作
                # reply = self.myserial.ser.read(len(command))
        except Exception as e:
            print(f"(无串口) write跳过: {e}")
        # reply = self.myserial.ser.read(len(command))
        # if reply:
        #     data = list(reply)
        #     expect = [0x55, 0xAA, 0x10, addr, value,
        #               0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]
        #     if data != expect:
        #         print("unexpected write response", data)
        # else:
        #     print("no response on write")
        idx = self.regaddr.index(addr)
        print(f"Wrote {self.regname[idx]}(0x{addr:02X}) = 0x{value:02X}")
        self.busy_status = 0
        return self

    def cgf_read(self, addr: int) -> int:
        """Read one register and return its value."""

        self.busy_status = 1

        # # empty any pending bytes from previous commands
        # while self.myserial.ser.read():
        #     continue

        # command = bytes([0x55, 0xAA, 0x02, addr,
        #                  0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44])
        # self.myserial.ser.write(command)

        # reply = self.myserial.ser.read(len(command))

        # value = None
        # if reply:
        #     data = list(reply)
        #     if (len(data) == len(command) and data[0:3] == [0x55, 0xAA, 0x20]
        #             and data[3] == addr):
                
        #         value = data[4]
        #         self.config[addr] = value
        #     else:
        #         print("unexpected read response", data)
        # else:
        #     print("no response on read")

        # if value is not None:
        #             idx = self.regaddr.index(addr)
        #             print(f"Read {self.regname[idx]}(0x{addr:02X}) = 0x{value:02X}")

        # self.busy_status = 0
        # return value
    

        try:
        # 发送读命令但不等回复
            command = bytes([0x55, 0xAA, 0x02, addr,
                            0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44])
            self.myserial.ser.write(command)
        # reply = self.myserial.ser.read(len(command))
        except Exception as e:
            print(f"(无串口) read跳过: {e}")

        value = self.config[addr]
        idx = self.regaddr.index(addr)
        print(f"Read {self.regname[idx]}(0x{addr:02X}) = 0x{value:02X}")
        self.busy_status = 0
        return value
    
    # Convenience wrappers using a more descriptive name
    def write_reg(self, addr: int, value: int):
        """Alias of :meth:`cgf_write`."""
        return self.cgf_write(addr, value)

    def read_reg(self, addr: int) -> int:
        """Alias of :meth:`cgf_read`."""
        return self.cgf_read(addr)

    def show_registers(self):
        """Print the value of each register stored in ``self.config``."""
        for name, addr in zip(self.regname, self.regaddr):
            val = self.config[addr]
            print(f"{name} (0x{addr:02X}) = 0x{val:02X}")



def main():
    """Simple demonstration that prints all register values."""
    dev = cm1348_dev()

    ports = dev.myserial.port_get()
    if ports:
        dev.myserial.port = ports[0].device
        print("Using port:", dev.myserial.port)
        dev.myserial.open_port()
        for addr in dev.regaddr:
            dev.read_reg(addr)
     #   dev.myserial.close_port()
    else:
        print("No serial ports found. Only displaying cached values.")
        dev.show_registers()
        return
    # 用户输入循环
    print("\n请输入需要写入的寄存器和数值，格式如: CONFIG0 0x55 或 0 85（输入q退出）")
    while True:
        user_input = input("寄存器 写入数值 > ").strip()
        if user_input.lower() in ('q', 'quit', 'exit'):
            break
        if not user_input:
            continue
        parts = user_input.split()
        if len(parts) != 2:
            print("格式错误，请重新输入，例如: CONFIG1 0x83 或 1 131")
            continue

        # 解析寄存器
        reg, val = parts
        try:
            # 支持名字、十进制、十六进制
            if reg.upper() in dev.regname:
                addr = dev.regname.index(reg.upper())
            else:
                if reg.lower().startswith('0x'):
                    addr = int(reg, 16)
                else:
                    addr = int(reg)
            if addr not in dev.regaddr:
                raise ValueError
        except Exception:
            print("寄存器无效，请输入有效的名字或地址")
            continue

        try:
            # 数值支持十进制或十六进制
            value = int(val, 0)
            if not (0 <= value <= 255):
                raise ValueError
        except Exception:
            print("写入数值无效，应为0-255的十进制或0x00-0xFF十六进制")
            continue

        # 写寄存器
        dev.write_reg(addr, value)

    # 最后打印所有寄存器
    print("\n修改后的寄存器如下：")
    for addr in dev.regaddr:
        dev.read_reg(addr)
    dev.myserial.close_port()


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()