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

import io
import os
import sys
import platform
import subprocess
import shutil
import argparse
from typing import Dict, Any, List, Optional

from src.utils.logging_utils import get_logger
from src.utils.common_tools import run_command

logger = get_logger(__name__)


DEFAULT_ZEPHYR_REPO_URL = "https://github.com/zephyrproject-rtos/zephyr"


def _get_zephyr_repo_url() -> str:
    # Allow users to route around GitHub connectivity issues using a mirror.
    # Example (PowerShell):
    #   $env:ZEPHYR_REPO_URL = 'https://<your-mirror>/zephyr'
    return (
        os.environ.get("ZEPHYR_WEST_ZEPHYR_URL")
        or os.environ.get("ZEPHYR_REPO_URL")
        or DEFAULT_ZEPHYR_REPO_URL
    )


def _run_or_raise(
    cmd: List[str],
    *,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    retries: int = 3,
    retry_backoff_seconds: float = 1.0,
) -> None:
    cmd_result = run_command(
        cmd,
        cwd=cwd,
        env=env,
        timeout=timeout,
        retries=retries,
        retry_backoff_seconds=retry_backoff_seconds,
    )
    if cmd_result.get("status") != "success":
        logger.error(
            "Command failed (attempts=%s): %s\nstdout: %s\nstderr: %s",
            cmd_result.get("attempts"),
            " ".join(cmd),
            (cmd_result.get("stdout") or "").strip(),
            (cmd_result.get("stderr") or "").strip(),
        )
        raise subprocess.CalledProcessError(
            cmd_result.get("returncode", 1),
            cmd,
            output=cmd_result.get("stdout"),
            stderr=cmd_result.get("stderr"),
        )


def setup_zephyr_environment(
    workspace_path: str,
    zephyr_version: str = "latest",
    install_sdk: bool = True,
    sdk_version: str = "0.17.1",
    platforms: Optional[List[str]] = None,
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
        ...     logger.info(f"Zephyr environment set up at: {result['details']['workspace_path']}")
    """

    try:
        # Validate parameters
        if not workspace_path:
            return {"status": "error", "message": "Workspace path is required"}

        # Create absolute path
        workspace_path = os.path.abspath(workspace_path)

        # Check if workspace already exists
        if os.path.exists(workspace_path):
            if not force:
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
    platforms: Optional[List[str]],
) -> Dict[str, Any]:
    """
    Set up Zephyr environment on Windows according to official guidelines.
    """
    try:
        zephyr_repo_url = _get_zephyr_repo_url()

        # Ensure PowerShell can execute locally generated scripts (CurrentUser scope)
        _ensure_windows_powershell_execution_policy()

        # Check and install dependencies
        check_result = _check_windows_dependencies()
        if check_result["status"] != "success":
            return check_result

        # Create workspace directory
        os.makedirs(workspace_path, exist_ok=True)
        logger.info("Created workspace directory: %s", workspace_path)

        # Create and activate Python virtual environment
        venv_path = os.path.join(workspace_path, ".venv")
        logger.info("Creating Python virtual environment in %s...", venv_path)
        subprocess.check_call([sys.executable, "-m", "venv", venv_path])

        # Get path to pip in virtual environment
        venv_pip = os.path.join(venv_path, "Scripts", "pip.exe")

        # Check for Visual Studio Build Tools
        vs_tools_installed = _check_visual_studio_tools()
        if not vs_tools_installed:
            logger.warning("Visual Studio Build Tools not found.")
            logger.warning(
                "It's recommended to install Visual Studio Build Tools for C++ development."
            )
            logger.warning(
                "Download: https://visualstudio.microsoft.com/downloads/"
            )

        # Install West with specific version requirements in virtual environment
        logger.info(
            "Installing West tool with required dependencies in virtual environment..."
        )
        _run_or_raise([venv_pip, "install", "west", "pyelftools"], cwd=workspace_path)

        # Initialize Zephyr workspace
        logger.info("Initializing Zephyr workspace in %s...", workspace_path)
        os.chdir(workspace_path)

        # Get path to west in virtual environment
        venv_west = os.path.join(venv_path, "Scripts", "west.exe")

        try:
            if zephyr_version == "latest":
                _run_or_raise(
                    [venv_west, "init", "-m", zephyr_repo_url, "."],
                    cwd=workspace_path,
                    retries=3,
                    retry_backoff_seconds=1.5,
                )
            else:
                _run_or_raise(
                    [venv_west, "init", "-m", zephyr_repo_url, "--mr", zephyr_version, "."],
                    cwd=workspace_path,
                    retries=3,
                    retry_backoff_seconds=1.5,
                )
        except subprocess.CalledProcessError:
            # Try with proxy settings if available
            env = os.environ.copy()
            if "http_proxy" in env or "https_proxy" in env:
                logger.info("Retry with proxy settings...")
                if zephyr_version == "latest":
                    _run_or_raise(
                        [venv_west, "init", "-m", zephyr_repo_url, "."],
                        cwd=workspace_path,
                        env=env,
                        retries=3,
                        retry_backoff_seconds=2.0,
                    )
                else:
                    _run_or_raise(
                        [venv_west, "init", "-m", zephyr_repo_url, "--mr", zephyr_version, "."],
                        cwd=workspace_path,
                        env=env,
                        retries=3,
                        retry_backoff_seconds=2.0,
                    )
            else:
                raise

        # Update West with progress indicator
        logger.info("Updating West dependencies (this may take several minutes)...")
        _run_or_raise(
            [venv_west, "update"],
            cwd=workspace_path,
            retries=3,
            retry_backoff_seconds=2.0,
        )

        # Install Zephyr Python dependencies in virtual environment
        logger.info("Installing Zephyr Python dependencies in virtual environment...")
        requirements_file = os.path.join(
            workspace_path, "zephyr", "scripts", "requirements.txt"
        )
        if os.path.exists(requirements_file):
            _run_or_raise(
                [venv_pip, "install", "-r", requirements_file],
                cwd=workspace_path,
                retries=3,
                retry_backoff_seconds=2.0,
            )
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


def _ensure_windows_powershell_execution_policy() -> None:
    """Best-effort: set PowerShell execution policy for CurrentUser to RemoteSigned.

    Command requested:
      Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

    This function is non-fatal: it logs warnings if it cannot apply the setting.
    """

    if platform.system().lower() != "windows":
        return

    ps_exe = shutil.which("powershell") or shutil.which("pwsh")
    if not ps_exe:
        logger.warning("PowerShell not found; cannot set execution policy.")
        logger.warning(
            "Run manually: Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned"
        )
        return

    try:
        current = (
            subprocess.check_output(
                [
                    ps_exe,
                    "-NoProfile",
                    "-Command",
                    "Get-ExecutionPolicy -Scope CurrentUser",
                ],
                text=True,
                stderr=subprocess.STDOUT,
            )
            .strip()
            .lower()
        )
    except (subprocess.CalledProcessError, OSError) as e:
        logger.warning("Could not read PowerShell execution policy: %s", e)
        current = ""

    # RemoteSigned is requested; treat more permissive settings as OK.
    if current in {"remotesigned", "unrestricted", "bypass"}:
        return

    try:
        subprocess.check_call(
            [
                ps_exe,
                "-NoProfile",
                "-Command",
                "Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force",
            ]
        )
        logger.info("PowerShell execution policy set to RemoteSigned (CurrentUser).")
    except (subprocess.CalledProcessError, OSError) as e:
        logger.warning("Failed to set PowerShell execution policy: %s", e)
        logger.warning(
            "Run manually: Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned"
        )


def _setup_linux_environment(
    workspace_path: str,
    zephyr_version: str,
    install_sdk: bool,
    sdk_version: str,
    platforms: Optional[List[str]],
) -> Dict[str, Any]:
    """
    Set up Zephyr environment on Linux according to official guidelines.
    """
    try:
        zephyr_repo_url = _get_zephyr_repo_url()

        # Check and install dependencies
        check_result = _check_linux_dependencies()
        if check_result["status"] != "success":
            return check_result

        # Create workspace directory with proper permissions
        os.makedirs(workspace_path, exist_ok=True)
        os.chmod(workspace_path, 0o755)  # Ensure proper permissions
        logger.info("Created workspace directory: %s", workspace_path)

        # Check if running as root (not recommended)
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            logger.warning(
                "Running as root is not recommended for Zephyr development"
            )
            logger.warning("Consider using a regular user account for development.")

        # Create and activate Python virtual environment
        venv_path = os.path.join(workspace_path, ".venv")
        logger.info("Creating Python virtual environment in %s...", venv_path)
        subprocess.check_call([sys.executable, "-m", "venv", venv_path])

        # Get path to pip in virtual environment
        venv_pip = os.path.join(venv_path, "bin", "pip")

        # Install West with specific version requirements in virtual environment
        logger.info(
            "Installing West tool with required dependencies in virtual environment..."
        )
        _run_or_raise([venv_pip, "install", "west", "pyelftools"], cwd=workspace_path)

        # Initialize Zephyr workspace
        logger.info("Initializing Zephyr workspace in %s...", workspace_path)
        os.chdir(workspace_path)

        # Get path to west in virtual environment
        venv_west = os.path.join(venv_path, "bin", "west")

        try:
            if zephyr_version == "latest":
                _run_or_raise(
                    [venv_west, "init", "-m", zephyr_repo_url, "."],
                    cwd=workspace_path,
                    retries=3,
                    retry_backoff_seconds=1.5,
                )
            else:
                _run_or_raise(
                    [venv_west, "init", "-m", zephyr_repo_url, "--mr", zephyr_version, "."],
                    cwd=workspace_path,
                    retries=3,
                    retry_backoff_seconds=1.5,
                )
        except subprocess.CalledProcessError:
            # Try with proxy settings if available
            env = os.environ.copy()
            if "http_proxy" in env or "https_proxy" in env:
                logger.info("Retry with proxy settings...")
                if zephyr_version == "latest":
                    _run_or_raise(
                        [venv_west, "init", "-m", zephyr_repo_url, "."],
                        cwd=workspace_path,
                        env=env,
                        retries=3,
                        retry_backoff_seconds=2.0,
                    )
                else:
                    _run_or_raise(
                        [venv_west, "init", "-m", zephyr_repo_url, "--mr", zephyr_version, "."],
                        cwd=workspace_path,
                        env=env,
                        retries=3,
                        retry_backoff_seconds=2.0,
                    )
            else:
                raise

        # Update West with progress indicator
        logger.info("Updating West dependencies (this may take several minutes)...")
        _run_or_raise(
            [venv_west, "update"],
            cwd=workspace_path,
            retries=3,
            retry_backoff_seconds=2.0,
        )

        # Install Zephyr Python dependencies in virtual environment
        logger.info("Installing Zephyr Python dependencies in virtual environment...")
        requirements_file = os.path.join(
            workspace_path, "zephyr", "scripts", "requirements.txt"
        )
        if os.path.exists(requirements_file):
            _run_or_raise(
                [venv_pip, "install", "-r", requirements_file],
                cwd=workspace_path,
                retries=3,
                retry_backoff_seconds=2.0,
            )
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

    with open(env_script_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    # Make the script executable
    os.chmod(env_script_path, 0o755)
    logger.info("Created environment setup script: %s", env_script_path)
    logger.info(
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

    with open(env_script_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    # Make the script executable
    os.chmod(env_script_path, 0o755)
    logger.info("Created environment setup script: %s", env_script_path)
    logger.info(
        "To activate the Zephyr environment in future sessions, run: source zephyr_env.sh"
    )


def _setup_macos_environment(
    workspace_path: str,
    zephyr_version: str,
    install_sdk: bool,
    sdk_version: str,
    platforms: Optional[List[str]],
) -> Dict[str, Any]:
    """
    Set up Zephyr environment on macOS according to official guidelines.
    """
    try:
        zephyr_repo_url = _get_zephyr_repo_url()

        # Check and install dependencies
        check_result = _check_macos_dependencies()
        if check_result["status"] != "success":
            return check_result

        # Create workspace directory with proper permissions
        os.makedirs(workspace_path, exist_ok=True)
        os.chmod(workspace_path, 0o755)  # Ensure proper permissions
        logger.info("Created workspace directory: %s", workspace_path)

        # Create and activate Python virtual environment
        venv_path = os.path.join(workspace_path, ".venv")
        logger.info("Creating Python virtual environment in %s...", venv_path)
        subprocess.check_call([sys.executable, "-m", "venv", venv_path])

        # Get path to pip in virtual environment
        venv_pip = os.path.join(venv_path, "bin", "pip")

        # Install West with specific version requirements in virtual environment
        logger.info(
            "Installing West tool with required dependencies in virtual environment..."
        )
        _run_or_raise([venv_pip, "install", "west", "pyelftools"], cwd=workspace_path)

        # Initialize Zephyr workspace
        logger.info("Initializing Zephyr workspace in %s...", workspace_path)
        os.chdir(workspace_path)

        # Get path to west in virtual environment
        venv_west = os.path.join(venv_path, "bin", "west")

        try:
            if zephyr_version == "latest":
                _run_or_raise(
                    [venv_west, "init", "-m", zephyr_repo_url, "."],
                    cwd=workspace_path,
                    retries=3,
                    retry_backoff_seconds=1.5,
                )
            else:
                _run_or_raise(
                    [venv_west, "init", "-m", zephyr_repo_url, "--mr", zephyr_version, "."],
                    cwd=workspace_path,
                    retries=3,
                    retry_backoff_seconds=1.5,
                )
        except subprocess.CalledProcessError:
            # Try with proxy settings if available
            env = os.environ.copy()
            if "http_proxy" in env or "https_proxy" in env:
                logger.info("Retry with proxy settings...")
                if zephyr_version == "latest":
                    _run_or_raise(
                        [venv_west, "init", "-m", zephyr_repo_url, "."],
                        cwd=workspace_path,
                        env=env,
                        retries=3,
                        retry_backoff_seconds=2.0,
                    )
                else:
                    _run_or_raise(
                        [venv_west, "init", "-m", zephyr_repo_url, "--mr", zephyr_version, "."],
                        cwd=workspace_path,
                        env=env,
                        retries=3,
                        retry_backoff_seconds=2.0,
                    )
            else:
                raise

        # Update West with progress indicator
        logger.info("Updating West dependencies (this may take several minutes)...")
        _run_or_raise(
            [venv_west, "update"],
            cwd=workspace_path,
            retries=3,
            retry_backoff_seconds=2.0,
        )

        # Install Zephyr Python dependencies in virtual environment
        logger.info("Installing Zephyr Python dependencies in virtual environment...")
        requirements_file = os.path.join(
            workspace_path, "zephyr", "scripts", "requirements.txt"
        )
        if os.path.exists(requirements_file):
            _run_or_raise(
                [venv_pip, "install", "-r", requirements_file],
                cwd=workspace_path,
                retries=3,
                retry_backoff_seconds=2.0,
            )
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
    if sys.platform == "win32":
        # Best-effort: ensure UTF-8 output on Windows.
        # In hosted/tooling environments, stdout/stderr may be proxies where
        # reconfiguration/re-wrapping is not permitted.
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            elif hasattr(sys.stdout, "buffer"):
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer, encoding="utf-8", errors="replace"
                )
        except Exception as e:
            logger.debug("Could not reconfigure stdout to UTF-8: %s", e)

        try:
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
            elif hasattr(sys.stderr, "buffer"):
                sys.stderr = io.TextIOWrapper(
                    sys.stderr.buffer, encoding="utf-8", errors="replace"
                )
        except Exception as e:
            logger.debug("Could not reconfigure stderr to UTF-8: %s", e)

        # Install dependencies using winget
        install_cmd = (
            "winget install Kitware.CMake Ninja-build.Ninja oss-winget.gperf "
            "Python.Python.3.12 Git.Git oss-winget.dtc wget 7zip.7zip -e --accept-package-agreements --accept-source-agreements"
        )
        try:
            logger.info("Installing dependencies with winget...")
            subprocess.run(install_cmd, shell=True, check=True)
            logger.info("Dependencies installed successfully.")
        except Exception as e:
            logger.warning("Dependency installation failed: %s", e)

    try:
        # Check Python version
        if sys.version_info < (3, 8):
            return {"status": "error", "message": "Python 3.8 or higher is required"}
        logger.info("Python version: %s (OK)", platform.python_version())

        # Check Git
        if shutil.which("git") is None:
            return {
                "status": "error",
                "message": "Git is not installed. Please install Git from https://git-scm.com/download/win",
            }
        git_version = subprocess.check_output(
            ["git", "--version"], universal_newlines=True
        ).strip()
        logger.info("Git: %s (OK)", git_version)

        # Check CMake
        if shutil.which("cmake") is None:
            return {
                "status": "error",
                "message": "CMake is not installed. Please install CMake 3.20.1 or higher from https://cmake.org/download/",
            }
        cmake_version = subprocess.check_output(
            ["cmake", "--version"], universal_newlines=True
        ).split()[2]
        logger.info("CMake version: %s", cmake_version)

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
            logger.info("Ninja: %s (OK)", ninja_version)
        else:
            logger.warning(
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
        logger.info("Python version: %s (OK)", platform.python_version())

        # Check if running as root (not recommended)
        if hasattr(os, "geteuid"):
            if os.geteuid() == 0:
                logger.warning("Running as root is not recommended")

        # Check Git
        if shutil.which("git") is None:
            return {
                "status": "error",
                "message": "Git is not installed. Please install with: sudo apt-get install git",
            }
        git_version = subprocess.check_output(
            ["git", "--version"], universal_newlines=True
        ).strip()
        logger.info("Git: %s (OK)", git_version)

        # Check CMake
        if shutil.which("cmake") is None:
            return {
                "status": "error",
                "message": "CMake is not installed. Please install CMake 3.20.1 or higher",
            }
        cmake_version = subprocess.check_output(
            ["cmake", "--version"], universal_newlines=True
        ).split()[2]
        logger.info("CMake version: %s", cmake_version)

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
        logger.info("Ninja: %s (OK)", ninja_version)

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
        logger.info("Python version: %s (OK)", platform.python_version())

        # Check Git
        if shutil.which("git") is None:
            return {
                "status": "error",
                "message": "Git is not installed. Please install Xcode Command Line Tools or Git from https://git-scm.com/",
            }
        git_version = subprocess.check_output(
            ["git", "--version"], universal_newlines=True
        ).strip()
        logger.info("Git: %s (OK)", git_version)

        # Check Xcode Command Line Tools
        try:
            subprocess.check_output(
                ["xcode-select", "--version"], universal_newlines=True
            )
            logger.info("Xcode Command Line Tools: Installed (OK)")
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
        logger.info("CMake version: %s", cmake_version)

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
        logger.info("Ninja: %s (OK)", ninja_version)

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
                os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                "Microsoft Visual Studio",
            ),
            os.path.join(
                os.environ.get("ProgramFiles", r"C:\Program Files"),
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
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
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
        with open(env_batch_file, "w", encoding="utf-8") as f:
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
            f.write("echo Run this script before working with Zephyr projects.\n")

        logger.info("Created environment setup batch file: %s", env_batch_file)
        logger.info("Run this script before working with Zephyr projects.")
    except Exception as e:
        logger.warning("Failed to create environment setup file: %s", e)


def _install_windows_sdk(workspace_path: str, sdk_version: str) -> Dict[str, Any]:
    """
    Install Zephyr SDK on Windows.
    """
    try:
        logger.info("Installing Zephyr SDK %s...", sdk_version)

        # Create SDK directory
        sdk_dir = os.path.join(workspace_path, "tools", "zephyr-sdk")
        os.makedirs(sdk_dir, exist_ok=True)

        # Download and install SDK (simplified for example)
        # In a real implementation, you would download the installer and run it
        sdk_installer_url = f"https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v{sdk_version}/zephyr-sdk-{sdk_version}_windows-x86_64.exe"

        # For automation, use PowerShell to download and silently install the SDK.
        ps_exe = shutil.which("powershell") or shutil.which("pwsh")
        if not ps_exe:
            message = "PowerShell not found; cannot automate Zephyr SDK install on Windows."
            logger.error(message)
            return {
                "status": "error",
                "message": message,
                "details": {
                    "sdk_installer_url": sdk_installer_url,
                    "suggested_install_dir": sdk_dir,
                },
                "suggestions": [
                    "Install Windows PowerShell (powershell) or PowerShell 7 (pwsh) and retry",
                    "Or download the SDK installer from the provided URL and install it manually",
                ],
            }

        sdk_installer_path = os.path.join(
            sdk_dir, f"zephyr-sdk-{sdk_version}_windows-x86_64.exe"
        )

        download_cmd = [
            ps_exe,
            "-NoProfile",
            "-Command",
            f"Invoke-WebRequest -Uri '{sdk_installer_url}' -OutFile '{sdk_installer_path}'",
        ]
        logger.info("Downloading Zephyr SDK installer to: %s", sdk_installer_path)
        _run_or_raise(download_cmd, cwd=workspace_path, retries=3, retry_backoff_seconds=2.0)

        # Silent install: the Zephyr SDK Windows installer is typically NSIS.
        # NSIS supports /S (silent) and /D=<dir> (must be last).
        install_cmd = [
            ps_exe,
            "-NoProfile",
            "-Command",
            f"Start-Process -FilePath '{sdk_installer_path}' -ArgumentList '/S','/D={sdk_dir}' -Wait -PassThru | Out-Null",
        ]
        logger.info("Running Zephyr SDK installer silently...")
        _run_or_raise(install_cmd, cwd=workspace_path, retries=1)
        logger.info("Zephyr SDK installed successfully at: %s", sdk_dir)

        return {
            "status": "success",
            "message": "Zephyr SDK installed successfully",
            "sdk_path": sdk_dir,
            "installer_path": sdk_installer_path,
        }

    except subprocess.CalledProcessError as e:
        logger.exception("Windows SDK installation failed")
        return {
            "status": "error",
            "message": "Windows SDK installation failed",
            "details": {
                "sdk_version": sdk_version,
                "returncode": getattr(e, "returncode", None),
                "cmd": getattr(e, "cmd", None),
                "stdout": getattr(e, "output", None),
                "stderr": getattr(e, "stderr", None),
            },
            "suggestions": [
                "Verify internet connectivity and GitHub access",
                "Try running again (transient download failures are common)",
                "If silent install fails, run the downloaded installer manually",
            ],
        }
    except OSError as e:
        logger.exception("Windows SDK installation failed (OS error)")
        return {
            "status": "error",
            "message": f"Windows SDK installation failed: {e}",
            "suggestions": [
                "Check file permissions for the workspace/tools directory",
                "Ensure antivirus or endpoint protection is not blocking downloads/executables",
            ],
        }


def _install_linux_sdk(workspace_path: str, sdk_version: str) -> Dict[str, Any]:
    """
    Install Zephyr SDK on Linux.
    """
    try:
        logger.info("Installing Zephyr SDK %s...", sdk_version)

        # Create SDK directory
        sdk_dir = os.path.join(workspace_path, "tools", "zephyr-sdk")
        os.makedirs(sdk_dir, exist_ok=True)

        # Download SDK
        os.chdir(sdk_dir)
        sdk_file = f"zephyr-sdk-{sdk_version}_linux-x86_64.tar.gz"
        sdk_url = f"https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v{sdk_version}/{sdk_file}"

        logger.info("Downloading SDK from: %s", sdk_url)
        _run_or_raise(
            ["wget", sdk_url],
            cwd=sdk_dir,
            retries=3,
            retry_backoff_seconds=2.0,
        )

        # Extract SDK
        logger.info("Extracting SDK...")
        _run_or_raise(["tar", "xf", sdk_file], cwd=sdk_dir)

        # Run setup script
        setup_script = os.path.join(sdk_dir, f"zephyr-sdk-{sdk_version}", "setup.sh")
        if os.path.exists(setup_script):
            logger.info("Running SDK setup script...")
            _run_or_raise(["bash", setup_script], cwd=sdk_dir)

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
        logger.info("Installing Zephyr SDK %s...", sdk_version)

        # Create SDK directory
        sdk_dir = os.path.join(workspace_path, "tools", "zephyr-sdk")
        os.makedirs(sdk_dir, exist_ok=True)

        # Download SDK
        os.chdir(sdk_dir)
        sdk_file = f"zephyr-sdk-{sdk_version}_macos-x86_64.tar.gz"
        sdk_url = f"https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v{sdk_version}/{sdk_file}"

        logger.info("Downloading SDK from: %s", sdk_url)
        _run_or_raise(
            ["curl", "-L", sdk_url, "-o", sdk_file],
            cwd=sdk_dir,
            retries=3,
            retry_backoff_seconds=2.0,
        )

        # Extract SDK
        logger.info("Extracting SDK...")
        _run_or_raise(["tar", "xf", sdk_file], cwd=sdk_dir)

        # Run setup script
        setup_script = os.path.join(sdk_dir, f"zephyr-sdk-{sdk_version}", "setup.sh")
        if os.path.exists(setup_script):
            logger.info("Running SDK setup script...")
            _run_or_raise(["bash", setup_script], cwd=sdk_dir)

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

    # Log header
    logger.info("%s", "=" * 80)
    logger.info("%s", "Zephyr RTOS Development Environment Setup Tool".center(80))
    logger.info("%s", "=" * 80)
    logger.info("Setting up Zephyr environment in: %s", args.workspace)
    logger.info("Zephyr version: %s", args.version)
    logger.info("Install SDK: %s", args.install_sdk)
    if args.install_sdk:
        logger.info("SDK version: %s", args.sdk_version)
    logger.info("Force mode: %s", args.force)
    logger.info("%s", "=" * 80)

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
        logger.info("%s", "=" * 80)
        logger.info("SETUP RESULTS:")
        logger.info("%s", "=" * 80)
        logger.info(
            "Status: %s",
            "SUCCESS" if result["status"] == "success" else "ERROR",
        )
        logger.info("Message: %s", result["message"])

        if "details" in result:
            logger.info("Details:")
            for key, value in result["details"].items():
                logger.info("- %s: %s", key, value)

        if "warnings" in result:
            logger.warning("Warnings:")
            for warning in result["warnings"]:
                logger.warning("%s", warning)

        if "errors" in result:
            logger.error("Errors:")
            for error in result["errors"]:
                logger.error("%s", error)

        # Print next steps
        if result["status"] == "success":
            logger.info("%s", "=" * 80)
            logger.info("NEXT STEPS:")
            logger.info("%s", "=" * 80)

            if platform.system() == "Windows":
                env_script = os.path.join(
                    os.path.abspath(args.workspace), "zephyr_env.cmd"
                )
                logger.info("1. Run the environment setup script: %s", env_script)
            else:
                env_script = os.path.join(
                    os.path.abspath(args.workspace), "zephyr_env.sh"
                )
                logger.info("1. Source the environment setup script: source %s", env_script)

            logger.info("2. To build your first application:")
            logger.info("   cd zephyr/samples/hello_world")
            logger.info("   west build -b <board-name> .")
            logger.info(
                "3. For more information, visit: https://docs.zephyrproject.org/latest/getting_started/index.html"
            )

        sys.exit(0 if result["status"] == "success" else 1)

    except KeyboardInterrupt:
        logger.warning("Setup interrupted by user. Exiting.")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during setup: %s", e)
        logger.error("Please check your environment and try again.")
        sys.exit(1)
