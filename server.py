import subprocess
import os
from flask import Flask, request, jsonify
from mcp.server.fastmcp import FastMCP

app = Flask(__name__)

# init MCP server
mcp_server = FastMCP("Zephyr build commands")

# Configuration for virtual environment
VENV_PATH = os.environ.get('ZEPHYR_VENV_PATH', '/path/to/your/zephyr-venv')
VENV_ACTIVATE = os.path.join(VENV_PATH, 'bin', 'activate')

def run_in_venv(cmd, **kwargs):
    """Run command in virtual environment"""
    # Create command that sources venv and runs the actual command
    venv_cmd = f"source {VENV_ACTIVATE} && {' '.join(cmd)}"
    return subprocess.run(venv_cmd, shell=True, **kwargs)

# regist tool
@mcp_server.tool()
def build(
    project_path: str,
    board: str = None,
    build_dir: str = "build",
    args: list = None,
    extra_args: list = None,
) -> dict:
    """
    Construct Zephyr project
    :param project_path: project path
    :param board: target board
    :param build_dir: build directoru
    :param args: build args
    :param extra_args: extra build extra args
    :return: build result
    """
    try:
        cmd = ["west", "build", "-d", build_dir, project_path]
        if board:
            cmd.extend(["-b", board])
        if args:
            # Handle all west build argument formats
            for arg in args:
                cmd.extend(arg)

        if extra_args:
            cmd.append("--")
            for arg in extra_args:
                cmd.extend(arg)

        result = run_in_venv(cmd, capture_output=True, text=True)
        return {"status": "success", "output": result.stdout}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# register flash tool
@mcp_server.tool()
def flash(device: str = None, runner: str = None, args: list = None) -> dict:
    """
    flash Zephyr firmware
    :param device: device
    :param runner: runner
    :param args: extra west flash parameter
    :return: flash result
    """
    try:
        cmd = ["west", "flash"]
        if device:
            cmd.extend(["--device", device])
        if runner:
            cmd.extend(["--runner", runner])
        if args:
            cmd.extend(args)

        result = run_in_venv(cmd, capture_output=True, text=True)
        return {"status": "success", "output": result.stdout}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.route("/build", methods=["POST"])
def build_zephyr():
    try:
        project_path = request.json.get("project_path")
        if not project_path or not os.path.exists(project_path):
            return jsonify({"error": "Invalid project path"}), 400

        build_dir = os.path.join(project_path, "build")
        os.makedirs(build_dir, exist_ok=True)

        cmd = [
            "west",
            "build",
            "-b",
            request.json.get("board", "native_posix"),
            project_path,
        ]

        result = run_in_venv(
            cmd,
            cwd=build_dir,
            capture_output=True,
            text=True,
        )

        return jsonify(
            {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/flash", methods=["POST"])
def flash_zephyr():
    try:
        project_path = request.json.get("project_path")
        if not project_path or not os.path.exists(project_path):
            return jsonify({"error": "Invalid project path"}), 400

        result = run_in_venv(
            ["west", "flash"],
            cwd=os.path.join(project_path, "build"),
            capture_output=True,
            text=True,
        )

        return jsonify(
            {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # start MCP{ server}
    mcp_server.start()

    # start Flask REST API
    app.run(host="0.0.0.0", port=5000)
