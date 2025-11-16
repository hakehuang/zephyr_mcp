import threading
import time
from fastmcp_protocol import FastMCPProtocol
from fastmcp_client import FastMCPClient

class DataCollector:
    """数据采集服务，负责收集和存储设备数据"""
    
    def __init__(self, server_host: str = 'localhost', server_port: int = 9999):
        self.server_host = server_host
        self.server_port = server_port
        self.client = FastMCPClient(server_host, server_port)
        self.data_store = {}  # {device_id: {timestamp: data}}
        self.lock = threading.Lock()
        self.running = False
        self.collection_interval = 5  # 数据采集间隔(秒)
        self.collection_thread = None
    
    def start(self) -> bool:
        """启动数据采集服务"""
        if self.running:
            return True
        
        # 连接到服务器
        if not self.client.connect():
            return False
        
        # 注册消息处理器
        self.client.register_handler(b'DATA', self._handle_device_data)
        
        self.running = True
        print("DataCollector started")
        
        # 启动定时采集线程
        self.collection_thread = threading.Thread(target=self._collect_data_periodically)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        
        return True
    
    def stop(self) -> None:
        """停止数据采集服务"""
        if not self.running:
            return
        
        self.running = False
        self.client.disconnect()
        
        if self.collection_thread and self.collection_thread.is_alive():
            self.collection_thread.join(timeout=1.0)
        
        print("DataCollector stopped")
    
    def _handle_device_data(self, client, command, message_id, payload):
        """处理设备数据消息"""
        try:
            device_id, timestamp, data = FastMCPProtocol.unpack_device_data(payload)
            
            with self.lock:
                if device_id not in self.data_store:
                    self.data_store[device_id] = {}
                self.data_store[device_id][timestamp] = data
            
            print(f"Received data from {device_id} at {timestamp}: {data}")
        except Exception as e:
            print(f"Error handling device data: {e}")
    
    def _collect_data_periodically(self) -> None:
        """定期采集数据的线程函数"""
        while self.running:
            try:
                # 这里应该实现向所有设备请求数据的逻辑
                # 简化示例，假设我们有一个设备列表
                device_ids = ['device1', 'device2']  # 实际应用中应从设备管理器获取
                
                for device_id in device_ids:
                    self.request_device_data(device_id)
                
                time.sleep(self.collection_interval)
            except Exception as e:
                print(f"Error in periodic data collection: {e}")
                time.sleep(self.collection_interval)
    
    def request_device_data(self, device_id: str) -> bool:
        """请求指定设备的数据"""
        try:
            payload = device_id.encode('utf-8')
            self.client.send_message(b'GETD', payload)
            return True
        except Exception as e:
            print(f"Error requesting device data: {e}")
            return False
    
    def get_device_data(self, device_id: str, limit: int = 100) -> dict:
        """获取指定设备的历史数据"""
        with self.lock:
            if device_id in self.data_store:
                # 返回最新的limit条数据
                timestamps = sorted(self.data_store[device_id].keys(), reverse=True)
                recent_timestamps = timestamps[:limit]
                return {ts: self.data_store[device_id][ts] for ts in recent_timestamps}
            return {}


# 示例用法
if __name__ == "__main__":
    data_collector = DataCollector()
    
    try:
        if data_collector.start():
            print("Data collection started...")
            
            # 收集数据一段时间
            time.sleep(30)
            
            # 获取某个设备的数据
            device_data = data_collector.get_device_data('device1')
            print(f"Collected data: {device_data}")
    finally:
        data_collector.stop()    