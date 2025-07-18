import serial
try:
    from serial.tools import list_ports
except Exception:  # pragma: no cover - fallback when pyserial missing
    list_ports = None


class SerialAchieve:
    def __init__(self):
        self.ser = None
        self.port = None
        if list_ports:
            self.port_list = list(list_ports.comports())  # 获取串口列表
        else:
            self.port_list = []
        # assert (len(self.port_list) != 0), '无可用串口'
        self.bold_rate = 115200 # 设置波特率

    def port_get(self):
        return self.port_list

    def open_port(self):
        if self.port is None:
            print("错误：没有选择串口！")
            return
        
        try:
            if self.ser is None:
                self.ser = serial.Serial(self.port, self.bold_rate, timeout=0.5)
            if self.ser.is_open:
                print(f"{self.port} + 串口已经打开！")
            else:
                self.ser = serial.Serial(self.port, self.bold_rate, timeout=0.5)
                print(f"{self.port} + 串口已经打开！")
        except serial.SerialException as e:
            print(f"打开串口失败: {e}")

    def close_port(self):
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
            if self.ser.is_open:
                print("串口关闭失败！")
            else:
                print("串口成功关闭！")
        else:
            print("串口未打开，无需关闭。")
