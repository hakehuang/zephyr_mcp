from nt import environ
import socket
import threading
import json
import time
from typing import Dict, Any, Callable, Optional
from tcp_base_client import TCPClientBase

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
            if not isinstance(msg_dict, dict) or "command" not in msg_dict:
                raise ValueError("Missing required 'command' field in JSON")
            return VSCMCPMessage(
                command=msg_dict.get("command"),
                params=msg_dict.get("params", {}),
                message_id=msg_dict.get("id")
            )
        except json.JSONDecodeError:
            # Re-raise with original error
            raise
        except Exception as e:
            # # # print(f"Invalid message structure: {e}")
            return None


class VSCMCPClient(TCPClientBase):
    """VSC MCP TCP客户端类，同时作为本地stdio服务器"""
    
    def __init__(self, host: str = 'localhost', port: int = 5002):
        super().__init__(host, port)
        self.local_server = None
        self.remote_server_connected = False
        # 添加远程服务器配置
        self.remote_host = host
        self.remote_port = port
        
    def start_local_stdio_server(self):
        self.local_server = threading.Thread(target=self._handle_stdio, daemon=True)
        self.local_server.start()
        # print("Local stdio MCP server started")
    
    def _handle_stdio(self):
        import sys
        while True:
            try:
                # 读取stdio输入
                data = sys.stdin.readline()
                if not data:
                    break
                # 解析输入并转发到远程服务器
                self._forward_to_remote_server(data.strip())
            except Exception as e:
                # print(f"Stdio error: {e}")
                break
    
    def _forward_to_remote_server(self, data):
        if not self.is_connected:
            # 如果未连接，则尝试连接远程服务器
            if not self.connect():
                # print("Failed to connect to remote server")
                return
        
        # 创建消息并发送到远程服务器
        message = VSCMCPMessage(
            command="relay",
            params={"data": data},
            message_id=self.generate_message_id()
        )
        self.send_message(message)
    
    def _receive_messages(self) -> None:
        """接收服务器消息的线程函数"""
        while self.is_connected:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    # 服务器关闭连接
                    # print("Server closed connection")
                    self.disconnect()
                    break
                raw_data = data.decode('utf-8').strip()
                try:
                    message = VSCMCPMessage.from_json(raw_data)
                except json.JSONDecodeError as e:
                    # print(f"Invalid JSON received: {raw_data}")
                    # print(f"JSON parsing error: {e}")
                    # Optionally send error notification
                    error_msg = VSCMCPMessage(
                        command="json_error",
                        params={"error": str(e), "raw_data": raw_data[:100]},
                        message_id=self.generate_message_id()
                    )
                    self.send_message(error_msg)
                    continue
                if message:
                    self._process_message(message)
            except Exception as e:
                if self.is_connected:
                    # print(f"Error receiving message: {e}")
                    self.disconnect()
                break
    
    def _process_message(self, message: VSCMCPMessage) -> None:
        import sys
        handler = self.message_handlers.get(message.command)
        if handler:
            try:
                handler(self, message)
            except Exception as e:
                pass
        else:
            # 将远程服务器消息转发到stdio
            # print(f"Remote server response: {message.to_json()}")
            sys.stdout.write(f"{message.to_json()}\n")
            sys.stdout.flush()
    
    def send_message(self, message: VSCMCPMessage) -> None:
        """向服务器发送消息"""
        if self.is_connected and self.client_socket:
            try:
                self.client_socket.sendall(message.to_json().encode('utf-8'))
            except Exception as e:
                # print(f"Error sending message: {e}")
                self.disconnect()
    

    
    def connect(self, max_retries=5, retry_delay=1) -> bool:
        retries = 0
        while retries < max_retries:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.remote_host, self.remote_port))
                self.is_connected = True
                self.start_receive_thread()
                return True
            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    return False
                time.sleep(retry_delay)
        return False

    def generate_message_id(self) -> str:
        """生成唯一的消息ID"""
        return str(self._get_next_message_id())


# 示例用法
if __name__ == "__main__":
    # 创建客户端实例，连接到远程服务器
    remote_host = environ.get("MCP_SERVER_HOST", "192.168.1.100")
    remote_port = int(environ.get("MCP_SERVER_PORT", 5002))
    client = VSCMCPClient(host=remote_host, port=remote_port)
    
    # 启动本地stdio服务器
    client.start_local_stdio_server()
    
    # 连接到远程服务器
    if client.connect():
        # print(f"Connected to remote MCP server at {client.remote_host}:{client.remote_port}")
        
        # 保持程序运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            client.disconnect()
            # print("Disconnected")
        
        # 定义消息处理器
        def handle_connect_ack(client: VSCMCPClient, message: VSCMCPMessage) -> None:
            # print(f"Connect ACK received: {message.params}")
            pass
        
        def handle_server_data(client: VSCMCPClient, message: VSCMCPMessage) -> None:
            # print(f"Received data from server: {message.params}")
            pass
        
        # 注册消息处理器
        client.register_handler("connect_ack", handle_connect_ack)
        client.register_handler("server_data", handle_server_data)
        
        # 发送连接消息
        connect_msg = VSCMCPMessage(
            command="connect",
            params={"client_type": "example", "version": "1.0"},
            message_id=client.generate_message_id()
        )
        client.send_message(connect_msg)
        
        # 发送一些数据
        for i in range(5):
            data_msg = VSCMCPMessage(
                command="data",
                params={"counter": i, "timestamp": time.time()},
                message_id=client.generate_message_id()
            )
            client.send_message(data_msg)
            time.sleep(1)
        
        # 断开连接
        client.disconnect()