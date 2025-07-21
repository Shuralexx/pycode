from cm1348_dev import cm1348_dev  # 导入cm1348_dev类

def main():
    cm1348_dev01 = cm1348_dev()  # 创建设备实例

    # 获取串口列表并检查是否有可用串口
    if len(cm1348_dev01.myserial.port_list) == 0:
        print("错误：未检测到任何串口设备！")
        return

    print("可用的串口设备：")
    for i, port_info in enumerate(cm1348_dev01.myserial.port_list):
        print(f"{i}: {port_info.device} - {port_info.description}")

    # 确保选择有效的串口
    port_index = 0  # 默认选择第一个串口，或者可以改为用户输入
    if port_index >= len(cm1348_dev01.myserial.port_list):
        print(f"错误：无效的串口索引 {port_index}，无法选择该串口。")
        return

    # 选择串口
    cm1348_dev01.myserial.port = cm1348_dev01.myserial.port_list[port_index].device
    print(f"选择串口: {cm1348_dev01.myserial.port}")

    cm1348_dev01.myserial.open_port()  # 打开串口
    # 后续设备操作，例如配置、采样等
    cm1348_dev01.sample_data()
    cm1348_dev01.disconnect_device()  # 断开连接

if __name__ == '__main__':
    main()
