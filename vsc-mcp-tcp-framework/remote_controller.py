import threading
from fastmcp_protocol import FastMCPProtocol
from fastmcp_client import FastMCPClient

class RemoteController:
    """远程控制服务，负责向设备发送控制命令并接收响应"""
    
    def __init__(self, server_host: str = 'localhost', server_port: int = 9999):
        self.server_host = server_host
        self.server_port = server_port
        self.client = FastMCPClient(server_host, server_port)
        self.pending_commands = {}  # {message_id: callback}
        self.lock = threading.Lock()
        self.running = False
    
    def start(self) -> bool:
        """启动远程控制服务"""
        if self.running:
            return True
        
        # 连接到服务器
        if not self.client.connect():
            return False
        
        # 注册消息处理器
        self.client.register_handler(b'CMDR', self._handle_command_response)
        
        self.running = True
        print("RemoteController started")
        return True
    
    def stop(self) -> None:
        """停止远程控制服务"""
        if not self.running:
            return
        
        self.running = False
        self.client.disconnect()
        print("RemoteController stopped")
    
    def _handle_command_response(self, client, command, message_id, payload):
        """处理命令响应消息"""
        try:
            response_message_id, device_id, success, response_data = FastMCPProtocol.unpack_command_response(payload)
            
            with self.lock:
                if response_message_id in self.pending_commands:
                    callback = self.pending_commands.pop(response_message_id)
                    if callback:
                        callback(device_id, success, response_data)
                    print(f"Command response processed for message ID: {response_message_id}")
                else:
                    print(f"Received response for unknown message ID: {response_message_id}")
        except Exception as e:
            print(f"Error handling command response: {e}")
    
    def send_command(self, device_id: str, command_code: bytes, command_params: bytes, 
                     callback: callable = None) -> bool:
        """发送控制命令到指定设备
        
        Args:
            device_id: 目标设备ID
            command_code: 命令代码(字节类型)
            command_params: 命令参数(字节类型)
            callback: 命令响应回调函数，格式为 callback(device_id, success, response_data)
        
        Returns:
            命令是否成功发送
        """
        try:
            # 记录消息ID和回调函数
            message_id = self.client._get_next_message_id()
            with self.lock:
                self.pending_commands[message_id] = callback
            
            # 构建并发送命令
            payload = FastMCPProtocol.pack_device_command(device_id, command_code, command_params, message_id)
            self.client.send_message(b'CMD', payload)
            
            print(f"Command sent to {device_id}: {command_code}")
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            with self.lock:
                if message_id in self.pending_commands:
                    del self.pending_commands[message_id]
            return False


# 示例用法
if __name__ == "__main__":
    def command_callback(device_id, success, response_data):
        """命令响应回调函数"""
        if success:
            print(f"Command to {device_id} succeeded: {response_data}")
        else:
            print(f"Command to {device_id} failed: {response_data}")
    
    controller = RemoteController()
    
    try:
        if controller.start():
            print("RemoteController started")
            
            # 发送控制命令
            controller.send_command(
                device_id='device1',
                command_code=b'SETP',  # 设置参数命令
                command_params=b'05',  # 参数值为5
                callback=command_callback
            )
            
            # 发送另一个命令
            controller.send_command(
                device_id='device2',
                command_code=b'REBOOT',  # 重启命令
                command_params=b'',
                callback=command_callback
            )
            
            # 保持运行一段时间以接收响应
            time.sleep(10)
    finally:
        controller.stop()    