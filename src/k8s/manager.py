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
        self.logger = logger
        self.logger.debug("K8sManager.__init__: Entry - Initializing K8sManager")
        
        self.config = config
        self.event_bus = event_bus
        
        self.logger.debug("K8sManager.__init__: Configuration and event bus initialized")
        
        # Setup paths
        base_path = Path(config.get('k8s.base_path', Path.home() / ".clusterm" / "k8s"))
        self.k8s_path = base_path
        self.helm_charts_path = self.k8s_path / "projects" / "helm-charts"
        
        self.logger.debug(f"K8sManager.__init__: Paths configured - base: {base_path}, charts: {self.helm_charts_path}")
        
        # Ensure directories exist
        self.logger.debug("K8sManager.__init__: Ensuring directory structure")
        self._ensure_directory_structure()
        
        # Initialize components
        self.logger.debug("K8sManager.__init__: Initializing sub-components")
        
        self.logger.debug("K8sManager.__init__: Creating ClusterManager")
        self.cluster_manager = ClusterManager(
            self.k8s_path / "clusters", event_bus, logger
        )
        
        self.logger.debug("K8sManager.__init__: Creating CommandExecutor")
        self.command_executor = CommandExecutor(base_path, event_bus, logger)
        
        self.logger.debug("K8sManager.__init__: Creating ResourceManager")
        self.resource_manager = ResourceManager(self.command_executor, logger)
        
        # Set up initial cluster
        self.logger.debug("K8sManager.__init__: Setting up initial cluster")
        self._setup_initial_cluster()
        
        # Subscribe to cluster changes
        self.logger.debug("K8sManager.__init__: Subscribing to cluster change events")
        self.event_bus.subscribe(EventType.CLUSTER_CHANGED, self._on_cluster_changed)
        
        self.logger.info("K8sManager.__init__: K8sManager initialization completed successfully")
    
    def _ensure_directory_structure(self):
        """Ensure the required directory structure exists"""
        self.logger.debug("K8sManager._ensure_directory_structure: Entry")
        
        try:
            # Create base directories
            directories = [
                self.k8s_path,
                self.k8s_path / "clusters",
                self.k8s_path / "tools", 
                self.k8s_path / "projects",
                self.helm_charts_path
            ]
            
            self.logger.debug(f"K8sManager._ensure_directory_structure: Creating {len(directories)} directories")
            
            for i, directory in enumerate(directories):
                self.logger.debug(f"K8sManager._ensure_directory_structure: Creating directory {i+1}/{len(directories)}: {directory}")
                directory.mkdir(parents=True, exist_ok=True)
                
            self.logger.info(f"Initialized Clusterm directory structure at: {self.k8s_path}")
            
            # Create example kubeconfig if none exist
            clusters_dir = self.k8s_path / "clusters"
            self.logger.debug(f"K8sManager._ensure_directory_structure: Checking for existing clusters in: {clusters_dir}")
            
            if not any(clusters_dir.iterdir() if clusters_dir.exists() else []):
                self.logger.info("K8sManager._ensure_directory_structure: No existing clusters found, creating example structure")
                self._create_example_structure()
            else:
                self.logger.debug("K8sManager._ensure_directory_structure: Existing cluster configurations found")
                
            self.logger.info(f"K8sManager._ensure_directory_structure: Successfully initialized directory structure")
            
        except Exception as e:
            self.logger.error(f"K8sManager._ensure_directory_structure: Failed to create directory structure: {e}", extra={
                "error_type": type(e).__name__,
                "k8s_path": str(self.k8s_path)
            })
    
    def _create_example_structure(self):
        """Create example configuration structure for first-time users"""
        self.logger.debug("K8sManager._create_example_structure: Entry - Creating example configuration")
        
        try:
            # Create example cluster directory
            example_cluster = self.k8s_path / "clusters" / "example-cluster"
            self.logger.debug(f"K8sManager._create_example_structure: Creating example cluster directory: {example_cluster}")
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
            
            self.logger.info("K8sManager._create_example_structure: Created example configuration structure successfully")
            
        except Exception as e:
            self.logger.error(f"K8sManager._create_example_structure: Failed to create example structure: {e}", extra={
                "error_type": type(e).__name__,
                "k8s_path": str(self.k8s_path)
            })
    
    def _setup_initial_cluster(self):
        """Set up the initial cluster if available"""
        self.logger.debug("K8sManager._setup_initial_cluster: Entry")
        
        try:
            clusters = self.cluster_manager.get_available_clusters()
            self.logger.debug(f"K8sManager._setup_initial_cluster: Found {len(clusters)} available clusters")
            
            if clusters and not self.cluster_manager.current_cluster:
                initial_cluster = clusters[0]["name"]
                self.logger.info(f"K8sManager._setup_initial_cluster: Setting initial cluster to: {initial_cluster}")
                self.cluster_manager.set_current_cluster(initial_cluster)
            elif self.cluster_manager.current_cluster:
                self.logger.debug(f"K8sManager._setup_initial_cluster: Current cluster already set: {self.cluster_manager.current_cluster}")
            else:
                self.logger.warning("K8sManager._setup_initial_cluster: No clusters available")
                
        except Exception as e:
            self.logger.error(f"K8sManager._setup_initial_cluster: Error setting up initial cluster: {e}", extra={
                "error_type": type(e).__name__
            })
    
    def _on_cluster_changed(self, event):
        """Handle cluster change events"""
        self.logger.debug(f"K8sManager._on_cluster_changed: Entry - Event data: {event.data}")
        
        new_cluster = event.data.get('new_cluster')
        if new_cluster:
            self.logger.info(f"K8sManager._on_cluster_changed: Processing cluster change to: {new_cluster}")
            
            try:
                self.logger.debug("K8sManager._on_cluster_changed: Getting current kubeconfig")
                kubeconfig = self.cluster_manager.get_current_kubeconfig()
                
                self.logger.debug("K8sManager._on_cluster_changed: Setting kubeconfig for command executor")
                self.command_executor.set_kubeconfig(kubeconfig)
                
                self.logger.info(f"K8sManager._on_cluster_changed: Successfully processed cluster change to: {new_cluster}")
                
            except Exception as e:
                self.logger.error(f"K8sManager._on_cluster_changed: Error processing cluster change: {e}", extra={
                    "error_type": type(e).__name__,
                    "new_cluster": new_cluster
                })
        else:
            self.logger.warning("K8sManager._on_cluster_changed: No new_cluster provided in event data")
    
    def get_available_charts(self) -> List[Dict[str, str]]:
        """Get list of available Helm charts"""
        self.logger.debug("K8sManager.get_available_charts: Entry")
        
        charts = []
        if not self.helm_charts_path.exists():
            self.logger.warning(f"K8sManager.get_available_charts: Helm charts directory not found: {self.helm_charts_path}")
            return charts
        
        self.logger.debug(f"K8sManager.get_available_charts: Scanning charts directory: {self.helm_charts_path}")
        
        chart_dirs = list(self.helm_charts_path.iterdir())
        self.logger.debug(f"K8sManager.get_available_charts: Found {len(chart_dirs)} items in charts directory")
        
        for i, chart_dir in enumerate(chart_dirs):
            if chart_dir.is_dir() and (chart_dir / "Chart.yaml").exists():
                self.logger.debug(f"K8sManager.get_available_charts: Processing chart {i+1}/{len(chart_dirs)}: {chart_dir.name}")
                chart_info = {
                    "name": chart_dir.name,
                    "path": str(chart_dir),
                    "description": "No description",
                    "version": "unknown"
                }
                
                try:
                    self.logger.debug(f"K8sManager.get_available_charts: Reading Chart.yaml for {chart_dir.name}")
                    with open(chart_dir / "Chart.yaml", 'r') as f:
                        chart_yaml = yaml.safe_load(f)
                        chart_info["description"] = chart_yaml.get("description", "No description")
                        chart_info["version"] = chart_yaml.get("version", "unknown")
                        
                    self.logger.debug(f"K8sManager.get_available_charts: Chart {chart_dir.name} - version: {chart_info['version']}, desc: {chart_info['description'][:50]}...")
                    
                except Exception as e:
                    self.logger.warning(f"K8sManager.get_available_charts: Could not read Chart.yaml for {chart_dir.name}: {e}")
                
                charts.append(chart_info)
                self.logger.debug(f"K8sManager.get_available_charts: Added chart: {chart_dir.name}")
            else:
                self.logger.debug(f"K8sManager.get_available_charts: Skipping {chart_dir.name} - not a valid chart directory")
        
        self.logger.info(f"K8sManager.get_available_charts: Found {len(charts)} available charts")
        return charts
    
    def deploy_chart(self, chart_name: str, config: Dict) -> Tuple[bool, str]:
        """Deploy a Helm chart with given configuration"""
        self.logger.debug(f"K8sManager.deploy_chart: Entry - Deploying chart: {chart_name} with config: {config}")
        
        chart_path = self.helm_charts_path / chart_name
        if not chart_path.exists():
            self.logger.error(f"K8sManager.deploy_chart: Chart not found: {chart_name} at path: {chart_path}")
            return False, f"Chart {chart_name} not found"
        
        release_name = f"{chart_name}-{config.get('environment', 'default')}"
        namespace = config.get('namespace', 'default')
        
        self.logger.info(f"K8sManager.deploy_chart: Deploying {chart_name} as release {release_name} to namespace {namespace}")
        
        cmd = [
            "upgrade", "--install",
            release_name,
            str(chart_path),
            "--namespace", namespace,
            "--create-namespace"
        ]
        
        self.logger.debug(f"K8sManager.deploy_chart: Base helm command: {' '.join(cmd)}")
        
        # Add configuration overrides
        config_overrides = []
        if config.get('replicas'):
            override = f"replicaCount={config['replicas']}"
            cmd.extend(["--set", override])
            config_overrides.append(override)
        
        if config.get('environment'):
            override = f"environment={config['environment']}"
            cmd.extend(["--set", override])
            config_overrides.append(override)
        
        if config.get('monitoring'):
            override = "monitoring.enabled=true"
            cmd.extend(["--set", override])
            config_overrides.append(override)
        
        self.logger.debug(f"K8sManager.deploy_chart: Configuration overrides: {config_overrides}")
        self.logger.debug(f"K8sManager.deploy_chart: Final helm command: {' '.join(cmd)}")
        
        self.logger.debug("K8sManager.deploy_chart: Executing helm deployment command")
        success, output = self.command_executor.execute_helm(cmd)
        
        if success:
            self.logger.info(f"K8sManager.deploy_chart: Successfully deployed {chart_name} as {release_name}")
            
            self.logger.debug("K8sManager.deploy_chart: Emitting DEPLOYMENT_UPDATED event")
            self.event_bus.emit_sync(
                EventType.DEPLOYMENT_UPDATED,
                "k8s_manager",
                chart_name=chart_name,
                release_name=release_name,
                action="deployed"
            )
        else:
            self.logger.error(f"K8sManager.deploy_chart: Failed to deploy {chart_name}: {output}", extra={
                "chart_name": chart_name,
                "release_name": release_name,
                "namespace": namespace,
                "config": config
            })
        
        return success, output
    
    # Resource access methods
    def get_deployments(self, namespace: Optional[str] = None) -> List[Dict]:
        """Get deployments"""
        self.logger.debug(f"K8sManager.get_deployments: Entry - namespace: {namespace}")
        
        try:
            deployments = self.resource_manager.get_deployments(namespace)
            self.logger.debug(f"K8sManager.get_deployments: Retrieved {len(deployments)} deployments")
            return deployments
        except Exception as e:
            self.logger.error(f"K8sManager.get_deployments: Error getting deployments: {e}", extra={
                "error_type": type(e).__name__,
                "namespace": namespace
            })
            return []
    
    def get_pods(self, namespace: str = "default") -> List[Dict]:
        """Get pods"""
        self.logger.debug(f"K8sManager.get_pods: Entry - namespace: {namespace}")
        
        try:
            pods = self.resource_manager.get_pods(namespace)
            self.logger.debug(f"K8sManager.get_pods: Retrieved {len(pods)} pods")
            return pods
        except Exception as e:
            self.logger.error(f"K8sManager.get_pods: Error getting pods: {e}", extra={
                "error_type": type(e).__name__,
                "namespace": namespace
            })
            return []
    
    def get_services(self, namespace: str = "default") -> List[Dict]:
        """Get services"""
        self.logger.debug(f"K8sManager.get_services: Entry - namespace: {namespace}")
        
        try:
            services = self.resource_manager.get_services(namespace)
            self.logger.debug(f"K8sManager.get_services: Retrieved {len(services)} services")
            return services
        except Exception as e:
            self.logger.error(f"K8sManager.get_services: Error getting services: {e}", extra={
                "error_type": type(e).__name__,
                "namespace": namespace
            })
            return []
    
    def get_namespaces(self) -> List[Dict]:
        """Get namespaces"""
        self.logger.debug("K8sManager.get_namespaces: Entry")
        
        try:
            namespaces = self.resource_manager.get_namespaces()
            self.logger.debug(f"K8sManager.get_namespaces: Retrieved {len(namespaces)} namespaces")
            return namespaces
        except Exception as e:
            self.logger.error(f"K8sManager.get_namespaces: Error getting namespaces: {e}", extra={
                "error_type": type(e).__name__
            })
            return []
    
    def get_helm_releases(self, namespace: Optional[str] = None) -> List[Dict]:
        """Get helm releases"""
        self.logger.debug(f"K8sManager.get_helm_releases: Entry - namespace: {namespace}")
        
        try:
            releases = self.resource_manager.get_helm_releases(namespace)
            self.logger.debug(f"K8sManager.get_helm_releases: Retrieved {len(releases)} helm releases")
            return releases
        except Exception as e:
            self.logger.error(f"K8sManager.get_helm_releases: Error getting helm releases: {e}", extra={
                "error_type": type(e).__name__,
                "namespace": namespace
            })
            return []
    
    def get_pod_logs(self, pod_name: str, namespace: str = "default") -> str:
        """Get pod logs"""
        self.logger.debug(f"K8sManager.get_pod_logs: Entry - pod: {pod_name}, namespace: {namespace}")
        
        try:
            logs = self.resource_manager.get_pod_logs(pod_name, namespace)
            self.logger.debug(f"K8sManager.get_pod_logs: Retrieved {len(logs)} characters of logs for pod: {pod_name}")
            return logs
        except Exception as e:
            self.logger.error(f"K8sManager.get_pod_logs: Error getting pod logs: {e}", extra={
                "error_type": type(e).__name__,
                "pod_name": pod_name,
                "namespace": namespace
            })
            return f"Error getting logs for pod {pod_name}: {str(e)}"
    
    def describe_resource(self, resource_type: str, resource_name: str, namespace: Optional[str] = None) -> str:
        """Describe a resource"""
        self.logger.debug(f"K8sManager.describe_resource: Entry - type: {resource_type}, name: {resource_name}, namespace: {namespace}")
        
        try:
            description = self.resource_manager.describe_resource(resource_type, resource_name, namespace)
            self.logger.debug(f"K8sManager.describe_resource: Retrieved {len(description)} characters of description for {resource_type}: {resource_name}")
            return description
        except Exception as e:
            self.logger.error(f"K8sManager.describe_resource: Error describing resource: {e}", extra={
                "error_type": type(e).__name__,
                "resource_type": resource_type,
                "resource_name": resource_name,
                "namespace": namespace
            })
            return f"Error describing {resource_type} {resource_name}: {str(e)}"