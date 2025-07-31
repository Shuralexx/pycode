import numpy as np

N = 8192  # 点数，也可以修改为其它值
table_type = 'float'  # 可选：'float' 或 'double'

cos_tbl = np.cos(2 * np.pi * np.arange(N // 2) / N)
sin_tbl = np.sin(2 * np.pi * np.arange(N // 2) / N)

# 格式化函数
def format_c_array(arr, name):
    typename = 'float' if table_type == 'float' else 'double'
    s = f"static const {typename} {name}[{N // 2}] = {{\n"
    for i, v in enumerate(arr):
        s += f"{v:.8f}f, " if table_type == 'float' else f"{v:.17g}, "
        if (i + 1) % 8 == 0:
            s += "\n"
    s = s.rstrip(', \n') + "\n};\n"
    return s

with open("cos_sin_table.c", "w") as f:
    f.write(format_c_array(cos_tbl, "cos_table"))
    f.write("\n")
    f.write(format_c_array(sin_tbl, "sin_table"))

print("生成完成！文件已保存为 cos_sin_table.c")
