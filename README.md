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

### VS Code Integration

This project includes VS Code configurations for easy development and debugging:

#### Running the Server
1. Open the project in VS Code
2. Open the Command Palette (Ctrl+Shift+P or Cmd+Shift+P)
3. Run the task: `Tasks: Run Build Task` (or press Ctrl+Shift+B)
4. Select `Start MCP Server` from the task list

#### Debugging the Server
1. Open the Run and Debug view (Ctrl+Shift+D or Cmd+Shift+D)
2. Select `Debug MCP Server` from the configuration dropdown
3. Click the green play button or press F5 to start debugging

### API Endpoints

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