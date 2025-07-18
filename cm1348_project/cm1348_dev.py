"""Minimal driver for the CM1348 device.

This simplified version only keeps the ability to initialise the
device and read/write the ten user accessible registers.  It is meant
for debugging purposes and therefore strips all the data acquisition
logic present in the original implementation.
"""

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
        self.myserial = SerialAchieve()
        self.show_registers()

    def cgf_write(self, addr: int, value: int):
        """Write one register.

        Parameters
        ----------
        addr : int
            Register address in the range 0x00-0x09.
        value : int
            Value to write.
        """
        self.busy_status = 1
        self.config[addr] = value
        command = [0x55, 0xAA, 0x01, addr, value, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]
        self.myserial.ser.write(command)
        reply = [self.myserial.ser.read() for _ in range(11)]
        if reply:
            data = np.frombuffer(np.array(reply), dtype=np.uint8).tolist()
            if data != [0x55, 0xAA, 0x10, addr, value, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]:
                print("unexpected write response", data)
        else:
            print("no response on write")
        idx = self.regaddr.index(addr)
        print(f"Wrote {self.regname[idx]}(0x{addr:02X}) = 0x{value:02X}")
        self.busy_status = 0
        return self

    def cgf_read(self, addr: int) -> int:
        """Read one register and return its value."""
        self.busy_status = 1
        # clear input buffer
        while self.myserial.ser.read():
            continue

        command = [0x55, 0xAA, 0x02, addr, 0x65, 0x6E, 0x64, 0x45, 0x4E, 0x44]
        self.myserial.ser.write(command)
        reply = [self.myserial.ser.read() for _ in range(11)]

        value = None
        if reply:
            data = np.frombuffer(np.array(reply), dtype=np.uint8).tolist()
            if len(data) == 11 and data[0:3] == [0x55, 0xAA, 0x20] and data[3] == addr:
                value = data[4]
                self.config[addr] = value
            else:
                print("unexpected read response", data)
        else:
            print("no response on read")

        if value is not None:
            idx = self.regaddr.index(addr)
            print(f"Read {self.regname[idx]}(0x{addr:02X}) = 0x{value:02X}")

        self.busy_status = 0
        return value

    def show_registers(self):
        """Print the value of each register stored in ``self.config``."""
        for name, addr in zip(self.regname, self.regaddr):
            val = self.config[addr]
            print(f"{name} (0x{addr:02X}) = 0x{val:02X}")
