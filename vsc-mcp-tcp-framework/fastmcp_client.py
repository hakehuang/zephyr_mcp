import socket
import threading
import time
from typing import Dict, Any, Callable, Optional
from fastmcp_protocol import FastMCPProtocol
from tcp_base_client import TCPClientBase

class FastMCPClient(TCPClientBase):
    """FastMCP TCP客户端类"""
    
    def __init__(self, host: str = 'localhost', port: int = 9999):
        super().__init__(host, port)
        self.buffer = b''
    

    

    
    def _receive_messages(self) -> None:
        """接收服务器消息的线程函数"""
        while self.is_connected:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    # 服务器关闭连接
                    print("Server closed connection")
                    self.disconnect()
                    break
                
                self.buffer += data
                
                # 处理所有完整的消息
                while len(self.buffer) >= FastMCPProtocol.HEADER_SIZE:
                    # 解析消息头获取消息长度
                    try:
                        length = struct.unpack('>I', self.buffer[:4])[0]
                    except struct.error:
                        break
                    
                    if len(self.buffer) >= length:
                        # 提取完整消息
                        message_data = self.buffer[:length]
                        self.buffer = self.buffer[length:]
                        
                        # 解析消息
                        message = FastMCPProtocol.unpack_message(message_data)
                        if message:
                            command, message_id, payload = message
                            self._process_message(command, message_id, payload)
                    else:
                        break
            except Exception as e:
                if self.is_connected:
                    print(f"Error receiving message: {e}")
                    self.disconnect()
                break
    
    def _process_message(self, command: bytes, message_id: int, payload: bytes) -> None:
        """处理接收到的消息"""
        handler = self.message_handlers.get(command)
        if handler:
            try:
                handler(self, command, message_id, payload)
            except Exception as e:
                print(f"Error processing message: {e}")
        else:
            print(f"No handler registered for command: {command}")
    
    def send_message(self, command: bytes, payload: bytes) -> None:
        """向服务器发送消息"""
        if self.is_connected and self.client_socket:
            message_id = self._get_next_message_id()
            message = FastMCPProtocol.pack_message(command, message_id, payload)
            try:
                self.client_socket.sendall(message)
            except Exception as e:
                print(f"Error sending message: {e}")
                self.disconnect()
    

    



# 示例用法
if __name__ == "__main__":
    # 创建客户端实例
    client = FastMCPClient()
    
    # 连接到服务器
    if client.connect():
        # 定义消息处理器
        def handle_connect_ack(client: FastMCPClient, command: bytes, message_id: int, payload: bytes) -> None:
            print(f"Connect ACK received: {payload}")
        
        def handle_data_broadcast(client: FastMCPClient, command: bytes, message_id: int, payload: bytes) -> None:
            print(f"Data broadcast received: {payload}")
        
        # 注册消息处理器
        client.register_handler(b'CA', handle_connect_ack)  # 连接确认消息
        client.register_handler(b'DB', handle_data_broadcast)  # 数据广播消息
        
        # 发送连接消息
        client.send_message(b'CN', b'Client connected')
        
        # 发送一些数据
        for i in range(5):
            client.send_message(b'DT', f'Data {i}'.encode('utf-8'))
            time.sleep(1)
        
        # 断开连接
        client.disconnect()