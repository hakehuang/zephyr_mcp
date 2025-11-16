import socket
import ssl
import sys
import threading
import time
import json
from typing import Optional

class MCPProxy:
    """MCP protocol proxy class responsible for forwarding data between local terminal and remote MCP server"""
    
    def __init__(self, remote_host: str, remote_port: int):
        """
        Initialize MCP proxy
        
        Args:
            remote_host: Remote MCP server hostname
            remote_port: Remote MCP server port
        """
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.input_buffer = bytearray()
        self.lock = threading.Lock()
        self.session_id = None
        self.mcp_path = "/mcp"
        
    def connect(self) -> bool:
        """Connect to remote MCP server"""
        try:
            # Create SSL context and wrap socket
            context = ssl.create_default_context()
            # For testing with self-signed certificates
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.server_socket = context.wrap_socket(
                socket.socket(socket.AF_INET, socket.SOCK_STREAM),
                server_hostname=self.remote_host
            )
            self.server_socket.connect((self.remote_host, self.remote_port))
            
            # Send initial connection status HTTP request
            json_request = {
                "jsonrpc": "2.0",
                "method": "executeCommand",
                "params": {"command": "connection_status_connected"},
                "id": int(time.time() * 1000)
            }
            json_data = json.dumps(json_request, separators=(',', ':')).encode('utf-8')
            
            http_request = (
                f"POST {self.mcp_path} HTTP/1.1\r\n"
                f"Host: {self.remote_host}{':' + str(self.remote_port) if self.remote_port not in (80, 443) else ''}\r\n"
                "User-Agent: Python-MCP-Proxy/1.0\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(json_data)}\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode('utf-8') + json_data
              # Debug: Log initial connection HTTP request
            sys.stderr.write(f"Sending initial connection request:\n{http_request.decode('utf-8', errors='replace')}\n")
            self.server_socket.sendall(http_request)
            self._initialize_session()
            return True
        except Exception as e:
            return False

    def _initialize_session(self):
        """Initialize MCP session (e.g., send authentication information)"""
        if not self.server_socket:
            return
            
        # Example: Send username/password for authentication
        # auth_command = f"AUTH username password\n"
        # self.server_socket.sendall(auth_command.encode('utf-8'))
        
        # Wait for authentication response
        #response = self.server_socket.recv(1024).decode('utf-8')
        #if "AUTH_SUCCESS" in response:
        #    print("Session initialized successfully")
            # Extract session ID (if available)
        #    self.session_id = response.split()[1] if len(response.split()) > 1 else None
        #else:
        #    print(f"Session initialization failed: {response}")
        #    self.disconnect()
        
    def disconnect(self):
        """Disconnect from remote server"""
        if self.server_socket:
            json_request = {
                "jsonrpc": "2.0",
                "method": "executeCommand",
                "params": {"command": "connection_status_disconnected"},
                "id": int(time.time() * 1000)
            }
            json_data = json.dumps(json_request, separators=(',', ':')).encode('utf-8')
            
            # Build HTTP request with proper headers
            http_request = (
                f"POST {self.mcp_path} HTTP/1.1\r\n"
                f"Host: {self.remote_host}{':' + str(self.remote_port) if self.remote_port not in (80, 443) else ''}\r\n"
                "User-Agent: Python-MCP-Proxy/1.0\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(json_data)}\r\n"
                "Connection: keep-alive\r\n"
                "\r\n"
            ).encode('utf-8') + json_data
            
            self.server_socket.sendall(http_request)
            self.server_socket.close()
            self.server_socket = None
            
    def start(self):
        """Start proxy service"""
        if not self.connect():
            return
            
        self.running = True
        
        # Start receive thread and input processing thread
        receive_thread = threading.Thread(target=self._receive_from_server)
        input_thread = threading.Thread(target=self._handle_user_input)
        
        receive_thread.daemon = True
        input_thread.daemon = True
        
        receive_thread.start()
        input_thread.start()
        
        try:
            # Main thread waits for exit signal
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass  # Exit signal handled internally
        finally:
            self.running = False
            self.disconnect()
            
    def _receive_from_server(self):
        """Receive data from server and display to terminal"""
        while self.running and self.server_socket:
            try:
                data = self.server_socket.recv(4096)
                if not data:
                    pass  # Server close handled by setting running=False
                    self.running = False
                    break
                    
                # Process HTTP response
                self.input_buffer.extend(data)
                
                # Check if we have a complete HTTP response
                if b'\r\n\r\n' in self.input_buffer:
                    # Split headers and body
                    header_end = self.input_buffer.find(b'\r\n\r\n') + 4
                    headers = self.input_buffer[:header_end].decode('utf-8')
                    body = self.input_buffer[header_end:]
                    
                    # Extract Content-Length from headers
                    content_length = 0
                    for line in headers.split('\r\n'):
                        if line.lower().startswith('content-length:'):
                            content_length = int(line.split(':')[1].strip())
                            break
                    
                    # Check if we have received the entire body
                    if len(body) >= content_length:
                        # Process the complete response
                        json_response = body[:content_length].decode('utf-8')
                        try:
                            response_data = json.loads(json_response)
                            # Handle JSON-RPC response if needed
                            if 'error' in response_data:
                                sys.stderr.write(f"Server error: {response_data['error']}\n")
                        except json.JSONDecodeError:
                            sys.stderr.write(f"Invalid JSON response: {json_response}\n")
                        
                        # Remove processed data from buffer
                        self.input_buffer = self.input_buffer[header_end + content_length:]
                    else:
                        # Not enough data yet, keep accumulating
                        pass
                else:
                    # Continue accumulating data
                    pass
                
            except Exception as e:
                if self.running:
                    pass  # Receive errors handled by stopping proxy
                self.running = False
                break
                
    def _handle_user_input(self):
        """Process user input and send to server"""
        while self.running:
            try:
                # Read a line of user input
                user_input = sys.stdin.readline().lstrip('>').strip()
                
                if not user_input:
                    # User pressed Ctrl+D
                    self.running = False
                    break
                    
                # Send raw JSON with newline delimiter
                json_request = {
                      "jsonrpc": "2.0",
                      "method": "executeCommand",
                      "params": {"command": user_input.strip()},
                      "id": int(time.time() * 1000)
                  }
                  
                json_data = json.dumps(json_request, separators=(',', ':')).encode('utf-8')
                
                # Build HTTP request with proper headers
                http_request = (
                    f"POST {self.mcp_path} HTTP/1.1\r\n"
                    f"Host: {self.remote_host}{':' + str(self.remote_port) if self.remote_port not in (80, 443) else ''}\r\n"
                    "User-Agent: Python-MCP-Proxy/1.0\r\n"
                    "Content-Type: application/json\r\n"
                    f"Content-Length: {len(json_data)}\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                ).encode('utf-8') + json_data
                  

                  
                if self.server_socket:
                      # Debug: Log HTTP request
                      # Debug: Log HTTP request with safe decoding
                      sys.stderr.write(f"Sending HTTP request:\n{http_request.decode('utf-8', errors='replace')}\n")
                      # Debug: Log user input HTTP request
                sys.stderr.write(f"Sending user input request:\n{http_request.decode('utf-8', errors='replace')}\n")
                self.server_socket.sendall(http_request)
                    
                # Removed prompt to prevent JSON parsing issues
                    
            except Exception as e:
                if self.running:
                    pass  # Input errors handled by stopping proxy
                self.running = False
                break

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        sys.stderr.write("Usage: python mcp_proxy.py <remote_host> [remote_port]\n")
        sys.stderr.write("Example: python mcp_proxy.py localhost 443\n")
        sys.exit(1)
         
    remote_host = sys.argv[1]
    remote_port = int(sys.argv[2]) if len(sys.argv) > 2 else 443
    
    # Create and start proxy
    proxy = MCPProxy(remote_host, remote_port)
    proxy.start()