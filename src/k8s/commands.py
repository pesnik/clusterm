"""
Command execution for kubectl and helm
"""

import subprocess
import os
from pathlib import Path
from typing import List, Tuple, Optional
from ..core.exceptions import K8sError
from ..core.logger import Logger
from ..core.events import EventBus, EventType


class CommandExecutor:
    """Execute kubectl and helm commands"""
    
    def __init__(self, base_path: Path, event_bus: EventBus, logger: Logger):
        self.base_path = base_path
        self.event_bus = event_bus
        self.logger = logger
        self.kubectl_path = base_path / "tools" / "kubectl"
        self.helm_paths = [
            base_path / "tools" / "linux-amd64" / "helm",
            base_path / "tools" / "helm"
        ]
        self.current_kubeconfig: Optional[Path] = None
        
        # Try to find tools in system PATH if not in local tools directory
        self.kubectl_binary = self._find_kubectl_binary()
        self.helm_binary = self._find_helm_binary()
    
    def set_kubeconfig(self, kubeconfig_path: Optional[Path]):
        """Set the kubeconfig path for commands"""
        self.current_kubeconfig = kubeconfig_path
    
    def _find_kubectl_binary(self) -> str:
        """Find kubectl binary in local tools or system PATH"""
        # Check local tools directory first
        if self.kubectl_path.exists():
            return str(self.kubectl_path)
        
        # Fall back to system PATH
        try:
            result = subprocess.run(['which', 'kubectl'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        return None
    
    def _find_helm_binary(self) -> str:
        """Find helm binary in local tools or system PATH"""
        # Check local tools directory first
        for path in self.helm_paths:
            if path.exists():
                return str(path)
        
        # Fall back to system PATH
        try:
            result = subprocess.run(['which', 'helm'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        return None

    def execute_kubectl(self, args: List[str], timeout: int = 30) -> Tuple[bool, str]:
        """Execute a kubectl command"""
        if not self.kubectl_binary:
            error_msg = f"kubectl not found in {self.kubectl_path} or system PATH"
            self.logger.error(error_msg)
            return False, error_msg
        
        if not self.current_kubeconfig:
            error_msg = "No kubeconfig set"
            self.logger.error(error_msg)
            return False, error_msg
        
        cmd = [self.kubectl_binary] + args
        return self._execute_command(cmd, "kubectl", timeout)
    
    def execute_helm(self, args: List[str], timeout: int = 60) -> Tuple[bool, str]:
        """Execute a helm command"""
        if not self.helm_binary:
            error_msg = "Helm binary not found"
            self.logger.error(error_msg)
            return False, error_msg
        
        if not self.current_kubeconfig:
            error_msg = "No kubeconfig set"
            self.logger.error(error_msg)
            return False, error_msg
        
        cmd = [self.helm_binary] + args
        return self._execute_command(cmd, "helm", timeout)
    
    
    def _execute_command(self, cmd: List[str], cmd_type: str, timeout: int) -> Tuple[bool, str]:
        """Execute a command with proper environment and error handling"""
        try:
            env = os.environ.copy()
            env['KUBECONFIG'] = str(self.current_kubeconfig)
            
            self.logger.debug(f"Executing {cmd_type} command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                timeout=timeout,
                cwd=str(self.base_path)
            )
            
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            # Emit command execution event
            self.event_bus.emit_sync(
                EventType.COMMAND_EXECUTED,
                "command_executor",
                command_type=cmd_type,
                command=cmd,
                success=success,
                output=output
            )
            
            if success:
                self.logger.debug(f"{cmd_type} command succeeded")
            else:
                self.logger.error(f"{cmd_type} command failed: {result.stderr}")
            
            return success, output
            
        except subprocess.TimeoutExpired:
            error_msg = f"{cmd_type} command timed out after {timeout}s"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Failed to execute {cmd_type} command: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg