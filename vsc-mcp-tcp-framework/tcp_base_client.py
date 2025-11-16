import socket
import threading
import time
from typing import Dict, Callable, Optional, Any

class TCPClientBase:
    """Base TCP client class providing common functionality for TCP communication"""
    def __init__(self, host: str = 'localhost', port: int = 9999):
        self.host = host
        self.port = port
        self.client_socket: Optional[socket.socket] = None
        self.message_handlers: Dict[Any, Callable] = {}
        self.is_connected: bool = False
        self.receive_thread: Optional[threading.Thread] = None
        self.message_id_counter: int = 0

    def connect(self, max_retries: int = 3, retry_delay: int = 1) -> bool:
        """Connect to server with retry logic"""
        retries = 0
        while retries < max_retries:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.host, self.port))
                self.is_connected = True
                print(f"Connected to server {self.host}:{self.port}")
                self._start_receive_thread()
                return True
            except Exception as e:
                retries += 1
                print(f"Connection attempt {retries} failed: {e}")
                if retries < max_retries:
                    time.sleep(retry_delay)
        print("Max retries reached, connection failed")
        return False

    def disconnect(self) -> None:
        """Disconnect from server and clean up resources"""
        self.is_connected = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except Exception as e:
                print(f"Error closing socket: {e}")
            self.client_socket = None
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
        print("Disconnected from server")

    def register_handler(self, command: Any, handler: Callable) -> None:
        """Register a handler for specific message commands"""
        self.message_handlers[command] = handler

    def _start_receive_thread(self) -> None:
        """Start the background thread for receiving messages"""
        self.receive_thread = threading.Thread(target=self._receive_messages)
        self.receive_thread.daemon = True
        self.receive_thread.start()

    def _receive_messages(self) -> None:
        """Receive messages from server - to be implemented by subclass"""
        raise NotImplementedError("Subclasses must implement _receive_messages method")

    def send_message(self, *args, **kwargs) -> None:
        """Send message to server - to be implemented by subclass"""
        raise NotImplementedError("Subclasses must implement send_message method")

    def _process_message(self, *args, **kwargs) -> None:
        """Process received message - to be implemented by subclass"""
        raise NotImplementedError("Subclasses must implement _process_message method")

    def _get_next_message_id(self) -> int:
        """Generate sequential message IDs"""
        self.message_id_counter = (self.message_id_counter + 1) % 0xFFFFFFFF
        return self.message_id_counter