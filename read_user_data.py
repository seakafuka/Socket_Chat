import pickle
# 显示用户数据库user_data.pkl内容
# 如果没有该文件 client.py注册第一个用户时会自动生成
# 指定你想要读取的 pkl 文件路径
file_path = "E:\Python-Chat-Application-Using-PyQt-and-Socket-master\user_data.pkl"  # 替换为你的文件路径

try:
    # 打开并加载 pkl 文件
    with open(file_path, "rb") as file:
        data = pickle.load(file)

    # 打印 pkl 文件的内容
    print("内容如下：")
    print(data)

except FileNotFoundError:
    print(f"文件 {file_path} 未找到，请检查路径。")
except pickle.UnpicklingError:
    print("文件无法被解析，可能不是有效的 .pkl 文件。")
except Exception as e:
    print(f"发生错误：{e}")
