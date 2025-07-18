import serial
import serial.tools.list_ports
# 获取所有串口设备实例。
# 如果没找到串口设备，则输出：“无串口设备。”
# 如果找到串口设备，则依次输出每个设备对应的串口号和描述信息。
# ports_list = list(serial.tools.list_ports.comports())
# if len(ports_list) <= 0:
#     print("无串口设备。")
# else:
#     print("可用的串口设备如下：")
#     for comport in ports_list:
#         print(list(comport)[0], list(comport)[1])


#确定串口号
# # 方式1：调用函数接口打开串口时传入配置参数
# ser = serial.Serial("COM1", 115200)    # 打开COM1，将波特率配置为115200，其余参数使用默认值
# if ser.isOpen():                        # 判断串口是否成功打开
#     print("打开串口成功。")
#     print(ser.name)    # 输出串口号
# else:
#     print("打开串口失败。")


#配置串口 & 打开串口
# # 打开 COM1，将波特率配置为115200，数据位为7，停止位为2，无校验位，读超时时间为0.5秒。
# ser = serial.Serial(port="COM1",
#                     baudrate=115200,
#                     bytesize=serial.SEVENBITS,
#                     parity=serial.PARITY_NONE,
#                     stopbits=serial.STOPBITS_TWO,
#                     timeout=0.5) 


#关闭串口
# ser.close()
# if ser.isOpen():                        # 判断串口是否关闭
#     print("串口未关闭。")
# else:
#     print("串口已关闭。")


# #发送数据 write()
# # 打开 COM1，将波特率配置为115200.
# ser = serial.Serial(port="COM1", baudrate=115200)
 
# # 串口发送 ABCDEFG，并输出发送的字节数。
# write_len = ser.write("ABCDEFG".encode('utf-8'))
# print("串口发出{}个字节。".format(write_len))
 
# ser.close()


#读取数据 read()
# 打开 COM1，将波特率配置为115200, 读超时时间为1秒
ser = serial.Serial(port="COM1", baudrate=115200, timeout=1)
 
# 读取串口输入信息并输出。
while True:
    com_input = ser.read(10)
    if com_input:   # 如果读取结果非空，则输出
        print(com_input)

ser.close()