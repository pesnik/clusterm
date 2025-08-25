"""
Main Kubernetes manager - coordinates all K8s operations
"""

import yaml
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from ..core.config import Config
from ..core.logger import Logger
from ..core.events import EventBus, EventType
from .cluster import ClusterManager
from .resources import ResourceManager
from .commands import CommandExecutor


class K8sManager:
    """Main manager for Kubernetes operations"""
    
    def __init__(self, config: Config, event_bus: EventBus, logger: Logger):
        self.config = config
        self.event_bus = event_bus
        self.logger = logger
        
        # Setup paths
        base_path = Path(config.get('k8s.base_path', Path.home() / ".clusterm" / "k8s"))
        self.k8s_path = base_path
        self.helm_charts_path = self.k8s_path / "projects" / "helm-charts"
        
        # Ensure directories exist
        self._ensure_directory_structure()
        
        # Initialize components
        self.cluster_manager = ClusterManager(
            self.k8s_path / "clusters", event_bus, logger
        )
        self.command_executor = CommandExecutor(base_path, event_bus, logger)
        self.resource_manager = ResourceManager(self.command_executor, logger)
        
        # Set up initial cluster
        self._setup_initial_cluster()
        
        # Subscribe to cluster changes
        self.event_bus.subscribe(EventType.CLUSTER_CHANGED, self._on_cluster_changed)
    
    def _ensure_directory_structure(self):
        """Ensure the required directory structure exists"""
        try:
            # Create base directories
            directories = [
                self.k8s_path,
                self.k8s_path / "clusters",
                self.k8s_path / "tools", 
                self.k8s_path / "projects",
                self.helm_charts_path
            ]
            
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                
            self.logger.info(f"Initialized Clusterm directory structure at: {self.k8s_path}")
            
            # Create example kubeconfig if none exist
            clusters_dir = self.k8s_path / "clusters"
            if not any(clusters_dir.iterdir() if clusters_dir.exists() else []):
                self._create_example_structure()
                
        except Exception as e:
            self.logger.error(f"Failed to create directory structure: {e}")
    
    def _create_example_structure(self):
        """Create example configuration structure for first-time users"""
        try:
            # Create example cluster directory
            example_cluster = self.k8s_path / "clusters" / "example-cluster"
            example_cluster.mkdir(exist_ok=True)
            
            # Create example kubeconfig with instructions
            kubeconfig_example = example_cluster / "kubeconfig.example"
            kubeconfig_example.write_text("""# Example kubeconfig file
# 1. Copy your actual kubeconfig here and rename to 'kubeconfig' (without .example)
# 2. Or create a symlink to your existing kubeconfig:
#    ln -s ~/.kube/config kubeconfig
#
# You can have multiple cluster directories under ~/.clusterm/k8s/clusters/
# Each cluster directory should contain a 'kubeconfig' file

apiVersion: v1
kind: Config
contexts:
- context:
    cluster: example-cluster
    user: example-user
  name: example-context
current-context: example-context
clusters:
- cluster:
    server: https://your-kubernetes-api-server:6443
  name: example-cluster
users:
- name: example-user
  user:
    # Add your authentication config here
""")
            
            # Create tools directory with instructions
            tools_readme = self.k8s_path / "tools" / "README.md"
            tools_readme.write_text("""# Tools Directory

Place your kubectl and helm binaries here, or ensure they're in your system PATH.

## Option 1: System PATH (Recommended)
- Install kubectl and helm normally on your system
- Clusterm will find them automatically

## Option 2: Local Tools
- Download kubectl binary and place as: `kubectl`
- Download helm binary and place as: `helm`
- Make sure they're executable: `chmod +x kubectl helm`

## Downloads:
- kubectl: https://kubernetes.io/docs/tasks/tools/install-kubectl/
- helm: https://helm.sh/docs/intro/install/
""")
            
            # Create example helm chart
            example_chart = self.helm_charts_path / "example-app"
            example_chart.mkdir(exist_ok=True)
            
            chart_yaml = example_chart / "Chart.yaml"
            chart_yaml.write_text("""apiVersion: v2
name: example-app
description: An example Helm chart for Clusterm
version: 1.0.0
appVersion: 1.0.0
""")
            
            values_yaml = example_chart / "values.yaml"
            values_yaml.write_text("""# Example values file
replicaCount: 1

image:
  repository: nginx
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: false

resources: {}
""")
            
            self.logger.info("Created example configuration structure")
            
        except Exception as e:
            self.logger.error(f"Failed to create example structure: {e}")
    
    def _setup_initial_cluster(self):
        """Set up the initial cluster if available"""
        clusters = self.cluster_manager.get_available_clusters()
        if clusters and not self.cluster_manager.current_cluster:
            self.cluster_manager.set_current_cluster(clusters[0]["name"])
    
    def _on_cluster_changed(self, event):
        """Handle cluster change events"""
        new_cluster = event.data.get('new_cluster')
        if new_cluster:
            kubeconfig = self.cluster_manager.get_current_kubeconfig()
            self.command_executor.set_kubeconfig(kubeconfig)
    
    def get_available_charts(self) -> List[Dict[str, str]]:
        """Get list of available Helm charts"""
        charts = []
        if not self.helm_charts_path.exists():
            self.logger.warning(f"Helm charts directory not found: {self.helm_charts_path}")
            return charts
        
        for chart_dir in self.helm_charts_path.iterdir():
            if chart_dir.is_dir() and (chart_dir / "Chart.yaml").exists():
                chart_info = {
                    "name": chart_dir.name,
                    "path": str(chart_dir),
                    "description": "No description",
                    "version": "unknown"
                }
                
                try:
                    with open(chart_dir / "Chart.yaml", 'r') as f:
                        chart_yaml = yaml.safe_load(f)
                        chart_info["description"] = chart_yaml.get("description", "No description")
                        chart_info["version"] = chart_yaml.get("version", "unknown")
                except Exception as e:
                    self.logger.warning(f"Could not read Chart.yaml for {chart_dir.name}: {e}")
                
                charts.append(chart_info)
        
        return charts
    
    def deploy_chart(self, chart_name: str, config: Dict) -> Tuple[bool, str]:
        """Deploy a Helm chart with given configuration"""
        chart_path = self.helm_charts_path / chart_name
        if not chart_path.exists():
            return False, f"Chart {chart_name} not found"
        
        release_name = f"{chart_name}-{config.get('environment', 'default')}"
        
        cmd = [
            "upgrade", "--install",
            release_name,
            str(chart_path),
            "--namespace", config.get('namespace', 'default'),
            "--create-namespace"
        ]
        
        # Add configuration overrides
        if config.get('replicas'):
            cmd.extend(["--set", f"replicaCount={config['replicas']}"])
        
        if config.get('environment'):
            cmd.extend(["--set", f"environment={config['environment']}"])
        
        if config.get('monitoring'):
            cmd.extend(["--set", "monitoring.enabled=true"])
        
        success, output = self.command_executor.execute_helm(cmd)
        
        if success:
            self.event_bus.emit_sync(
                EventType.DEPLOYMENT_UPDATED,
                "k8s_manager",
                chart_name=chart_name,
                release_name=release_name,
                action="deployed"
            )
            self.logger.info(f"Successfully deployed {chart_name}")
        else:
            self.logger.error(f"Failed to deploy {chart_name}: {output}")
        
        return success, output
    
    # Resource access methods
    def get_deployments(self, namespace: Optional[str] = None) -> List[Dict]:
        """Get deployments"""
        return self.resource_manager.get_deployments(namespace)
    
    def get_pods(self, namespace: str = "default") -> List[Dict]:
        """Get pods"""
        return self.resource_manager.get_pods(namespace)
    
    def get_services(self, namespace: str = "default") -> List[Dict]:
        """Get services"""
        return self.resource_manager.get_services(namespace)
    
    def get_namespaces(self) -> List[Dict]:
        """Get namespaces"""
        return self.resource_manager.get_namespaces()
    
    def get_helm_releases(self, namespace: Optional[str] = None) -> List[Dict]:
        """Get helm releases"""
        return self.resource_manager.get_helm_releases(namespace)
    
    def get_pod_logs(self, pod_name: str, namespace: str = "default") -> str:
        """Get pod logs"""
        return self.resource_manager.get_pod_logs(pod_name, namespace)
    
    def describe_resource(self, resource_type: str, resource_name: str, namespace: Optional[str] = None) -> str:
        """Describe a resource"""
        return self.resource_manager.describe_resource(resource_type, resource_name, namespace)