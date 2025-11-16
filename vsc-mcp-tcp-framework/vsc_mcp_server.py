import socket
import threading
import json
import time
from typing import Dict, Any, Callable, Optional

class VSCMCPMessage:
    """VSC MCP消息类，处理消息的序列化和反序列化"""
    
    def __init__(self, command: str, params: Dict[str, Any] = None, message_id: Optional[str] = None):
        self.command = command
        self.params = params or {}
        self.message_id = message_id
    
    def to_dict(self) -> Dict[str, Any]:
        """将消息转换为字典格式"""
        msg_dict = {"command": self.command, "params": self.params}
        if self.message_id:
            msg_dict["id"] = self.message_id
        return msg_dict
    
    def to_json(self) -> str:
        """将消息转换为JSON字符串"""
        return json.dumps(self.to_dict())
    
    @staticmethod
    def from_json(json_str: str) -> 'VSCMCPMessage':
        """从JSON字符串解析消息"""
        try:
            msg_dict = json.loads(json_str)
            return VSCMCPMessage(
                command=msg_dict.get("command"),
                params=msg_dict.get("params", {}),
                message_id=msg_dict.get("id")
            )
        except json.JSONDecodeError:
            print("Error decoding JSON message")
            return None


class VSCMCPServer:
    """VSC MCP TCP服务器类"""
    
    def __init__(self, host: str = 'localhost', port: int = 9999):
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_connections = {}  # 客户端连接字典: {client_id: connection}
        self.message_handlers = {}  # 消息处理器字典: {command: handler_function}
        self.is_running = False
        self.thread = None
    
    def start(self) -> None:
        """启动服务器"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.is_running = True
        self.thread = threading.Thread(target=self._accept_connections)
        self.thread.daemon = True
        self.thread.start()
        print(f"Server started on {self.host}:{self.port}")
    
    def stop(self) -> None:
        """停止服务器"""
        self.is_running = False
        # 关闭所有客户端连接
        for client_id, conn in self.client_connections.items():
            try:
                conn.close()
            except Exception as e:
                print(f"Error closing client connection {client_id}: {e}")
        self.client_connections.clear()
        
        # 关闭服务器套接字
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                print(f"Error closing server socket: {e}")
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        print("Server stopped")
    
    def _accept_connections(self) -> None:
        """接受客户端连接的线程函数"""
        while self.is_running:
            try:
                conn, addr = self.server_socket.accept()
                client_id = f"{addr[0]}:{addr[1]}"
                self.client_connections[client_id] = conn
                print(f"New client connected: {client_id}")
                # 为每个客户端创建一个线程处理消息
                client_thread = threading.Thread(target=self._handle_client, args=(conn, client_id))
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if self.is_running:
                    print(f"Error accepting connection: {e}")
                else:
                    break
    
    def _handle_client(self, conn: socket.socket, client_id: str) -> None:
        """处理客户端消息的线程函数"""
        try:
            while self.is_running:
                data = conn.recv(4096)
                if not data:
                    break
                message = VSCMCPMessage.from_json(data.decode('utf-8'))
                if message:
                    self._process_message(message, client_id)
        except Exception as e:
            print(f"Error handling client {client_id}: {e}")
        finally:
            # 客户端断开连接
            self._remove_client(client_id)
    
    def _process_message(self, message: VSCMCPMessage, client_id: str) -> None:
        """处理接收到的消息"""
        handler = self.message_handlers.get(message.command)
        if handler:
            try:
                handler(self, message, client_id)
            except Exception as e:
                print(f"Error processing message: {e}")
        else:
            print(f"No handler registered for command: {message.command}")
    
    def _remove_client(self, client_id: str) -> None:
        """移除客户端连接"""
        if client_id in self.client_connections:
            try:
                self.client_connections[client_id].close()
            except Exception as e:
                print(f"Error closing client connection: {e}")
            del self.client_connections[client_id]
            print(f"Client disconnected: {client_id}")
    
    def send_message(self, client_id: str, message: VSCMCPMessage) -> None:
        """向指定客户端发送消息"""
        if client_id in self.client_connections:
            try:
                self.client_connections[client_id].sendall(message.to_json().encode('utf-8'))
            except Exception as e:
                print(f"Error sending message to client {client_id}: {e}")
                self._remove_client(client_id)
    
    def broadcast_message(self, message: VSCMCPMessage) -> None:
        """向所有客户端广播消息"""
        for client_id in list(self.client_connections.keys()):
            self.send_message(client_id, message)
    
    def register_handler(self, command: str, handler: Callable) -> None:
        """注册消息处理器"""
        self.message_handlers[command] = handler


# 示例用法
if __name__ == "__main__":
    # 创建服务器实例
    server = VSCMCPServer()
    
    # 定义消息处理器
    def handle_connect(server: VSCMCPServer, message: VSCMCPMessage, client_id: str) -> None:
        print(f"Client {client_id} connected with params: {message.params}")
        response = VSCMCPMessage(
            command="connect_ack",
            params={"status": "success", "timestamp": time.time()},
            message_id=message.message_id
        )
        server.send_message(client_id, response)
    
    def handle_data(server: VSCMCPServer, message: VSCMCPMessage, client_id: str) -> None:
        print(f"Received data from {client_id}: {message.params}")
        # 处理数据...
    
    # 注册消息处理器
    server.register_handler("connect", handle_connect)
    server.register_handler("data", handle_data)
    
    # 启动服务器
    server.start()
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # 优雅地停止服务器
        server.stop()    