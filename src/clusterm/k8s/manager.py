"""Main Kubernetes manager - coordinates all K8s operations
"""

from pathlib import Path

import yaml

from ..core.config import Config
from ..core.events import EventBus, EventType
from ..core.logger import Logger
from .cluster import ClusterManager
from .commands import CommandExecutor
from .resources import ResourceManager


class K8sManager:
    """Main manager for Kubernetes operations"""

    def __init__(self, config: Config, event_bus: EventBus, logger: Logger):
        self.logger = logger
        self.logger.debug("K8sManager.__init__: Entry - Initializing K8sManager")

        self.config = config
        self.event_bus = event_bus

        self.logger.debug("K8sManager.__init__: Configuration and event bus initialized")

        # Setup paths
        base_path = Path(config.get("k8s.base_path", Path.home() / ".clusterm" / "k8s"))
        self.k8s_path = base_path

        # Initialize cluster-aware project paths (will be set based on current context)
        self.current_cluster_path = None
        self.current_projects_path = None

        self.logger.debug(f"K8sManager.__init__: Paths configured - base: {base_path}")

        # Ensure directories exist
        self.logger.debug("K8sManager.__init__: Ensuring directory structure")
        self._ensure_directory_structure()

        # Initialize components
        self.logger.debug("K8sManager.__init__: Initializing sub-components")

        self.logger.debug("K8sManager.__init__: Creating ClusterManager")
        self.cluster_manager = ClusterManager(
            self.k8s_path / "clusters", event_bus, logger,
        )

        self.logger.debug("K8sManager.__init__: Creating CommandExecutor")
        self.command_executor = CommandExecutor(base_path, event_bus, logger)

        self.logger.debug("K8sManager.__init__: Creating ResourceManager")
        self.resource_manager = ResourceManager(self.command_executor, logger)

        # Subscribe to cluster changes BEFORE setting up initial cluster
        self.logger.debug("K8sManager.__init__: Subscribing to cluster change events")
        self.event_bus.subscribe(EventType.CLUSTER_CHANGED, self._on_cluster_changed)

        # Set up initial cluster (now the event handler will be called)
        self.logger.debug("K8sManager.__init__: Setting up initial cluster")
        self._setup_initial_cluster()

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
            ]

            self.logger.debug(f"K8sManager._ensure_directory_structure: Creating {len(directories)} base directories")

            for i, directory in enumerate(directories):
                self.logger.debug(f"K8sManager._ensure_directory_structure: Creating directory {i+1}/{len(directories)}: {directory}")
                directory.mkdir(parents=True, exist_ok=True)

            self.logger.info(f"Initialized Clusterm directory structure at: {self.k8s_path}")

            # Create example kubeconfig if none exist
            clusters_dir = self.k8s_path / "clusters"
            self.logger.debug(f"K8sManager._ensure_directory_structure: Checking for existing clusters in: {clusters_dir}")

            if not any(clusters_dir.iterdir() if clusters_dir.exists() else []):
                self.logger.info("K8sManager._ensure_directory_structure: No existing clusters found, creating example structure")
                self._create_basic_structure()
            else:
                self.logger.debug("K8sManager._ensure_directory_structure: Existing cluster configurations found")

            self.logger.info("K8sManager._ensure_directory_structure: Successfully initialized directory structure")

        except Exception as e:
            self.logger.error(f"K8sManager._ensure_directory_structure: Failed to create directory structure: {e}", extra={
                "error_type": type(e).__name__,
                "k8s_path": str(self.k8s_path),
            })

    def _create_basic_structure(self):
        """Create minimal required directory structure"""
        self.logger.debug("K8sManager._create_basic_structure: Entry - Creating basic directories")

        try:
            # Create tools directory with instructions only
            tools_readme = self.k8s_path / "tools" / "README.md"
            if not tools_readme.exists():
                tools_readme.parent.mkdir(exist_ok=True)
                tools_readme.write_text("""# Tools Directory

Place your kubectl and helm binaries here, or ensure they're in your system PATH.

## Recommended: System PATH
- Install kubectl and helm normally on your system
- Clusterm will find them automatically

## Alternative: Local Tools
- Download kubectl binary and place as: `kubectl`
- Download helm binary and place as: `helm`  
- Make them executable: `chmod +x kubectl helm`

## Downloads
- kubectl: https://kubernetes.io/docs/tasks/tools/install-kubectl/
- helm: https://helm.sh/docs/intro/install/
""")

            self.logger.info("K8sManager._create_basic_structure: Created basic directory structure")

        except Exception as e:
            self.logger.error(f"K8sManager._create_basic_structure: Failed to create basic structure: {e}", extra={
                "error_type": type(e).__name__,
                "k8s_path": str(self.k8s_path),
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
                # Set up initial paths
                self._update_cluster_paths(initial_cluster)
            elif self.cluster_manager.current_cluster:
                self.logger.debug(f"K8sManager._setup_initial_cluster: Current cluster already set: {self.cluster_manager.current_cluster}")
                # Ensure paths are set for current cluster
                self._update_cluster_paths(self.cluster_manager.current_cluster)
            else:
                self.logger.warning("K8sManager._setup_initial_cluster: No clusters available")

        except Exception as e:
            self.logger.error(f"K8sManager._setup_initial_cluster: Error setting up initial cluster: {e}", extra={
                "error_type": type(e).__name__,
            })

    def _on_cluster_changed(self, event):
        """Handle cluster change events"""
        self.logger.debug(f"K8sManager._on_cluster_changed: Entry - Event data: {event.data}")

        new_cluster = event.data.get("new_cluster")
        if new_cluster:
            self.logger.info(f"K8sManager._on_cluster_changed: Processing cluster change to: {new_cluster}")

            try:
                self.logger.debug("K8sManager._on_cluster_changed: Getting current kubeconfig")
                kubeconfig = self.cluster_manager.get_current_kubeconfig()

                self.logger.debug("K8sManager._on_cluster_changed: Setting kubeconfig for command executor")
                self.command_executor.set_kubeconfig(kubeconfig)

                # Update cluster-aware paths
                self._update_cluster_paths(new_cluster)

                self.logger.info(f"K8sManager._on_cluster_changed: Successfully processed cluster change to: {new_cluster}")

            except Exception as e:
                self.logger.error(f"K8sManager._on_cluster_changed: Error processing cluster change: {e}", extra={
                    "error_type": type(e).__name__,
                    "new_cluster": new_cluster,
                })
        else:
            self.logger.warning("K8sManager._on_cluster_changed: No new_cluster provided in event data")

    def _update_cluster_paths(self, cluster_name: str):
        """Update cluster-aware project paths when cluster changes"""
        self.logger.debug(f"K8sManager._update_cluster_paths: Updating paths for cluster: {cluster_name}")

        self.current_cluster_path = self.k8s_path / "clusters" / cluster_name
        self.current_projects_path = self.current_cluster_path / "projects"

        # Ensure projects directory exists
        self.current_projects_path.mkdir(parents=True, exist_ok=True)

        self.logger.debug(f"K8sManager._update_cluster_paths: Updated paths - cluster: {self.current_cluster_path}, projects: {self.current_projects_path}")

    def get_current_namespace_projects_path(self, namespace: str = "default") -> Path | None:
        """Get the projects path for the current cluster and namespace"""
        if not self.current_projects_path:
            self.logger.warning("K8sManager.get_current_namespace_projects_path: No current cluster set")
            return None

        namespace_path = self.current_projects_path / namespace
        namespace_path.mkdir(parents=True, exist_ok=True)

        return namespace_path

    def get_available_projects(self, namespace: str = "default") -> dict[str, list[dict[str, str]]]:
        """Get all available projects (helm-charts, manifests, apps) for current cluster and namespace"""
        self.logger.debug(f"K8sManager.get_available_projects: Entry - namespace: {namespace}")

        projects = {
            "helm-charts": [],
            "manifests": [],
            "apps": [],
            "other": []
        }

        # Get namespace projects path for current cluster
        namespace_path = self.get_current_namespace_projects_path(namespace)
        if not namespace_path or not namespace_path.exists():
            self.logger.warning(f"K8sManager.get_available_projects: Projects directory not found for namespace: {namespace}")
            return projects

        self.logger.debug(f"K8sManager.get_available_projects: Scanning projects in: {namespace_path}")

        # Scan for different project types
        for project_type_dir in namespace_path.iterdir():
            if not project_type_dir.is_dir():
                continue

            project_type = project_type_dir.name.lower()
            self.logger.debug(f"K8sManager.get_available_projects: Found project type directory: {project_type}")

            # Determine project category
            if project_type in ["helm-charts", "helm", "charts"]:
                category = "helm-charts"
            elif project_type in ["manifests", "yaml", "yamls", "k8s"]:
                category = "manifests"
            elif project_type in ["apps", "applications"]:
                category = "apps"
            else:
                category = "other"

            # Scan projects within this type
            project_items = self._scan_project_directory(project_type_dir, category)
            projects[category].extend(project_items)

        total_projects = sum(len(items) for items in projects.values())
        self.logger.info(f"K8sManager.get_available_projects: Found {total_projects} projects in {namespace} namespace")
        return projects

    def _scan_project_directory(self, project_dir: Path, project_type: str) -> list[dict[str, str]]:
        """Scan a project directory for individual projects"""
        items = []

        for item_path in project_dir.iterdir():
            if not item_path.is_dir():
                continue

            item_info = {
                "name": item_path.name,
                "path": str(item_path),
                "type": project_type,
                "namespace": project_dir.parent.name,
                "cluster": self.cluster_manager.current_cluster or "unknown",
                "description": "No description",
                "version": "unknown",
            }

            # Type-specific processing
            if project_type == "helm-charts":
                # Check for Chart.yaml
                if (item_path / "Chart.yaml").exists():
                    try:
                        with open(item_path / "Chart.yaml") as f:
                            chart_yaml = yaml.safe_load(f)
                            item_info["description"] = chart_yaml.get("description", "Helm chart")
                            item_info["version"] = chart_yaml.get("version", "unknown")
                            item_info["app_version"] = chart_yaml.get("appVersion", "unknown")
                    except Exception as e:
                        self.logger.warning(f"K8sManager._scan_project_directory: Could not read Chart.yaml for {item_path.name}: {e}")
                        item_info["description"] = "Helm chart (error reading Chart.yaml)"
                else:
                    # Skip if no Chart.yaml
                    continue

            elif project_type == "manifests":
                # Check for YAML files
                yaml_files = list(item_path.glob("*.yaml")) + list(item_path.glob("*.yml"))
                if yaml_files:
                    item_info["description"] = f"Kubernetes manifests ({len(yaml_files)} files)"
                else:
                    item_info["description"] = "Kubernetes manifests directory"

            elif project_type == "apps":
                # Check for common app files
                app_files = (
                    list(item_path.glob("*.yaml")) +
                    list(item_path.glob("*.yml")) +
                    list(item_path.glob("Dockerfile")) +
                    list(item_path.glob("docker-compose.yml"))
                )
                if app_files:
                    item_info["description"] = f"Application ({len(app_files)} files)"
                else:
                    item_info["description"] = "Application directory"

            else:
                item_info["description"] = f"{project_type.title()} project"

            items.append(item_info)

        self.logger.debug(f"K8sManager._scan_project_directory: Found {len(items)} items in {project_dir.name}")
        return items

    def get_available_charts(self, namespace: str = "default") -> list[dict[str, str]]:
        """Get list of available Helm charts for current cluster and namespace (backward compatibility)"""
        self.logger.debug(f"K8sManager.get_available_charts: Entry - namespace: {namespace}")

        projects = self.get_available_projects(namespace)
        charts = projects.get("helm-charts", [])

        self.logger.info(f"K8sManager.get_available_charts: Found {len(charts)} Helm charts in {namespace} namespace")
        return charts

    def deploy_chart(self, chart_name: str, config: dict) -> tuple[bool, str]:
        """Deploy a Helm chart with given configuration from current cluster/namespace context"""
        self.logger.debug(f"K8sManager.deploy_chart: Entry - Deploying chart: {chart_name} with config: {config}")

        namespace = config.get("namespace", "default")

        # Find chart in current cluster/namespace context
        namespace_path = self.get_current_namespace_projects_path(namespace)
        if not namespace_path:
            self.logger.error("K8sManager.deploy_chart: No current cluster set")
            return False, "No current cluster configured"

        chart_path = namespace_path / chart_name
        if not chart_path.exists():
            self.logger.error(f"K8sManager.deploy_chart: Chart not found: {chart_name} at path: {chart_path}")
            cluster_name = self.cluster_manager.current_cluster or "unknown"
            return False, f"Chart {chart_name} not found in {cluster_name}/{namespace}"

        release_name = f"{chart_name}-{config.get('environment', 'default')}"

        self.logger.info(f"K8sManager.deploy_chart: Deploying {chart_name} as release {release_name} to namespace {namespace}")

        cmd = [
            "upgrade", "--install",
            release_name,
            str(chart_path),
            "--namespace", namespace,
            "--create-namespace",
        ]

        self.logger.debug(f"K8sManager.deploy_chart: Base helm command: {' '.join(cmd)}")

        # Add configuration overrides
        config_overrides = []
        if config.get("replicas"):
            override = f"replicaCount={config['replicas']}"
            cmd.extend(["--set", override])
            config_overrides.append(override)

        if config.get("environment"):
            override = f"environment={config['environment']}"
            cmd.extend(["--set", override])
            config_overrides.append(override)

        if config.get("monitoring"):
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
                action="deployed",
                cluster=self.cluster_manager.current_cluster,
                namespace=namespace,
            )
        else:
            self.logger.error(f"K8sManager.deploy_chart: Failed to deploy {chart_name}: {output}", extra={
                "chart_name": chart_name,
                "release_name": release_name,
                "namespace": namespace,
                "config": config,
                "cluster": self.cluster_manager.current_cluster,
            })

        return success, output

    # Resource access methods
    def get_deployments(self, namespace: str | None = None) -> list[dict]:
        """Get deployments"""
        self.logger.debug(f"K8sManager.get_deployments: Entry - namespace: {namespace}")

        try:
            deployments = self.resource_manager.get_deployments(namespace)
            self.logger.debug(f"K8sManager.get_deployments: Retrieved {len(deployments)} deployments")
            return deployments
        except Exception as e:
            self.logger.error(f"K8sManager.get_deployments: Error getting deployments: {e}", extra={
                "error_type": type(e).__name__,
                "namespace": namespace,
            })
            return []

    def get_pods(self, namespace: str = "default") -> list[dict]:
        """Get pods"""
        self.logger.debug(f"K8sManager.get_pods: Entry - namespace: {namespace}")

        try:
            pods = self.resource_manager.get_pods(namespace)
            self.logger.debug(f"K8sManager.get_pods: Retrieved {len(pods)} pods")
            return pods
        except Exception as e:
            self.logger.error(f"K8sManager.get_pods: Error getting pods: {e}", extra={
                "error_type": type(e).__name__,
                "namespace": namespace,
            })
            return []

    def get_services(self, namespace: str = "default") -> list[dict]:
        """Get services"""
        self.logger.debug(f"K8sManager.get_services: Entry - namespace: {namespace}")

        try:
            services = self.resource_manager.get_services(namespace)
            self.logger.debug(f"K8sManager.get_services: Retrieved {len(services)} services")
            return services
        except Exception as e:
            self.logger.error(f"K8sManager.get_services: Error getting services: {e}", extra={
                "error_type": type(e).__name__,
                "namespace": namespace,
            })
            return []

    def get_namespaces(self) -> list[dict]:
        """Get namespaces"""
        self.logger.debug("K8sManager.get_namespaces: Entry")

        try:
            namespaces = self.resource_manager.get_namespaces()
            self.logger.debug(f"K8sManager.get_namespaces: Retrieved {len(namespaces)} namespaces")
            return namespaces
        except Exception as e:
            self.logger.error(f"K8sManager.get_namespaces: Error getting namespaces: {e}", extra={
                "error_type": type(e).__name__,
            })
            return []

    def get_helm_releases(self, namespace: str | None = None) -> list[dict]:
        """Get helm releases"""
        self.logger.debug(f"K8sManager.get_helm_releases: Entry - namespace: {namespace}")

        try:
            releases = self.resource_manager.get_helm_releases(namespace)
            self.logger.debug(f"K8sManager.get_helm_releases: Retrieved {len(releases)} helm releases")
            return releases
        except Exception as e:
            self.logger.error(f"K8sManager.get_helm_releases: Error getting helm releases: {e}", extra={
                "error_type": type(e).__name__,
                "namespace": namespace,
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
                "namespace": namespace,
            })
            return f"Error getting logs for pod {pod_name}: {e!s}"

    def describe_resource(self, resource_type: str, resource_name: str, namespace: str | None = None) -> str:
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
                "namespace": namespace,
            })
            return f"Error describing {resource_type} {resource_name}: {e!s}"
