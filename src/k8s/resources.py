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
        self.logger = logger
        self.logger.debug("ResourceManager.__init__: Entry - Initializing ResourceManager")
        
        self.executor = command_executor
        
        self.logger.info("ResourceManager.__init__: ResourceManager initialized successfully")
    
    def get_deployments(self, namespace: Optional[str] = None) -> List[Dict]:
        """Get current deployments"""
        self.logger.debug(f"ResourceManager.get_deployments: Entry - namespace: {namespace}")
        
        try:
            cmd = ["get", "deployments", "-o", "json"]
            if namespace:
                cmd.extend(["-n", namespace])
                self.logger.debug(f"ResourceManager.get_deployments: Getting deployments for namespace: {namespace}")
            else:
                cmd.append("--all-namespaces")
                self.logger.debug("ResourceManager.get_deployments: Getting deployments from all namespaces")
            
            self.logger.debug(f"ResourceManager.get_deployments: Executing kubectl command: {' '.join(cmd)}")
            
            success, output = self.executor.execute_kubectl(cmd)
            self.logger.debug(f"ResourceManager.get_deployments: Command result - success: {success}, output length: {len(output) if output else 0}")
            
            if success and output.strip():
                try:
                    data = json.loads(output)
                    deployments = data.get("items", [])
                    self.logger.info(f"ResourceManager.get_deployments: Successfully retrieved {len(deployments)} deployments")
                    return deployments
                except json.JSONDecodeError as e:
                    self.logger.error(f"ResourceManager.get_deployments: Failed to parse deployments JSON: {e}", extra={
                        "error_type": type(e).__name__,
                        "output_preview": output[:200] if output else "None"
                    })
            else:
                if not success:
                    self.logger.warning(f"ResourceManager.get_deployments: kubectl command failed: {output}")
                else:
                    self.logger.debug("ResourceManager.get_deployments: Empty output from kubectl")
                    
        except Exception as e:
            self.logger.error(f"ResourceManager.get_deployments: Failed to get deployments: {e}", extra={
                "error_type": type(e).__name__,
                "namespace": namespace
            })
        
        self.logger.debug("ResourceManager.get_deployments: Returning empty list")
        return []
    
    def get_pods(self, namespace: str = "default") -> List[Dict]:
        """Get pods in namespace"""
        self.logger.debug(f"ResourceManager.get_pods: Entry - namespace: {namespace}")
        
        try:
            cmd = ["get", "pods", "-n", namespace, "-o", "json"]
            self.logger.debug(f"ResourceManager.get_pods: Executing kubectl command: {' '.join(cmd)}")
            
            success, output = self.executor.execute_kubectl(cmd)
            self.logger.debug(f"ResourceManager.get_pods: Command result - success: {success}, output length: {len(output) if output else 0}")
            
            if success and output.strip():
                try:
                    data = json.loads(output)
                    pods = data.get("items", [])
                    self.logger.info(f"ResourceManager.get_pods: Successfully retrieved {len(pods)} pods from namespace: {namespace}")
                    return pods
                except json.JSONDecodeError as e:
                    self.logger.error(f"ResourceManager.get_pods: Failed to parse pods JSON: {e}", extra={
                        "error_type": type(e).__name__,
                        "namespace": namespace,
                        "output_preview": output[:200] if output else "None"
                    })
            else:
                if not success:
                    self.logger.warning(f"ResourceManager.get_pods: kubectl command failed for namespace {namespace}: {output}")
                else:
                    self.logger.debug(f"ResourceManager.get_pods: Empty output from kubectl for namespace: {namespace}")
                    
        except Exception as e:
            self.logger.error(f"ResourceManager.get_pods: Failed to get pods: {e}", extra={
                "error_type": type(e).__name__,
                "namespace": namespace
            })
        
        self.logger.debug(f"ResourceManager.get_pods: Returning empty list for namespace: {namespace}")
        return []
    
    def get_services(self, namespace: str = "default") -> List[Dict]:
        """Get services in namespace"""
        self.logger.debug(f"ResourceManager.get_services: Entry - namespace: {namespace}")
        
        try:
            cmd = ["get", "services", "-n", namespace, "-o", "json"]
            self.logger.debug(f"ResourceManager.get_services: Executing kubectl command: {' '.join(cmd)}")
            
            success, output = self.executor.execute_kubectl(cmd)
            self.logger.debug(f"ResourceManager.get_services: Command result - success: {success}, output length: {len(output) if output else 0}")
            
            if success and output.strip():
                try:
                    data = json.loads(output)
                    services = data.get("items", [])
                    self.logger.info(f"ResourceManager.get_services: Successfully retrieved {len(services)} services from namespace: {namespace}")
                    return services
                except json.JSONDecodeError as e:
                    self.logger.error(f"ResourceManager.get_services: Failed to parse services JSON: {e}", extra={
                        "error_type": type(e).__name__,
                        "namespace": namespace,
                        "output_preview": output[:200] if output else "None"
                    })
            else:
                if not success:
                    self.logger.warning(f"ResourceManager.get_services: kubectl command failed for namespace {namespace}: {output}")
                else:
                    self.logger.debug(f"ResourceManager.get_services: Empty output from kubectl for namespace: {namespace}")
                    
        except Exception as e:
            self.logger.error(f"ResourceManager.get_services: Failed to get services: {e}", extra={
                "error_type": type(e).__name__,
                "namespace": namespace
            })
        
        self.logger.debug(f"ResourceManager.get_services: Returning empty list for namespace: {namespace}")
        return []
    
    def get_namespaces(self) -> List[Dict]:
        """Get all namespaces"""
        self.logger.debug("ResourceManager.get_namespaces: Entry")
        
        try:
            cmd = ["get", "namespaces", "-o", "json"]
            self.logger.debug(f"ResourceManager.get_namespaces: Executing kubectl command: {' '.join(cmd)}")
            
            success, output = self.executor.execute_kubectl(cmd)
            self.logger.debug(f"ResourceManager.get_namespaces: Command result - success: {success}, output length: {len(output) if output else 0}")
            
            if success and output.strip():
                try:
                    data = json.loads(output)
                    namespaces = data.get("items", [])
                    namespace_names = [ns.get('metadata', {}).get('name', 'unknown') for ns in namespaces]
                    self.logger.info(f"ResourceManager.get_namespaces: Successfully retrieved {len(namespaces)} namespaces: {namespace_names}")
                    return namespaces
                except json.JSONDecodeError as e:
                    self.logger.error(f"ResourceManager.get_namespaces: Failed to parse namespaces JSON: {e}", extra={
                        "error_type": type(e).__name__,
                        "output_preview": output[:200] if output else "None"
                    })
            else:
                if not success:
                    self.logger.warning(f"ResourceManager.get_namespaces: kubectl command failed: {output}")
                else:
                    self.logger.debug("ResourceManager.get_namespaces: Empty output from kubectl")
                    
        except Exception as e:
            self.logger.error(f"ResourceManager.get_namespaces: Failed to get namespaces: {e}", extra={
                "error_type": type(e).__name__
            })
        
        self.logger.debug("ResourceManager.get_namespaces: Returning empty list")
        return []
    
    def get_helm_releases(self, namespace: Optional[str] = None) -> List[Dict]:
        """Get helm releases"""
        self.logger.debug(f"ResourceManager.get_helm_releases: Entry - namespace: {namespace}")
        
        try:
            cmd = ["list", "-o", "json"]
            if namespace:
                cmd.extend(["-n", namespace])
                self.logger.debug(f"ResourceManager.get_helm_releases: Getting helm releases for namespace: {namespace}")
            else:
                cmd.append("--all-namespaces")
                self.logger.debug("ResourceManager.get_helm_releases: Getting helm releases from all namespaces")
            
            self.logger.debug(f"ResourceManager.get_helm_releases: Executing helm command: {' '.join(cmd)}")
            
            success, output = self.executor.execute_helm(cmd)
            self.logger.debug(f"ResourceManager.get_helm_releases: Command result - success: {success}, output length: {len(output) if output else 0}")
            
            if success and output.strip():
                try:
                    releases = json.loads(output)
                    self.logger.info(f"ResourceManager.get_helm_releases: Successfully retrieved {len(releases)} helm releases")
                    return releases
                except json.JSONDecodeError as e:
                    self.logger.error(f"ResourceManager.get_helm_releases: Failed to parse helm releases JSON: {e}", extra={
                        "error_type": type(e).__name__,
                        "namespace": namespace,
                        "output_preview": output[:200] if output else "None"
                    })
            else:
                if not success:
                    self.logger.warning(f"ResourceManager.get_helm_releases: helm command failed: {output}")
                else:
                    self.logger.debug("ResourceManager.get_helm_releases: Empty output from helm")
                    
        except Exception as e:
            self.logger.error(f"ResourceManager.get_helm_releases: Failed to get helm releases: {e}", extra={
                "error_type": type(e).__name__,
                "namespace": namespace
            })
        
        self.logger.debug("ResourceManager.get_helm_releases: Returning empty list")
        return []
    
    def get_pod_logs(self, pod_name: str, namespace: str = "default", lines: int = 100) -> str:
        """Get logs from a pod"""
        self.logger.debug(f"ResourceManager.get_pod_logs: Entry - pod: {pod_name}, namespace: {namespace}, lines: {lines}")
        
        try:
            cmd = ["logs", pod_name, "-n", namespace, f"--tail={lines}"]
            self.logger.debug(f"ResourceManager.get_pod_logs: Executing kubectl command: {' '.join(cmd)}")
            
            success, output = self.executor.execute_kubectl(cmd)
            self.logger.debug(f"ResourceManager.get_pod_logs: Command result - success: {success}, output length: {len(output) if output else 0}")
            
            if success:
                self.logger.info(f"ResourceManager.get_pod_logs: Successfully retrieved logs for pod {pod_name} ({len(output)} characters)")
                return output
            else:
                self.logger.warning(f"ResourceManager.get_pod_logs: Failed to get logs for pod {pod_name}: {output}")
                return f"Failed to get logs: {output}"
                
        except Exception as e:
            self.logger.error(f"ResourceManager.get_pod_logs: Failed to get pod logs: {e}", extra={
                "error_type": type(e).__name__,
                "pod_name": pod_name,
                "namespace": namespace,
                "lines": lines
            })
            return f"Error getting logs: {str(e)}"
    
    def describe_resource(self, resource_type: str, resource_name: str, namespace: Optional[str] = None) -> str:
        """Describe a Kubernetes resource"""
        self.logger.debug(f"ResourceManager.describe_resource: Entry - type: {resource_type}, name: {resource_name}, namespace: {namespace}")
        
        try:
            cmd = ["describe", resource_type, resource_name]
            if namespace:
                cmd.extend(["-n", namespace])
                self.logger.debug(f"ResourceManager.describe_resource: Including namespace in command: {namespace}")
            
            self.logger.debug(f"ResourceManager.describe_resource: Executing kubectl command: {' '.join(cmd)}")
            
            success, output = self.executor.execute_kubectl(cmd)
            self.logger.debug(f"ResourceManager.describe_resource: Command result - success: {success}, output length: {len(output) if output else 0}")
            
            if success:
                self.logger.info(f"ResourceManager.describe_resource: Successfully described {resource_type} {resource_name} ({len(output)} characters)")
                return output
            else:
                self.logger.warning(f"ResourceManager.describe_resource: Failed to describe {resource_type} {resource_name}: {output}")
                return f"Failed to describe {resource_type}: {output}"
                
        except Exception as e:
            self.logger.error(f"ResourceManager.describe_resource: Failed to describe {resource_type}: {e}", extra={
                "error_type": type(e).__name__,
                "resource_type": resource_type,
                "resource_name": resource_name,
                "namespace": namespace
            })
            return f"Error describing resource: {str(e)}"