import threading
from fastmcp_protocol import FastMCPProtocol
from fastmcp_client import FastMCPClient

class DeviceManager:
    """设备管理服务，负责管理连接的设备和设备状态"""
    
    def __init__(self, server_host: str = 'localhost', server_port: int = 9999):
        self.server_host = server_host
        self.server_port = server_port
        self.devices = {}  # {device_id: device_info}
        self.lock = threading.Lock()
        self.client = FastMCPClient(server_host, server_port)
        self.running = False
    
    def start(self) -> bool:
        """启动设备管理服务"""
        if self.running:
            return True
        
        # 连接到服务器
        if not self.client.connect():
            return False
        
        # 注册消息处理器
        self.client.register_handler(b'CN', self._handle_device_connect)
        self.client.register_handler(b'DC', self._handle_device_disconnect)
        self.client.register_handler(b'ST', self._handle_device_status)
        
        self.running = True
        print("DeviceManager started")
        return True
    
    def stop(self) -> None:
        """停止设备管理服务"""
        if not self.running:
            return
        
        self.running = False
        self.client.disconnect()
        print("DeviceManager stopped")
    
    def _handle_device_connect(self, client, command, message_id, payload):
        """处理设备连接消息"""
        try:
            device_info = FastMCPProtocol.unpack_device_info(payload)
            device_id = device_info['device_id']
            
            with self.lock:
                self.devices[device_id] = device_info
            
            print(f"Device connected: {device_id}, {device_info}")
            
            # 发送连接确认
            response_payload = FastMCPProtocol.pack_device_ack(device_id, True, "Connection accepted")
            client.send_message(b'CA', response_payload)
        except Exception as e:
            print(f"Error handling device connect: {e}")
    
    def _handle_device_disconnect(self, client, command, message_id, payload):
        """处理设备断开连接消息"""
        try:
            device_id = payload.decode('utf-8')
            
            with self.lock:
                if device_id in self.devices:
                    del self.devices[device_id]
            
            print(f"Device disconnected: {device_id}")
        except Exception as e:
            print(f"Error handling device disconnect: {e}")
    
    def _handle_device_status(self, client, command, message_id, payload):
        """处理设备状态更新消息"""
        try:
            device_id, status = FastMCPProtocol.unpack_device_status(payload)
            
            with self.lock:
                if device_id in self.devices:
                    self.devices[device_id]['status'] = status
                    print(f"Device status updated: {device_id}, {status}")
                else:
                    print(f"Received status from unknown device: {device_id}")
        except Exception as e:
            print(f"Error handling device status: {e}")
    
    def get_device_list(self) -> list:
        """获取当前连接的设备列表"""
        with self.lock:
            return list(self.devices.values())
    
    def get_device_info(self, device_id: str) -> dict:
        """获取指定设备的信息"""
        with self.lock:
            return self.devices.get(device_id, {})
    
    def send_command_to_device(self, device_id: str, command_code: bytes, command_params: bytes) -> bool:
        """向指定设备发送命令"""
        try:
            payload = FastMCPProtocol.pack_device_command(device_id, command_code, command_params)
            self.client.send_message(b'CMD', payload)
            return True
        except Exception as e:
            print(f"Error sending command to device: {e}")
            return False


# 示例用法
if __name__ == "__main__":
    device_manager = DeviceManager()
    
    try:
        if device_manager.start():
            # 等待设备连接
            print("Waiting for devices to connect...")
            time.sleep(30)
            
            # 获取设备列表
            devices = device_manager.get_device_list()
            print(f"Connected devices: {devices}")
            
            # 向第一个设备发送命令（如果有）
            if devices:
                first_device_id = devices[0]['device_id']
                device_manager.send_command_to_device(first_device_id, b'REB', b'')  # 重启命令
    finally:
        device_manager.stop()    