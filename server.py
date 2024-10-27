import socket
from threading import Thread
import os
import re
import time
import pickle  # 用于存储用户数据

clients = {}  # 存储已连接的客户端和对应的名称
user_data = {}  # 存储用户名和密码


def load_user_data():
    """加载用户数据"""
    global user_data
    if os.path.exists('user_data.pkl'):
        with open('user_data.pkl', 'rb') as f:
            user_data = pickle.load(f)

def save_user_data():
    """保存用户数据"""
    with open('user_data.pkl', 'wb') as f:
        pickle.dump(user_data, f)


class ClientThread(Thread):
    def __init__(self, client_socket, client_address):
        Thread.__init__(self)
        self.client_socket = client_socket
        self.client_address = client_address
        self.client_name = None
        self.password = None
        print(f"[+] New connection from {client_address}")

    def run(self):
        global clients
        load_user_data()
        # 接收客户端发送的名字
        received_data = self.client_socket.recv(1024).decode("utf-8")
        data_parts = received_data.split('\n')
        self.client_name = data_parts[0] if len(data_parts) > 0 else ""
        self.password = data_parts[1] if len(data_parts) > 1 else ""
        username = self.client_name
        password = self.password
        if username in user_data:
            # 用户存在，检查密码
            if user_data[username] == password:
                clients[self.client_socket] = self.client_name
            else:
                self.client_name = None
                self.password = None
                self.client_socket.send(b'WRONG_PASSWORD')
                self.client_socket.close()
                return
        else:
            # 用户不存在，注册新用户
            user_data[username] = password
            save_user_data()
            clients[self.client_socket] = self.client_name


        self.broadcast(f'server@wind:{self.client_name} has joined the chat.', self.client_socket, 0)
        self.broadcast_user_list()
        while True:
            try:
                message = self.client_socket.recv(1024)
                if message:
                    # 广播客户端消息，附加客户端名字
                    if message == "SEND_FILE".encode('utf8'):
                        # 接收文件名
                        filename = self.client_socket.recv(1024).decode()  # 接收文件名
                        print(f'Receiving file: {filename}')

                        # 将文件保存到服务器
                        with open(os.path.basename(filename), 'wb') as f:
                            # bytes_read = self.client_socket.recv(1024)
                            # f.write(bytes_read)
                            # n=0
                            while True:
                                bytes_read = self.client_socket.recv(1024)
                                if bytes_read == "SEND_FILE END".encode('utf8') or not bytes_read:
                                    break
                                f.write(bytes_read)

                        print(f'File {filename} received from {self.client_address}.')
                        # for client in clients.keys():
                        #     if client != self.client_socket:  # 不发送给发送文件的客户端
                        #         client.sendall(f"FILE {filename}".encode())  # 发送文件名
                        self.broadcast(f"FILE {filename} 0", self.client_socket, 1)
                        self.broadcast(f"server@wind:{clients[self.client_socket]} send a file '{filename}'",
                                       self.client_socket, 0)
                    elif message == "RECEIVE_FILE".encode('utf8'):
                        filename = self.client_socket.recv(1024).decode()  # 接收文件名
                        print(f'Sending file {filename} to {clients[self.client_socket]}.')
                        self.client_socket.send(f"FILE {filename} 1".encode('utf8'))
                        # 读取并发送文件
                        with open(os.path.basename(filename), 'rb') as f:
                            bytes_read = f.read(1024)
                            while bytes_read:
                                self.client_socket.send(bytes_read)
                                bytes_read = f.read(1024)
                        time.sleep(1)
                        self.client_socket.send("file end".encode("utf8"))  # 发送结束标志
                        print(f'File {filename} sent to {clients[self.client_socket]}.')
                    else:
                        self.broadcast(f"{self.client_name}: {message.decode('utf-8')}", self.client_socket, 1)
                else:
                    break
            except:
                break

        # 客户端断开连接
        print(f"[-] Connection closed from {self.client_address}")
        self.broadcast(f'server@wind:{self.client_name} has left the chat.', self.client_socket, 0)
        # self.broadcast(f'<div style="color:gray; text-align:center;">{self.client_name} has left the chat.</div>', self.client_socket,0)
        # clients.pop(self.client_socket)
        self.broadcast_user_list()
        self.client_socket.close()

    def broadcast(self, message, sender_socket, flag):
        """广播消息给所有连接的客户端"""
        to_remove = []
        # 系统公共消息
        if flag == 0:
            for client in clients:
                try:
                    client.send(message.encode())
                except:
                    to_remove.append(client)

        # 用户发送消息
        else:
            for client in clients:
                if client != sender_socket:
                    try:
                        left_message = f'{message}'
                        # left_message= f'<div style="text-align: left;">{message}</div>'
                        client.send(left_message.encode())
                    except:
                        to_remove.append(client)
        for client in to_remove:
            client.close()
            # clients.pop(client)
            clients.pop(client, None)

    def broadcast_user_list(self):
        to_remove = []
        """广播当前在线用户列表"""
        client_list = list(clients.keys())
        user_list = ','.join(clients.values())  # 将用户名列表组合成字符串
        for client in client_list:
            try:
                client.send(f"USER_LIST:{user_list}".encode())  # 发送用户列表，使用特定前缀区分
            except:
                to_remove.append(client)
        for client in to_remove:
            client.close()
            # clients.pop(client)
            clients.pop(client, None)


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    host = '0.0.0.0'
    port = 8080
    server_socket.bind((host, port))
    server_socket.listen(5)
    print("[*] Server started on port 8080")

    while True:
        client_socket, client_address = server_socket.accept()
        new_client = ClientThread(client_socket, client_address)
        new_client.start()


if __name__ == "__main__":
    server_thread = Thread(target=start_server)
    server_thread.start()

    while True:
        # 服务器端可以主动输入消息广播给所有客户端
        server_message = input("Server: ")
        for client in clients:
            try:
                client.send(f"Server: {server_message}".encode())
            except:
                client.close()
                clients.pop(client)
