import subprocess
import os
from flask import Flask, request, jsonify
from mcp import MCPServer

app = Flask(__name__)

# 初始化MCP服务器
mcp_server = MCPServer("Zephyr Build Server")

# 注册构建工具
@mcp_server.tool()
def build(project_path: str, board: str = None,
            build_dir: str = 'build', args: list = None,
            extra_args: list = None) -> dict:
    """
    构建Zephyr项目
    :param project_path: 项目路径
    :param board: 目标开发板
    :param build_dir: 构建目录
    :param args: 额外west build参数
    :return: 构建结果
    """
    try:
        cmd = ['west', 'build', '-d', build_dir, project_path]
        if board:
            cmd.extend(['-b', board])
        if args:
            # Handle all west build argument formats
            for arg in args:
                cmd.extend(arg)

        if extra_args:
            cmd.append("--")
            for arg in extra_args:
                cmd.extend(arg)
            
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        return {"status": "success", "output": result.stdout}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 注册烧录工具
@mcp_server.tool()
def flash(device: str = None, runner: str = None, args: list = None) -> dict:
    """
    烧录Zephyr固件
    :param device: 设备标识
    :param runner: 烧录runner
    :param args: 额外west flash参数
    :return: 烧录结果
    """
    try:
        cmd = ['west', 'flash']
        if device:
            cmd.extend(['--device', device])
        if runner:
            cmd.extend(['--runner', runner])
        if args:
            cmd.extend(args)
            
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        return {"status": "success", "output": result.stdout}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/build', methods=['POST'])
def build_zephyr():
    try:
        project_path = request.json.get('project_path')
        if not project_path or not os.path.exists(project_path):
            return jsonify({'error': 'Invalid project path'}), 400
            
        build_dir = os.path.join(project_path, 'build')
        os.makedirs(build_dir, exist_ok=True)
        
        result = subprocess.run(
            ['west', 'build', '-b', request.json.get('board', 'native_posix'), project_path],
            cwd=build_dir,
            capture_output=True,
            text=True
        )
        
        return jsonify({
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/flash', methods=['POST'])
def flash_zephyr():
    try:
        project_path = request.json.get('project_path')
        if not project_path or not os.path.exists(project_path):
            return jsonify({'error': 'Invalid project path'}), 400
            
        result = subprocess.run(
            ['west', 'flash'],
            cwd=os.path.join(project_path, 'build'),
            capture_output=True,
            text=True
        )
        
        return jsonify({
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 启动MCP服务器
    mcp_server.start()
    
    # 启动Flask REST API
    app.run(host='0.0.0.0', port=5000)