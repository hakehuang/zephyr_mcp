import subprocess
import os
import sys
from flask import Flask, request, jsonify
from mcp.server.fastmcp import FastMCP

app = Flask(__name__)

# init MCP server
mcp_server = FastMCP("Zephyr build commands")

# Configuration for virtual environment
VENV_PATH = os.environ.get("ZEPHYR_VENV_PATH", "/path/to/your/zephyr-venv")


def get_venv_paths():
    """Get virtual environment paths for current platform"""
    if sys.platform == "win32":
        # Windows paths
        venv_bin = os.path.join(VENV_PATH, "Scripts")
        python_exe = os.path.join(venv_bin, "python.exe")
        activate_script = os.path.join(venv_bin, "activate.bat")
    else:
        # Unix/Linux/macOS paths
        venv_bin = os.path.join(VENV_PATH, "bin")
        python_exe = os.path.join(venv_bin, "python")
        activate_script = os.path.join(venv_bin, "activate")

    return venv_bin, python_exe, activate_script


def get_venv_env():
    """Get environment variables for virtual environment"""
    venv_bin, python_exe, activate_script = get_venv_paths()

    env = os.environ.copy()
    env["VIRTUAL_ENV"] = VENV_PATH

    # Prepend venv bin directory to PATH
    if sys.platform == "win32":
        env["PATH"] = f"{venv_bin};{env['PATH']}"
    else:
        env["PATH"] = f"{venv_bin}:{env['PATH']}"

    # Remove PYTHONHOME if it exists to avoid conflicts
    env.pop("PYTHONHOME", None)
    return env


def run_with_venv(cmd, **kwargs):
    """Run command with virtual environment activated"""
    kwargs["env"] = get_venv_env()

    # On Windows, we might need shell=True for some commands
    if sys.platform == "win32" and "shell" not in kwargs:
        kwargs["shell"] = True

    return subprocess.run(cmd, **kwargs)


# Alternative approach using activation script
def run_in_venv_with_script(cmd, **kwargs):
    """Run command by activating venv first (Windows compatible)"""
    venv_bin, python_exe, activate_script = get_venv_paths()

    if sys.platform == "win32":
        # Windows batch command
        full_cmd = f'"{activate_script}" && {" ".join(cmd)}'
        kwargs["shell"] = True
    else:
        # Unix shell command
        full_cmd = f'. "{activate_script}" && {" ".join(cmd)}'
        kwargs["shell"] = True

    return subprocess.run(full_cmd, **kwargs)


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
                if isinstance(arg, list):
                    cmd.extend(arg)
                else:
                    cmd.append(arg)

        if extra_args:
            cmd.append("--")
            for arg in extra_args:
                if isinstance(arg, list):
                    cmd.extend(arg)
                else:
                    cmd.append(arg)

        result = run_with_venv(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return {"status": "success", "output": result.stdout}
        else:
            return {
                "status": "error",
                "message": result.stderr,
                "output": result.stdout,
            }
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
            if isinstance(args, list):
                cmd.extend(args)
            else:
                cmd.append(args)

        result = run_with_venv(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return {"status": "success", "output": result.stdout}
        else:
            return {
                "status": "error",
                "message": result.stderr,
                "output": result.stdout,
            }
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

        result = run_with_venv(
            [
                "west",
                "build",
                "-b",
                request.json.get("board", "native_posix"),
                project_path,
            ],
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

        result = run_with_venv(
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
