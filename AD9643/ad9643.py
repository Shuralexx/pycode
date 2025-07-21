from Serial_class import SerialAchieve
import numpy as np  


class ad9643:
    def __init__(self):
        self.busy_status = 0
        self.myserial = SerialAchieve()
        
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
    

    def ad9643_write_reg(self, addr, value):
        """
        向ad9643指定寄存器地址写入数据
        :param addr: 1字节，寄存器地址
        :param value: 1字节，要写入的数据
        """
        self.busy_status = 1
        # ad9643写寄存器协议：[cmd1, cmd2, data]
        command = [0x1B, 0x00, addr, value]
        # 发送命令
        self.myserial.ser.write(bytearray(command))
        # 读取返回值，期望返回0x00
        ret = self.myserial.ser.read(1)
        if ret and ret[0] == 0x00:
            print(f"成功写入ad9643寄存器0x{addr:02X}, 数据0x{value:02X}")
        else:
            print(f"写入ad9643寄存器失败，返回：{ret.hex() if ret else '无返回'}")
        self.busy_status = 0


    def ad9643_read_reg(self, addr):
        """
        读取ad9643指定寄存器的值
        :param addr: 1字节，寄存器地址
        :return: 读到的数据值
        """
        self.busy_status = 1
        # ad9643读寄存器协议：[cmd1, cmd2, data]
        command = [0x1A, 0x00, addr]
        # 发送命令
        self.myserial.ser.write(bytearray(command))
        # 读取返回值，期望返回1字节寄存器数据
        ret = self.myserial.ser.read(1)
        if ret:
            print(f"读取ad9643寄存器0x{addr:02X}，值=0x{ret[0]:02X}")
            value = ret[0]
        else:
            print(f"读取ad9643寄存器失败，无返回数据")
            value = None
        self.busy_status = 0
        return value

    

def main():
    ad9643_01= ad9643()# 创建设备实例
    ad9643_01.myserial.port_get()# 获取可用串口列表
    for port_num in ad9643_01.myserial.port_list:
        print(port_num.description)# 打印所有串口的描述信息
    ad9643_01.myserial.port = ad9643_01.myserial.port_list[1].device
    print(ad9643_01.myserial.port)# 打印选中的串口
    ad9643_01.myserial.open_port()# 打开串口连接
    ad9643_01 = ad9643_01.hand_shake() # 握手验证设备连接
   # ad9643_01 = ad9643_01.sample_num_set(4)# 设置采样点数为2^4=16
   # ad9643_01 = ad9643_01.get_sample()# 获取采样数据1
   # ad9643_01 = ad9643_01.get_sample()# 获取采样数据2
    ad9643_01.myserial.close_port()# 关闭串口连接


if __name__ == '__main__':#当脚本作为主程序直接运行时，执行 main()；作为模块导入时，不执行
    main()