import struct
import time
import threading
from typing import Dict, Any, Callable, Optional, Tuple

class FastMCPProtocol:
    """FastMCP协议实现类，处理消息的打包和解包"""
    
    # 消息头结构：长度(4字节) + 命令(2字节) + 消息ID(4字节) + 校验和(2字节)
    HEADER_FORMAT = '>I2sI2s'
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    
    @staticmethod
    def calculate_checksum(data: bytes) -> bytes:
        """计算数据的校验和"""
        checksum = 0
        for byte in data:
            checksum ^= byte
        return struct.pack('>H', checksum)
    
    @staticmethod
    def pack_message(command: bytes, message_id: int, payload: bytes) -> bytes:
        """打包消息为FastMCP格式"""
        payload_length = len(payload)
        total_length = FastMCPProtocol.HEADER_SIZE + payload_length
        
        # 构建不含校验和的头部
        header_without_checksum = struct.pack(
            '>I2sI', 
            total_length, 
            command, 
            message_id
        )
        
        # 计算校验和（包含头部和负载）
        data_to_checksum = header_without_checksum + payload
        checksum = FastMCPProtocol.calculate_checksum(data_to_checksum)
        
        # 构建完整头部
        header = header_without_checksum + checksum
        
        # 返回完整消息
        return header + payload
    
    @staticmethod
    def unpack_message(data: bytes) -> Optional[Tuple[bytes, int, bytes]]:
        """从字节数据解包消息"""
        if len(data) < FastMCPProtocol.HEADER_SIZE:
            return None
        
        # 解析头部
        header = data[:FastMCPProtocol.HEADER_SIZE]
        payload = data[FastMCPProtocol.HEADER_SIZE:]
        
        try:
            length, command, message_id, received_checksum = struct.unpack(
                FastMCPProtocol.HEADER_FORMAT, 
                header
            )
        except struct.error:
            return None
        
        # 验证消息长度
        if length != len(data):
            return None
        
        # 验证校验和
        expected_checksum = FastMCPProtocol.calculate_checksum(header[:-2] + payload)
        if expected_checksum != received_checksum:
            return None
        
        return command, message_id, payload    