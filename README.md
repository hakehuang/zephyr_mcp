# Zephyr MCP Server

A Microcontroller Programming Server for building and flashing Zephyr projects.

## Requirements
- Python 3.6+
- West tool (Zephyr RTOS)
- Flask (will be installed via requirements.txt)

## Installation
1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`

## Usage
1. Run the server: `python server.py`
2. Send POST requests to:
   - `/build` - Build a Zephyr project
     - Parameters: `project_path` (required), `board` (optional, default: native_posix)
   - `/flash` - Flash a built Zephyr project
     - Parameters: `project_path` (required)

## Example Requests
```bash
# Build
curl -X POST -H "Content-Type: application/json" -d '{"project_path":"/path/to/zephyr_project"}' http://localhost:5000/build

# Flash
curl -X POST -H "Content-Type: application/json" -d '{"project_path":"/path/to/zephyr_project"}' http://localhost:5000/flash
```

## Notes
- Make sure Zephyr environment is properly set up before using this server
- The server must have access to the west tool and Zephyr SDK