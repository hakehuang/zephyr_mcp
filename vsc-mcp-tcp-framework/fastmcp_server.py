import socket
import threading
import time
from typing import Dict, Any, Callable, Optional
from fastmcp_protocol import FastMCPProtocol

class FastMCPServer:
    """FastMCP TCP服务器类"""
    
    def __init__(self, host: str = 'localhost', port: int = 9999, max_clients: int = 10):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.server_socket = None
        self.clients = {}  # 客户端字典: {client_address: client_socket}
        self.message_handlers = {}  # 消息处理器字典: {command: handler_function}
        self.is_running = False
        self.accept_thread = None
        self.message_id_counter = 0
    
    def start(self) -> bool:
        """启动服务器"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_clients)
            self.is_running = True
            print(f"Server started on {self.host}:{self.port}")
            
            # 启动接受客户端连接的线程
            self.accept_thread = threading.Thread(target=self._accept_clients)
            self.accept_thread.daemon = True
            self.accept_thread.start()
            return True
        except Exception as e:
            print(f"Error starting server: {e}")
            return False
    
    def stop(self) -> None:
        """停止服务器"""
        self.is_running = False
        
        # 关闭所有客户端连接
        for client_address, client_socket in self.clients.items():
            try:
                client_socket.close()
            except Exception as e:
                print(f"Error closing client {client_address}: {e}")
        self.clients.clear()
        
        # 关闭服务器套接字
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                print(f"Error closing server socket: {e}")
            self.server_socket = None
        
        # 等待接受线程结束
        if self.accept_thread and self.accept_thread.is_alive():
            self.accept_thread.join(timeout=1.0)
        
        print("Server stopped")
    
    def _accept_clients(self) -> None:
        """接受客户端连接的线程函数"""
        while self.is_running:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"New client connected: {client_address}")
                self.clients[client_address] = client_socket
                
                # 为每个客户端启动一个接收线程
                client_thread = threading.Thread(target=self._handle_client, args=(client_socket, client_address))
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if self.is_running:
                    print(f"Error accepting client: {e}")
    
    def _handle_client(self, client_socket: socket.socket, client_address: tuple) -> None:
        """处理客户端连接的线程函数"""
        buffer = b''
        while self.is_running and client_address in self.clients:
            try:
                data = client_socket.recv(4096)
                if not data:
                    # 客户端关闭连接
                    print(f"Client disconnected: {client_address}")
                    self._remove_client(client_address)
                    break
                
                buffer += data
                
                # 处理所有完整的消息
                while len(buffer) >= FastMCPProtocol.HEADER_SIZE:
                    # 解析消息头获取消息长度
                    try:
                        length = struct.unpack('>I', buffer[:4])[0]
                    except struct.error:
                        break
                    
                    if len(buffer) >= length:
                        # 提取完整消息
                        message_data = buffer[:length]
                        buffer = buffer[length:]
                        
                        # 解析消息
                        message = FastMCPProtocol.unpack_message(message_data)
                        if message:
                            command, message_id, payload = message
                            self._process_message(client_socket, client_address, command, message_id, payload)
                    else:
                        break
            except Exception as e:
                if self.is_running and client_address in self.clients:
                    print(f"Error handling client {client_address}: {e}")
                    self._remove_client(client_address)
                break
    
    def _remove_client(self, client_address: tuple) -> None:
        """移除客户端连接"""
        if client_address in self.clients:
            try:
                self.clients[client_address].close()
            except Exception as e:
                print(f"Error closing client socket: {e}")
            del self.clients[client_address]
    
    def _process_message(self, client_socket: socket.socket, client_address: tuple, 
                         command: bytes, message_id: int, payload: bytes) -> None:
        """处理接收到的消息"""
        handler = self.message_handlers.get(command)
        if handler:
            try:
                handler(self, client_socket, client_address, command, message_id, payload)
            except Exception as e:
                print(f"Error processing message: {e}")
        else:
            print(f"No handler registered for command: {command}")
    
    def send_message(self, client_socket: socket.socket, command: bytes, payload: bytes) -> None:
        """向客户端发送消息"""
        if self.is_running:
            message_id = self._get_next_message_id()
            message = FastMCPProtocol.pack_message(command, message_id, payload)
            try:
                client_socket.sendall(message)
            except Exception as e:
                print(f"Error sending message: {e}")
    
    def broadcast_message(self, command: bytes, payload: bytes) -> None:
        """向所有客户端广播消息"""
        if self.is_running:
            message_id = self._get_next_message_id()
            message = FastMCPProtocol.pack_message(command, message_id, payload)
            for client_address, client_socket in list(self.clients.items()):
                try:
                    client_socket.sendall(message)
                except Exception as e:
                    print(f"Error broadcasting to {client_address}: {e}")
                    self._remove_client(client_address)
    
    def register_handler(self, command: bytes, handler: Callable) -> None:
        """注册消息处理器"""
        self.message_handlers[command] = handler
    
    def _get_next_message_id(self) -> int:
        """获取下一个消息ID"""
        self.message_id_counter = (self.message_id_counter + 1) % 0xFFFFFFFF
        return self.message_id_counter


# 示例用法
if __name__ == "__main__":
    # 创建服务器实例
    server = FastMCPServer()
    
    # 启动服务器
    if server.start():
        # 定义消息处理器
        def handle_connect(server: FastMCPServer, client_socket: socket.socket, 
                          client_address: tuple, command: bytes, message_id: int, payload: bytes) -> None:
            print(f"Connect message from {client_address}: {payload}")
            # 发送连接确认
            server.send_message(client_socket, b'CA', b'Connection accepted')
        
        def handle_data(server: FastMCPServer, client_socket: socket.socket, 
                       client_address: tuple, command: bytes, message_id: int, payload: bytes) -> None:
            print(f"Data message from {client_address}: {payload}")
            # 广播数据给所有客户端
            server.broadcast_message(b'DB', payload)
        
        # 注册消息处理器
        server.register_handler(b'CN', handle_connect)  # 连接消息
        server.register_handler(b'DT', handle_data)    # 数据消息
        
        try:
            # 保持主线程运行
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            # 优雅地停止服务器
            server.stop()    