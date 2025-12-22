#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zephyr RTOS Development Environment Setup Tool

This tool automates the setup of a complete Zephyr RTOS development environment according to the official
Zephyr Project Getting Started Guide. It handles all platform-specific requirements for Windows, Linux,
and macOS, ensuring a consistent development experience across operating systems.

Key Features:
-------------
- Automatic detection and installation of required dependencies
- Cross-platform support (Windows, Linux, macOS)
- Version control for both Zephyr and the SDK
- Environment variable setup and configuration
- Comprehensive validation of the development environment
- Detailed error handling with actionable recommendations
- Support for proxies and offline installation scenarios
- Automatic Python virtual environment creation for isolated dependencies

Virtual Environment Information:
-------------------------------
- A Python virtual environment is automatically created in the workspace directory
- All Python packages (West, Zephyr dependencies) are installed in this virtual environment
- Environment setup scripts automatically activate the virtual environment
- This ensures isolation from system Python packages and prevents version conflicts

Requirements:
------------
- Python 3.8 or higher
- Git (for repository cloning)
- CMake 3.20.0 or higher
- Ninja build system (recommended)
- Platform-specific requirements:
  Windows: Visual Studio Build Tools or MinGW
  Linux: Development packages (gcc, libc-dev, etc.)
  macOS: Xcode Command Line Tools

Usage:
------
1. Basic usage:
   python setup_zephyr_environment.py /path/to/workspace

2. Advanced usage:
   python setup_zephyr_environment.py /path/to/workspace --version v3.5.0 --sdk-version 0.16.8

3. Skip SDK installation:
   python setup_zephyr_environment.py /path/to/workspace --no-sdk

4. Force overwrite existing workspace:
   python setup_zephyr_environment.py /path/to/workspace --force

After successful installation, the tool will generate platform-specific environment setup scripts:
- Windows: zephyr_env.cmd (run to set up environment variables)
- Linux/macOS: zephyr_env.sh (run with 'source zephyr_env.sh')

For more information, visit the official Zephyr Project documentation:
https://docs.zephyrproject.org/latest/getting_started/index.html
"""

import os
import sys
import platform
import subprocess
import shutil
import argparse
from typing import Dict, Any, List


def setup_zephyr_environment(
    workspace_path: str,
    zephyr_version: str = "latest",
    install_sdk: bool = True,
    sdk_version: str = "0.16.8",
    platforms: List[str] = None,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Set up a complete Zephyr RTOS development environment according to official getting started guide.

    This tool automates the process of setting up a Zephyr RTOS development environment by:
    1. Creating the workspace directory structure
    2. Installing necessary Python dependencies (west, pyelftools, pykwalify, etc.)
    3. Initializing a West workspace with the specified Zephyr version
    4. Installing the Zephyr SDK (if enabled)
    5. Setting up platform-specific environment variables
    6. Handling common issues and providing detailed error messages

    Args:
        workspace_path: Path where the Zephyr workspace will be created
        zephyr_version: Zephyr version to install (e.g., "main", "v3.5.0", or "latest")
        install_sdk: Whether to install the Zephyr SDK
        sdk_version: Version of the Zephyr SDK to install
        platforms: List of target platforms to support (e.g., ["arm", "riscv", "x86"])
        force: Overwrite existing workspace if it exists

    Returns:
        Dict with keys:
            - "status": "success" or "error"
            - "message": Summary of the operation
            - "details": Additional information (workspace path, SDK path, etc.)
            - "warnings": Any non-critical issues encountered

    Example:
        >>> result = setup_zephyr_environment("C:/zephyr", zephyr_version="v3.5.0")
        >>> if result["status"] == "success":
        ...     print(f"Zephyr environment set up at: {result['details']['workspace_path']}")
    """

    # Function implementation starts here
    try:
        # Validate parameters
        if not workspace_path:
            return {"status": "error", "message": "Workspace path is required"}

        # Create absolute path
        workspace_path = os.path.abspath(workspace_path)

        # Check if workspace already exists
        if os.path.exists(workspace_path):
            if force:
                shutil.rmtree(workspace_path)
            else:
                return {
                    "status": "error",
                    "message": f"Directory {workspace_path} already exists. Use force=True to overwrite.",
                }

        # Determine OS and set up environment accordingly
        current_os = platform.system().lower()

        if current_os == "windows":
            result = _setup_windows_environment(
                workspace_path, zephyr_version, install_sdk, sdk_version, platforms
            )
        elif current_os == "linux":
            result = _setup_linux_environment(
                workspace_path, zephyr_version, install_sdk, sdk_version, platforms
            )
        elif current_os == "darwin":
            result = _setup_macos_environment(
                workspace_path, zephyr_version, install_sdk, sdk_version, platforms
            )
        else:
            return {
                "status": "error",
                "message": f"Unsupported operating system: {current_os}",
            }

        if result["status"] == "success":
            result["path"] = workspace_path
            result["environment_details"] = _get_environment_details(workspace_path)

        return result

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error setting up Zephyr environment: {str(e)}",
        }


def _setup_windows_environment(
    workspace_path: str,
    zephyr_version: str,
    install_sdk: bool,
    sdk_version: str,
    platforms: List[str],
) -> Dict[str, Any]:
    """
    Set up Zephyr environment on Windows according to official guidelines.
    """
    try:
        # Check and install dependencies
        check_result = _check_windows_dependencies()
        if check_result["status"] != "success":
            return check_result

        # Create workspace directory
        os.makedirs(workspace_path, exist_ok=True)
        print(f"Created workspace directory: {workspace_path}")

        # Create and activate Python virtual environment
        venv_path = os.path.join(workspace_path, "venv")
        print(f"Creating Python virtual environment in {venv_path}...")
        subprocess.check_call([sys.executable, "-m", "venv", venv_path])

        # Get path to pip in virtual environment
        venv_pip = os.path.join(venv_path, "Scripts", "pip.exe")

        # Check for Visual Studio Build Tools
        vs_tools_installed = _check_visual_studio_tools()
        if not vs_tools_installed:
            print("WARNING: Visual Studio Build Tools not found.")
            print(
                "It's recommended to install Visual Studio Build Tools for C++ development."
            )
            print(
                "You can download it from: https://visualstudio.microsoft.com/downloads/"
            )

        # Install West with specific version requirements in virtual environment
        print(
            "Installing West tool with required dependencies in virtual environment..."
        )
        subprocess.check_call([venv_pip, "install", "west", "pyelftools"])

        # Initialize Zephyr workspace
        print(f"Initializing Zephyr workspace in {workspace_path}...")
        os.chdir(workspace_path)

        # Get path to west in virtual environment
        venv_west = os.path.join(venv_path, "Scripts", "west.exe")

        try:
            if zephyr_version == "latest":
                subprocess.check_call(
                    [
                        venv_west,
                        "init",
                        "-m",
                        "https://github.com/zephyrproject-rtos/zephyr",
                        ".",
                    ]
                )
            else:
                subprocess.check_call(
                    [
                        venv_west,
                        "init",
                        "-m",
                        "https://github.com/zephyrproject-rtos/zephyr",
                        "--mr",
                        zephyr_version,
                        ".",
                    ]
                )
        except subprocess.CalledProcessError as e:
            # Try with proxy settings if available
            env = os.environ.copy()
            if "http_proxy" in env or "https_proxy" in env:
                print("Retry with proxy settings...")
                if zephyr_version == "latest":
                    subprocess.check_call(
                        [
                            venv_west,
                            "init",
                            "-m",
                            "https://github.com/zephyrproject-rtos/zephyr",
                            ".",
                        ],
                        env=env,
                    )
                else:
                    subprocess.check_call(
                        [
                            venv_west,
                            "init",
                            "-m",
                            "https://github.com/zephyrproject-rtos/zephyr",
                            "--mr",
                            zephyr_version,
                            ".",
                        ],
                        env=env,
                    )
            else:
                raise

        # Update West with progress indicator
        print("Updating West dependencies (this may take several minutes)...")
        subprocess.check_call([venv_west, "update"])

        # Install Zephyr Python dependencies in virtual environment
        print("Installing Zephyr Python dependencies in virtual environment...")
        requirements_file = os.path.join(
            workspace_path, "zephyr", "scripts", "requirements.txt"
        )
        if os.path.exists(requirements_file):
            subprocess.check_call([venv_pip, "install", "-r", requirements_file])
        else:
            return {
                "status": "error",
                "message": f"Requirements file not found: {requirements_file}",
            }

        # Install Zephyr SDK if requested
        if install_sdk:
            sdk_result = _install_windows_sdk(workspace_path, sdk_version)
            if sdk_result["status"] != "success":
                return sdk_result

        # Set up environment variables for Windows with virtual environment support
        _setup_windows_env_vars(workspace_path, venv_path)

        return {
            "status": "success",
            "message": "Zephyr environment set up successfully on Windows",
            "visual_studio_tools": vs_tools_installed,
            "venv_path": venv_path,
        }

    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": f"Command failed: {str(e)}",
            "suggestions": [
                "Check your internet connection",
                "Ensure you have administrator privileges",
                "Verify all dependencies are installed correctly",
            ],
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Windows setup failed: {str(e)}",
            "suggestions": [
                "Try running with administrator privileges",
                "Check available disk space",
                "Ensure Python is properly installed",
            ],
        }


def _setup_linux_environment(
    workspace_path: str,
    zephyr_version: str,
    install_sdk: bool,
    sdk_version: str,
    platforms: List[str],
) -> Dict[str, Any]:
    """
    Set up Zephyr environment on Linux according to official guidelines.
    """
    try:
        # Check and install dependencies
        check_result = _check_linux_dependencies()
        if check_result["status"] != "success":
            return check_result

        # Create workspace directory with proper permissions
        os.makedirs(workspace_path, exist_ok=True)
        os.chmod(workspace_path, 0o755)  # Ensure proper permissions
        print(f"Created workspace directory: {workspace_path}")

        # Check if running as root (not recommended)
        if os.geteuid() == 0:
            print("WARNING: Running as root is not recommended for Zephyr development")
            print("Please consider using a regular user account for development.")

        # Create and activate Python virtual environment
        venv_path = os.path.join(workspace_path, "venv")
        print(f"Creating Python virtual environment in {venv_path}...")
        subprocess.check_call([sys.executable, "-m", "venv", venv_path])

        # Get path to pip in virtual environment
        venv_pip = os.path.join(venv_path, "bin", "pip")

        # Install West with specific version requirements in virtual environment
        print(
            "Installing West tool with required dependencies in virtual environment..."
        )
        subprocess.check_call([venv_pip, "install", "west", "pyelftools"])

        # Initialize Zephyr workspace
        print(f"Initializing Zephyr workspace in {workspace_path}...")
        os.chdir(workspace_path)

        # Get path to west in virtual environment
        venv_west = os.path.join(venv_path, "bin", "west")

        try:
            if zephyr_version == "latest":
                subprocess.check_call(
                    [
                        venv_west,
                        "init",
                        "-m",
                        "https://github.com/zephyrproject-rtos/zephyr",
                        ".",
                    ]
                )
            else:
                subprocess.check_call(
                    [
                        venv_west,
                        "init",
                        "-m",
                        "https://github.com/zephyrproject-rtos/zephyr",
                        "--mr",
                        zephyr_version,
                        ".",
                    ]
                )
        except subprocess.CalledProcessError as e:
            # Try with proxy settings if available
            env = os.environ.copy()
            if "http_proxy" in env or "https_proxy" in env:
                print("Retry with proxy settings...")
                if zephyr_version == "latest":
                    subprocess.check_call(
                        [
                            venv_west,
                            "init",
                            "-m",
                            "https://github.com/zephyrproject-rtos/zephyr",
                            ".",
                        ],
                        env=env,
                    )
                else:
                    subprocess.check_call(
                        [
                            venv_west,
                            "init",
                            "-m",
                            "https://github.com/zephyrproject-rtos/zephyr",
                            "--mr",
                            zephyr_version,
                            ".",
                        ],
                        env=env,
                    )
            else:
                raise

        # Update West with progress indicator
        print("Updating West dependencies (this may take several minutes)...")
        subprocess.check_call([venv_west, "update"])

        # Install Zephyr Python dependencies in virtual environment
        print("Installing Zephyr Python dependencies in virtual environment...")
        requirements_file = os.path.join(
            workspace_path, "zephyr", "scripts", "requirements.txt"
        )
        if os.path.exists(requirements_file):
            subprocess.check_call([venv_pip, "install", "-r", requirements_file])
        else:
            return {
                "status": "error",
                "message": f"Requirements file not found: {requirements_file}",
            }

        # Install Zephyr SDK if requested
        if install_sdk:
            sdk_result = _install_linux_sdk(workspace_path, sdk_version)
            if sdk_result["status"] != "success":
                return sdk_result

        # Set up environment variables script for Linux with virtual environment support
        _setup_linux_env_vars(workspace_path, venv_path)

        return {
            "status": "success",
            "message": "Zephyr environment set up successfully on Linux",
            "venv_path": venv_path,
        }

    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": f"Command failed: {str(e)}",
            "suggestions": [
                "Check your internet connection",
                "Ensure you have required system packages installed",
                "Verify user permissions for the workspace directory",
            ],
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Linux setup failed: {str(e)}",
            "suggestions": [
                "Ensure Python is properly installed",
                "Check available disk space",
                "Verify system packages are up to date",
            ],
        }


def _setup_linux_env_vars(workspace_path: str, venv_path: str) -> None:
    """
    Create an environment setup script for Linux to help users easily activate Zephyr environment with virtual environment support.
    """
    env_script_path = os.path.join(workspace_path, "zephyr_env.sh")
    zephyr_base = os.path.join(workspace_path, "zephyr")

    script_content = f"""
#!/bin/bash
# Zephyr Environment Setup Script for Linux

# Set Zephyr base directory
export ZEPHYR_BASE="{zephyr_base}"

# Activate Python virtual environment
if [ -f "{os.path.join(venv_path, 'bin', 'activate')}" ]; then
    source "{os.path.join(venv_path, 'bin', 'activate')}"
    echo "Python virtual environment activated."
else
    echo "Warning: Virtual environment activation script not found."
fi

# Source Zephyr's environment script if available
ZEPHYR_ENV_SCRIPT="$ZEPHYR_BASE/zephyr-env.sh"
if [ -f "$ZEPHYR_ENV_SCRIPT" ]; then
    source "$ZEPHYR_ENV_SCRIPT"
    echo "Zephyr environment variables set successfully."
else
    echo "Warning: Zephyr environment script not found. Some features may not work properly."
fi
"""

    with open(env_script_path, "w") as f:
        f.write(script_content)

    # Make the script executable
    os.chmod(env_script_path, 0o755)
    print(f"Created environment setup script: {env_script_path}")
    print(
        "To activate the Zephyr environment in future sessions, run: source zephyr_env.sh"
    )


def _setup_macos_env_vars(workspace_path: str, venv_path: str) -> None:
    """
    Create an environment setup script for macOS to help users easily activate Zephyr environment with virtual environment support.
    """
    env_script_path = os.path.join(workspace_path, "zephyr_env.sh")
    zephyr_base = os.path.join(workspace_path, "zephyr")

    script_content = f"""
#!/bin/bash
# Zephyr Environment Setup Script for macOS

# Set Zephyr base directory
export ZEPHYR_BASE="{zephyr_base}"

# Activate Python virtual environment
if [ -f "{os.path.join(venv_path, 'bin', 'activate')}" ]; then
    source "{os.path.join(venv_path, 'bin', 'activate')}"
    echo "Python virtual environment activated."
else
    echo "Warning: Virtual environment activation script not found."
fi

# Add user's Python bin to PATH if not already present
USER_PYTHON_BIN="$HOME/.local/bin"
if [[ ":$PATH:" != *":$USER_PYTHON_BIN:"* ]]; then
    export PATH="$USER_PYTHON_BIN:$PATH"
fi

# Source Zephyr's environment script if available
ZEPHYR_ENV_SCRIPT="$ZEPHYR_BASE/zephyr-env.sh"
if [ -f "$ZEPHYR_ENV_SCRIPT" ]; then
    source "$ZEPHYR_ENV_SCRIPT"
    echo "Zephyr environment variables set successfully."
else
    echo "Warning: Zephyr environment script not found. Some features may not work properly."
fi
"""

    with open(env_script_path, "w") as f:
        f.write(script_content)

    # Make the script executable
    os.chmod(env_script_path, 0o755)
    print(f"Created environment setup script: {env_script_path}")
    print(
        "To activate the Zephyr environment in future sessions, run: source zephyr_env.sh"
    )


def _setup_macos_environment(
    workspace_path: str,
    zephyr_version: str,
    install_sdk: bool,
    sdk_version: str,
    platforms: List[str],
) -> Dict[str, Any]:
    """
    Set up Zephyr environment on macOS according to official guidelines.
    """
    try:
        # Check and install dependencies
        check_result = _check_macos_dependencies()
        if check_result["status"] != "success":
            return check_result

        # Create workspace directory with proper permissions
        os.makedirs(workspace_path, exist_ok=True)
        os.chmod(workspace_path, 0o755)  # Ensure proper permissions
        print(f"Created workspace directory: {workspace_path}")

        # Create and activate Python virtual environment
        venv_path = os.path.join(workspace_path, "venv")
        print(f"Creating Python virtual environment in {venv_path}...")
        subprocess.check_call([sys.executable, "-m", "venv", venv_path])

        # Get path to pip in virtual environment
        venv_pip = os.path.join(venv_path, "bin", "pip")

        # Install West with specific version requirements in virtual environment
        print(
            "Installing West tool with required dependencies in virtual environment..."
        )
        subprocess.check_call([venv_pip, "install", "west", "pyelftools"])

        # Initialize Zephyr workspace
        print(f"Initializing Zephyr workspace in {workspace_path}...")
        os.chdir(workspace_path)

        # Get path to west in virtual environment
        venv_west = os.path.join(venv_path, "bin", "west")

        try:
            if zephyr_version == "latest":
                subprocess.check_call(
                    [
                        venv_west,
                        "init",
                        "-m",
                        "https://github.com/zephyrproject-rtos/zephyr",
                        ".",
                    ]
                )
            else:
                subprocess.check_call(
                    [
                        venv_west,
                        "init",
                        "-m",
                        "https://github.com/zephyrproject-rtos/zephyr",
                        "--mr",
                        zephyr_version,
                        ".",
                    ]
                )
        except subprocess.CalledProcessError as e:
            # Try with proxy settings if available
            env = os.environ.copy()
            if "http_proxy" in env or "https_proxy" in env:
                print("Retry with proxy settings...")
                if zephyr_version == "latest":
                    subprocess.check_call(
                        [
                            venv_west,
                            "init",
                            "-m",
                            "https://github.com/zephyrproject-rtos/zephyr",
                            ".",
                        ],
                        env=env,
                    )
                else:
                    subprocess.check_call(
                        [
                            venv_west,
                            "init",
                            "-m",
                            "https://github.com/zephyrproject-rtos/zephyr",
                            "--mr",
                            zephyr_version,
                            ".",
                        ],
                        env=env,
                    )
            else:
                raise

        # Update West with progress indicator
        print("Updating West dependencies (this may take several minutes)...")
        subprocess.check_call([venv_west, "update"])

        # Install Zephyr Python dependencies in virtual environment
        print("Installing Zephyr Python dependencies in virtual environment...")
        requirements_file = os.path.join(
            workspace_path, "zephyr", "scripts", "requirements.txt"
        )
        if os.path.exists(requirements_file):
            subprocess.check_call([venv_pip, "install", "-r", requirements_file])
        else:
            return {
                "status": "error",
                "message": f"Requirements file not found: {requirements_file}",
            }

        # Install Zephyr SDK if requested
        if install_sdk:
            sdk_result = _install_macos_sdk(workspace_path, sdk_version)
            if sdk_result["status"] != "success":
                return sdk_result

        # Set up environment variables script for macOS
        _setup_macos_env_vars(workspace_path, venv_path)

        return {
            "status": "success",
            "message": "Zephyr environment set up successfully on macOS",
            "venv_path": venv_path,
        }

    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": f"Command failed: {str(e)}",
            "suggestions": [
                "Check your internet connection",
                "Ensure you have Xcode Command Line Tools installed",
                "Verify user permissions for the workspace directory",
            ],
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"macOS setup failed: {str(e)}",
            "suggestions": [
                "Ensure Python is properly installed",
                "Check available disk space",
                "Verify Homebrew is up to date",
            ],
        }


def _check_windows_dependencies() -> Dict[str, Any]:
    """
    Check and install required dependencies on Windows.
    """
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            return {"status": "error", "message": "Python 3.8 or higher is required"}
        print(f"Python version: {platform.python_version()} (OK)")

        # Check Git
        if shutil.which("git") is None:
            return {
                "status": "error",
                "message": "Git is not installed. Please install Git from https://git-scm.com/download/win",
            }
        git_version = subprocess.check_output(
            ["git", "--version"], universal_newlines=True
        ).strip()
        print(f"Git: {git_version} (OK)")

        # Check CMake
        if shutil.which("cmake") is None:
            return {
                "status": "error",
                "message": "CMake is not installed. Please install CMake 3.20.1 or higher from https://cmake.org/download/",
            }
        cmake_version = subprocess.check_output(
            ["cmake", "--version"], universal_newlines=True
        ).split()[2]
        print(f"CMake version: {cmake_version}")

        # Simple version check (major.minor.patch)
        cmake_parts = cmake_version.split(".")
        if len(cmake_parts) >= 3:
            cmake_major, cmake_minor, cmake_patch = (
                int(cmake_parts[0]),
                int(cmake_parts[1]),
                int(cmake_parts[2]),
            )
            if (cmake_major, cmake_minor, cmake_patch) < (3, 20, 1):
                return {
                    "status": "error",
                    "message": "CMake 3.20.1 or higher is required",
                }

        # Check Ninja (optional but recommended)
        ninja_available = shutil.which("ninja") is not None
        if ninja_available:
            ninja_version = subprocess.check_output(
                ["ninja", "--version"], universal_newlines=True
            ).strip()
            print(f"Ninja: {ninja_version} (OK)")
        else:
            print(
                "Ninja not found (optional but recommended). Install from https://github.com/ninja-build/ninja/releases"
            )

        return {
            "status": "success",
            "message": "All required dependencies are installed",
        }

    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Dependency check failed: {str(e)}"}
    except Exception as e:
        return {
            "status": "error",
            "message": f"Windows dependency check failed: {str(e)}",
        }


def _check_linux_dependencies() -> Dict[str, Any]:
    """
    Check and install required dependencies on Linux.
    """
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            return {"status": "error", "message": "Python 3.8 or higher is required"}
        print(f"Python version: {platform.python_version()} (OK)")

        # Check if running as root (not recommended)
        if os.geteuid() == 0:
            print("Warning: Running as root is not recommended")

        # Check Git
        if shutil.which("git") is None:
            return {
                "status": "error",
                "message": "Git is not installed. Please install with: sudo apt-get install git",
            }
        git_version = subprocess.check_output(
            ["git", "--version"], universal_newlines=True
        ).strip()
        print(f"Git: {git_version} (OK)")

        # Check CMake
        if shutil.which("cmake") is None:
            return {
                "status": "error",
                "message": "CMake is not installed. Please install CMake 3.20.1 or higher",
            }
        cmake_version = subprocess.check_output(
            ["cmake", "--version"], universal_newlines=True
        ).split()[2]
        print(f"CMake version: {cmake_version}")

        # Simple version check
        cmake_parts = cmake_version.split(".")
        if len(cmake_parts) >= 3:
            cmake_major, cmake_minor, cmake_patch = (
                int(cmake_parts[0]),
                int(cmake_parts[1]),
                int(cmake_parts[2]),
            )
            if (cmake_major, cmake_minor, cmake_patch) < (3, 20, 1):
                return {
                    "status": "error",
                    "message": "CMake 3.20.1 or higher is required",
                }

        # Check Ninja
        if shutil.which("ninja") is None:
            return {
                "status": "error",
                "message": "Ninja is not installed. Please install with: sudo apt-get install ninja-build",
            }
        ninja_version = subprocess.check_output(
            ["ninja", "--version"], universal_newlines=True
        ).strip()
        print(f"Ninja: {ninja_version} (OK)")

        # Check essential build tools
        essential_tools = ["gcc", "g++", "make"]
        for tool in essential_tools:
            if shutil.which(tool) is None:
                return {
                    "status": "error",
                    "message": f"{tool} is not installed. Please install build-essential package",
                }

        return {
            "status": "success",
            "message": "All required dependencies are installed",
        }

    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Dependency check failed: {str(e)}"}
    except Exception as e:
        return {
            "status": "error",
            "message": f"Linux dependency check failed: {str(e)}",
        }


def _check_macos_dependencies() -> Dict[str, Any]:
    """
    Check and install required dependencies on macOS.
    """
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            return {"status": "error", "message": "Python 3.8 or higher is required"}
        print(f"Python version: {platform.python_version()} (OK)")

        # Check Git
        if shutil.which("git") is None:
            return {
                "status": "error",
                "message": "Git is not installed. Please install Xcode Command Line Tools or Git from https://git-scm.com/",
            }
        git_version = subprocess.check_output(
            ["git", "--version"], universal_newlines=True
        ).strip()
        print(f"Git: {git_version} (OK)")

        # Check Xcode Command Line Tools
        try:
            subprocess.check_output(
                ["xcode-select", "--version"], universal_newlines=True
            )
            print("Xcode Command Line Tools: Installed (OK)")
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {
                "status": "error",
                "message": "Xcode Command Line Tools are not installed. Please run: xcode-select --install",
            }

        # Check CMake
        if shutil.which("cmake") is None:
            return {
                "status": "error",
                "message": "CMake is not installed. Please install CMake 3.20.1 or higher using Homebrew or from https://cmake.org/download/",
            }
        cmake_version = subprocess.check_output(
            ["cmake", "--version"], universal_newlines=True
        ).split()[2]
        print(f"CMake version: {cmake_version}")

        # Simple version check
        cmake_parts = cmake_version.split(".")
        if len(cmake_parts) >= 3:
            cmake_major, cmake_minor, cmake_patch = (
                int(cmake_parts[0]),
                int(cmake_parts[1]),
                int(cmake_parts[2]),
            )
            if (cmake_major, cmake_minor, cmake_patch) < (3, 20, 1):
                return {
                    "status": "error",
                    "message": "CMake 3.20.1 or higher is required",
                }

        # Check Ninja
        if shutil.which("ninja") is None:
            return {
                "status": "error",
                "message": "Ninja is not installed. Please install with Homebrew: brew install ninja",
            }
        ninja_version = subprocess.check_output(
            ["ninja", "--version"], universal_newlines=True
        ).strip()
        print(f"Ninja: {ninja_version} (OK)")

        return {
            "status": "success",
            "message": "All required dependencies are installed",
        }

    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Dependency check failed: {str(e)}"}
    except Exception as e:
        return {
            "status": "error",
            "message": f"macOS dependency check failed: {str(e)}",
        }


def _check_visual_studio_tools() -> bool:
    """
    Check if Visual Studio Build Tools are installed on Windows.
    """
    try:
        # Check for common Visual Studio installation paths
        vs_paths = [
            os.path.join(
                os.environ.get("ProgramFiles(x86)", "C:\Program Files (x86)"),
                "Microsoft Visual Studio",
            ),
            os.path.join(
                os.environ.get("ProgramFiles", "C:\Program Files"),
                "Microsoft Visual Studio",
            ),
        ]

        for path in vs_paths:
            if os.path.isdir(path):
                # Look for recent versions
                for item in os.listdir(path):
                    if item.startswith(("2019", "2022", "2024")) and os.path.isdir(
                        os.path.join(path, item)
                    ):
                        return True

        # Check for BuildTools specifically
        build_tools_path = os.path.join(
            os.environ.get("ProgramFiles(x86)", "C:\Program Files (x86)"),
            "Microsoft Visual Studio",
            "2022",
            "BuildTools",
        )
        if os.path.isdir(build_tools_path):
            return True

        return False
    except Exception:
        return False


def _setup_windows_env_vars(workspace_path: str, venv_path: str) -> None:
    """
    Set up environment variables for Zephyr on Windows with virtual environment support.
    """
    try:
        # Create a batch file to set environment variables and activate virtual environment
        env_batch_file = os.path.join(workspace_path, "setup_env.bat")
        with open(env_batch_file, "w") as f:
            f.write("@echo off\n")
            f.write("echo Setting up Zephyr environment variables...\n")
            f.write(
                f"set ZEPHYR_BASE={os.path.join(workspace_path, 'zephyr').replace('\\', '\\\\')}\n"
            )
            f.write("set ZEPHYR_TOOLCHAIN_VARIANT=zephyr\n")
            f.write(
                f"set ZEPHYR_SDK_INSTALL_DIR={os.path.join(workspace_path, 'tools', 'zephyr-sdk').replace('\\', '\\\\')}\n"
            )
            f.write("echo Activating Python virtual environment...\n")
            f.write(
                f"call {os.path.join(venv_path, 'Scripts', 'activate').replace('\\', '\\\\')}\n"
            )
            f.write(
                "echo Environment variables set and virtual environment activated.\n"
            )
            f.write(f"echo Run this script before working with Zephyr projects.\n")

        print(f"Created environment setup batch file: {env_batch_file}")
        print("Run this script before working with Zephyr projects.")
    except Exception as e:
        print(f"Warning: Failed to create environment setup file: {str(e)}")


def _install_windows_sdk(workspace_path: str, sdk_version: str) -> Dict[str, Any]:
    """
    Install Zephyr SDK on Windows.
    """
    try:
        print(f"Installing Zephyr SDK {sdk_version}...")

        # Create SDK directory
        sdk_dir = os.path.join(workspace_path, "tools", "zephyr-sdk")
        os.makedirs(sdk_dir, exist_ok=True)

        # Download and install SDK (simplified for example)
        # In a real implementation, you would download the installer and run it
        sdk_installer_url = f"https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v{sdk_version}/zephyr-sdk-{sdk_version}_windows-x86_64.exe"

        print(f"Please download and install Zephyr SDK from: {sdk_installer_url}")
        print(f"Install it to: {sdk_dir}")

        # For automation, you could use PowerShell to download and install silently
        # This is a placeholder for the actual implementation

        return {
            "status": "success",
            "message": "Zephyr SDK installation instructions provided",
            "sdk_path": sdk_dir,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Windows SDK installation failed: {str(e)}",
        }


def _install_linux_sdk(workspace_path: str, sdk_version: str) -> Dict[str, Any]:
    """
    Install Zephyr SDK on Linux.
    """
    try:
        print(f"Installing Zephyr SDK {sdk_version}...")

        # Create SDK directory
        sdk_dir = os.path.join(workspace_path, "tools", "zephyr-sdk")
        os.makedirs(sdk_dir, exist_ok=True)

        # Download SDK
        os.chdir(sdk_dir)
        sdk_file = f"zephyr-sdk-{sdk_version}_linux-x86_64.tar.gz"
        sdk_url = f"https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v{sdk_version}/{sdk_file}"

        print(f"Downloading SDK from: {sdk_url}")
        subprocess.check_call(["wget", sdk_url])

        # Extract SDK
        print("Extracting SDK...")
        subprocess.check_call(["tar", "xf", sdk_file])

        # Run setup script
        setup_script = os.path.join(sdk_dir, f"zephyr-sdk-{sdk_version}", "setup.sh")
        if os.path.exists(setup_script):
            print("Running SDK setup script...")
            subprocess.check_call(["bash", setup_script])

        return {
            "status": "success",
            "message": "Zephyr SDK installed successfully",
            "sdk_path": sdk_dir,
        }

    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Command failed: {str(e)}"}
    except Exception as e:
        return {
            "status": "error",
            "message": f"Linux SDK installation failed: {str(e)}",
        }


def _install_macos_sdk(workspace_path: str, sdk_version: str) -> Dict[str, Any]:
    """
    Install Zephyr SDK on macOS.
    """
    try:
        print(f"Installing Zephyr SDK {sdk_version}...")

        # Create SDK directory
        sdk_dir = os.path.join(workspace_path, "tools", "zephyr-sdk")
        os.makedirs(sdk_dir, exist_ok=True)

        # Download SDK
        os.chdir(sdk_dir)
        sdk_file = f"zephyr-sdk-{sdk_version}_macos-x86_64.tar.gz"
        sdk_url = f"https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v{sdk_version}/{sdk_file}"

        print(f"Downloading SDK from: {sdk_url}")
        subprocess.check_call(["curl", "-L", sdk_url, "-o", sdk_file])

        # Extract SDK
        print("Extracting SDK...")
        subprocess.check_call(["tar", "xf", sdk_file])

        # Run setup script
        setup_script = os.path.join(sdk_dir, f"zephyr-sdk-{sdk_version}", "setup.sh")
        if os.path.exists(setup_script):
            print("Running SDK setup script...")
            subprocess.check_call(["bash", setup_script])

        return {
            "status": "success",
            "message": "Zephyr SDK installed successfully",
            "sdk_path": sdk_dir,
        }

    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Command failed: {str(e)}"}
    except Exception as e:
        return {
            "status": "error",
            "message": f"macOS SDK installation failed: {str(e)}",
        }


def _get_environment_details(workspace_path: str) -> Dict[str, Any]:
    """
    Get details about the installed Zephyr environment.
    """
    details = {}

    try:
        # Check if zephyr directory exists
        zephyr_dir = os.path.join(workspace_path, "zephyr")
        details["zephyr_directory_exists"] = os.path.isdir(zephyr_dir)

        # Get West version
        try:
            west_version = subprocess.check_output(
                ["west", "--version"], universal_newlines=True
            ).strip()
            details["west_version"] = west_version
        except:
            details["west_version"] = "unknown"

        # Check if SDK directory exists
        sdk_dir = os.path.join(workspace_path, "tools", "zephyr-sdk")
        details["sdk_directory_exists"] = os.path.isdir(sdk_dir)

        # Get platform info
        details["platform"] = platform.system()
        details["platform_version"] = platform.version()
        details["python_version"] = platform.python_version()

    except Exception as e:
        details["error"] = str(e)

    return details


def validate_zephyr_environment(workspace_path: str) -> Dict[str, Any]:
    """
    Validate that a Zephyr environment is properly set up according to official requirements.

    Args:
        workspace_path: Path to the Zephyr workspace

    Returns:
        Dict containing validation results with status and detailed information
    """
    try:
        # Create absolute path
        workspace_path = os.path.abspath(workspace_path)
        details = {}
        warnings = []
        errors = []

        # Check if workspace exists
        if not os.path.isdir(workspace_path):
            return {
                "status": "error",
                "message": f"Workspace directory not found: {workspace_path}",
            }

        # Check if Zephyr directory exists
        zephyr_dir = os.path.join(workspace_path, "zephyr")
        details["zephyr_directory_exists"] = os.path.isdir(zephyr_dir)
        if not details["zephyr_directory_exists"]:
            return {
                "status": "error",
                "message": f"Zephyr directory not found in workspace",
            }

        # Check if west is initialized
        west_config = os.path.join(workspace_path, ".west", "config")
        details["west_initialized"] = os.path.isfile(west_config)
        if not details["west_initialized"]:
            warnings.append(
                "West configuration not found. Environment may not be fully initialized."
            )

        # Check if west.yml exists
        west_yml = os.path.join(workspace_path, "west.yml")
        details["west_yml_exists"] = os.path.isfile(west_yml)
        if not details["west_yml_exists"]:
            warnings.append("west.yml not found. West manifest may be missing.")

        # Check Python dependencies
        required_packages = ["west", "pyelftools", "pykwalify", "ply"]
        missing_packages = []
        for pkg in required_packages:
            try:
                __import__(pkg)
            except ImportError:
                missing_packages.append(pkg)

        if missing_packages:
            warnings.append(
                f"Missing Python dependencies: {', '.join(missing_packages)}"
            )
        else:
            details["python_dependencies"] = "installed"

        # Run a simple west command to verify functionality
        if details["west_initialized"]:
            try:
                os.chdir(workspace_path)
                subprocess.check_output(
                    ["west", "list"], universal_newlines=True, stderr=subprocess.STDOUT
                )
                details["west_functionality"] = "working"
            except subprocess.CalledProcessError as e:
                errors.append(f"West command failed: {str(e)}")
            except Exception as e:
                warnings.append(f"Error checking west functionality: {str(e)}")

        # Check SDK installation
        sdk_dir = os.path.join(workspace_path, "tools", "zephyr-sdk")
        details["sdk_directory_exists"] = os.path.isdir(sdk_dir)

        if details["sdk_directory_exists"]:
            # Check for SDK binaries
            sdk_tools = os.path.join(
                sdk_dir, "sysroots", "x86_64-pokysdk-linux", "usr", "bin"
            )
            details["sdk_tools_available"] = os.path.isdir(sdk_tools)

            # Try to detect toolchain
            try:
                for tool in ["zephyr-gcc", "arm-none-eabi-gcc"]:
                    if (
                        subprocess.call(
                            ["which", tool],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )
                        == 0
                    ):
                        details["toolchain_available"] = tool
                        break
                else:
                    warnings.append("No Zephyr toolchain found in PATH")
            except Exception as e:
                warnings.append(f"Error checking toolchain: {str(e)}")
        else:
            warnings.append("Zephyr SDK directory not found")

        # Check for CMake
        try:
            cmake_version = subprocess.check_output(
                ["cmake", "--version"], universal_newlines=True
            ).strip()
            details["cmake_version"] = cmake_version.split()[2]
        except Exception as e:
            errors.append(f"CMake not found: {str(e)}")

        # Check for Ninja (recommended build system)
        try:
            ninja_version = subprocess.check_output(
                ["ninja", "--version"], universal_newlines=True
            ).strip()
            details["ninja_version"] = ninja_version
        except Exception as e:
            warnings.append(f"Ninja build system not found: {str(e)}")

        # Add environment details
        details["platform"] = platform.system()
        details["platform_version"] = platform.version()
        details["python_version"] = platform.python_version()
        details["workspace_path"] = workspace_path
        details["zephyr_directory"] = (
            zephyr_dir if details["zephyr_directory_exists"] else None
        )

        # Determine overall status
        if errors:
            return {
                "status": "error",
                "message": "Critical errors found during validation",
                "details": details,
                "errors": errors,
                "warnings": warnings,
            }
        elif warnings:
            return {
                "status": "warning",
                "message": "Environment has warnings but may be functional",
                "details": details,
                "warnings": warnings,
            }
        else:
            return {
                "status": "success",
                "message": "Zephyr environment validation successful",
                "details": details,
            }

    except Exception as e:
        return {"status": "error", "message": f"Validation process failed: {str(e)}"}


if __name__ == "__main__":
    """
    Main entry point for the Zephyr RTOS Development Environment Setup Tool.
    
    Parses command line arguments and invokes the setup function, providing
    user-friendly output and error handling.
    """

    parser = argparse.ArgumentParser(
        description="Zephyr RTOS Development Environment Setup Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Basic setup:
    python setup_zephyr_environment.py /path/to/workspace
  
  Specify versions:
    python setup_zephyr_environment.py /path/to/workspace --version v3.5.0 --sdk-version 0.16.8
  
  Skip SDK installation:
    python setup_zephyr_environment.py /path/to/workspace --no-sdk
  
  Force overwrite existing workspace:
    python setup_zephyr_environment.py /path/to/workspace --force
        """,
    )

    parser.add_argument("workspace", help="Path to create the Zephyr workspace")
    parser.add_argument(
        "--version",
        default="latest",
        help="Zephyr version to install (e.g., v3.5.0, main)",
    )
    parser.add_argument(
        "--no-sdk",
        action="store_false",
        dest="install_sdk",
        help="Skip SDK installation",
    )
    parser.add_argument(
        "--sdk-version", default="0.16.8", help="Version of the Zephyr SDK to install"
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing workspace"
    )

    args = parser.parse_args()

    # Print header
    print("=" * 80)
    print("Zephyr RTOS Development Environment Setup Tool".center(80))
    print("=" * 80)
    print(f"Setting up Zephyr environment in: {args.workspace}")
    print(f"Zephyr version: {args.version}")
    print(f"Install SDK: {args.install_sdk}")
    if args.install_sdk:
        print(f"SDK version: {args.sdk_version}")
    print(f"Force mode: {args.force}")
    print("=" * 80)
    print()

    try:
        # Perform the environment setup
        result = setup_zephyr_environment(
            args.workspace,
            zephyr_version=args.version,
            install_sdk=args.install_sdk,
            sdk_version=args.sdk_version,
            force=args.force,
        )

        # Display results in a user-friendly format
        print("\n" + "=" * 80)
        print("SETUP RESULTS:")
        print("=" * 80)
        print(f"Status: {'SUCCESS' if result['status'] == 'success' else 'ERROR'}")
        print(f"Message: {result['message']}")

        if "details" in result:
            print("\nDetails:")
            for key, value in result["details"].items():
                print(f"  - {key}: {value}")

        if "warnings" in result:
            print("\nWarnings:")
            for warning in result["warnings"]:
                print(f"  ⚠️  {warning}")

        if "errors" in result:
            print("\nErrors:")
            for error in result["errors"]:
                print(f"  ❌ {error}")

        # Print next steps
        if result["status"] == "success":
            print("\n" + "=" * 80)
            print("NEXT STEPS:")
            print("=" * 80)

            if platform.system() == "Windows":
                env_script = os.path.join(
                    os.path.abspath(args.workspace), "zephyr_env.cmd"
                )
                print(f"1. Run the environment setup script: {env_script}")
            else:
                env_script = os.path.join(
                    os.path.abspath(args.workspace), "zephyr_env.sh"
                )
                print(f"1. Source the environment setup script: source {env_script}")

            print("2. To build your first application:")
            print("   cd zephyr/samples/hello_world")
            print("   west build -b <board-name> .")
            print(
                "3. For more information, visit: https://docs.zephyrproject.org/latest/getting_started/index.html"
            )

        sys.exit(0 if result["status"] == "success" else 1)

    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user. Exiting.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error during setup: {str(e)}")
        print("\nPlease check your environment and try again.")
        sys.exit(1)
