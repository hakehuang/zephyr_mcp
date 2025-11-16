# VSC-MCP TCP Framework

A modular TCP communication framework for device management and data exchange, featuring a base class architecture for code reuse and protocol-specific implementations.

## Project Structure

```
vsc-mcp-tcp-framework/
├── tcp_base_client.py      # Base TCP client implementation with shared functionality
├── fastmcp_client.py       # FastMCP protocol client
├── vsc_mcp_client.py       # VSC MCP protocol client
├── fastmcp_server.py       # FastMCP protocol server
├── vsc_mcp_server.py       # VSC MCP protocol server
├── fastmcp_protocol.py     # FastMCP protocol message handling
├── device_manager.py       # Device management service
├── remote_controller.py    # Remote device control service
└── data_collector.py       # Device data collection service
```

## Key Components

### Base Client Architecture
The framework uses a base class pattern to eliminate code duplication:

- **TCPClientBase** (`tcp_base_client.py`)
  - Connection management with retry logic
  - Thread handling for message reception
  - Message handler registration
  - Message ID generation

### Protocol Implementations
- **FastMCP** (`fastmcp_client.py`, `fastmcp_server.py`, `fastmcp_protocol.py`)
  - Binary protocol with message headers and checksum validation
  - Efficient buffer management for message parsing

- **VSC MCP** (`vsc_mcp_client.py`, `vsc_mcp_server.py`)
  - JSON-based message protocol
  - Human-readable message format

### Service Modules
- **DeviceManager**: Tracks connected devices and their status
- **RemoteController**: Sends commands to devices and handles responses
- **DataCollector**: Periodically collects and stores device data

## Usage Examples

### Creating a Client Connection

```python
# FastMCP Client Example
from fastmcp_client import FastMCPClient

client = FastMCPClient(host='localhost', port=9999)
if client.connect():
    # Register message handlers
    def handle_connect_ack(client, command, message_id, payload):
        print(f"Connection acknowledged: {payload}")

    client.register_handler(b'CA', handle_connect_ack)
    client.send_message(b'CN', b'Client connected')
    # ...
    client.disconnect()
```

### Starting a Server

```python
# FastMCP Server Example
from fastmcp_server import FastMCPServer

server = FastMCPServer(host='localhost', port=9999)
if server.start():
    # Register message handlers
    def handle_connect(server, client_socket, client_addr, command, msg_id, payload):
        print(f"New connection from {client_addr}")
        server.send_message(client_socket, b'CA', b'Connection accepted')

    server.register_handler(b'CN', handle_connect)
    # Keep server running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
```

## Services Usage

### Device Manager
```python
from device_manager import DeviceManager

manager = DeviceManager()
manager.start()
# Get connected devices
print(manager.get_device_list())
# Send command to device
manager.send_command_to_device('device1', b'SETP', b'05')
```

### Data Collector
```python
from data_collector import DataCollector

collector = DataCollector()
collector.start()
# Get collected data
print(collector.get_device_data('device1'))
```

## Protocol Specifications

### FastMCP Protocol
- Binary format with fixed-size headers
- Structure: [Length (4 bytes)][Command (2 bytes)][Message ID (4 bytes)][Checksum (2 bytes)][Payload]
- Checksum validation for data integrity

### VSC MCP Protocol
- JSON-based message format
- Structure: `{"command": "string", "params": {}, "id": "string"}`
- Human-readable for easier debugging

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.