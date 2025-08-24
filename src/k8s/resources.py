"""
Kubernetes resource management
"""

import json
from typing import List, Dict, Optional
from ..core.exceptions import K8sError
from ..core.logger import Logger
from .commands import CommandExecutor


class ResourceManager:
    """Manage Kubernetes resources"""
    
    def __init__(self, command_executor: CommandExecutor, logger: Logger):
        self.executor = command_executor
        self.logger = logger
    
    def get_deployments(self, namespace: Optional[str] = None) -> List[Dict]:
        """Get current deployments"""
        try:
            cmd = ["get", "deployments", "-o", "json"]
            if namespace:
                cmd.extend(["-n", namespace])
            else:
                cmd.append("--all-namespaces")
            
            success, output = self.executor.execute_kubectl(cmd)
            if success and output.strip():
                data = json.loads(output)
                return data.get("items", [])
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse deployments JSON: {e}")
        except Exception as e:
            self.logger.error(f"Failed to get deployments: {e}")
        
        return []
    
    def get_pods(self, namespace: str = "default") -> List[Dict]:
        """Get pods in namespace"""
        try:
            cmd = ["get", "pods", "-n", namespace, "-o", "json"]
            success, output = self.executor.execute_kubectl(cmd)
            if success and output.strip():
                data = json.loads(output)
                return data.get("items", [])
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse pods JSON: {e}")
        except Exception as e:
            self.logger.error(f"Failed to get pods: {e}")
        
        return []
    
    def get_services(self, namespace: str = "default") -> List[Dict]:
        """Get services in namespace"""
        try:
            cmd = ["get", "services", "-n", namespace, "-o", "json"]
            success, output = self.executor.execute_kubectl(cmd)
            if success and output.strip():
                data = json.loads(output)
                return data.get("items", [])
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse services JSON: {e}")
        except Exception as e:
            self.logger.error(f"Failed to get services: {e}")
        
        return []
    
    def get_namespaces(self) -> List[Dict]:
        """Get all namespaces"""
        try:
            cmd = ["get", "namespaces", "-o", "json"]
            success, output = self.executor.execute_kubectl(cmd)
            if success and output.strip():
                data = json.loads(output)
                return data.get("items", [])
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse namespaces JSON: {e}")
        except Exception as e:
            self.logger.error(f"Failed to get namespaces: {e}")
        
        return []
    
    def get_helm_releases(self, namespace: Optional[str] = None) -> List[Dict]:
        """Get helm releases"""
        try:
            cmd = ["list", "-o", "json"]
            if namespace:
                cmd.extend(["-n", namespace])
            else:
                cmd.append("--all-namespaces")
            
            success, output = self.executor.execute_helm(cmd)
            if success and output.strip():
                return json.loads(output)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse helm releases JSON: {e}")
        except Exception as e:
            self.logger.error(f"Failed to get helm releases: {e}")
        
        return []
    
    def get_pod_logs(self, pod_name: str, namespace: str = "default", lines: int = 100) -> str:
        """Get logs from a pod"""
        try:
            cmd = ["logs", pod_name, "-n", namespace, f"--tail={lines}"]
            success, output = self.executor.execute_kubectl(cmd)
            return output if success else f"Failed to get logs: {output}"
        except Exception as e:
            self.logger.error(f"Failed to get pod logs: {e}")
            return f"Error getting logs: {str(e)}"
    
    def describe_resource(self, resource_type: str, resource_name: str, namespace: Optional[str] = None) -> str:
        """Describe a Kubernetes resource"""
        try:
            cmd = ["describe", resource_type, resource_name]
            if namespace:
                cmd.extend(["-n", namespace])
            
            success, output = self.executor.execute_kubectl(cmd)
            return output if success else f"Failed to describe {resource_type}: {output}"
        except Exception as e:
            self.logger.error(f"Failed to describe {resource_type}: {e}")
            return f"Error describing resource: {str(e)}"