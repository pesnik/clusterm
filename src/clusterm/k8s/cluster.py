"""Kubernetes cluster management
"""

import os
import subprocess
from pathlib import Path

from ..core.events import EventBus, EventType
from ..core.logger import Logger


class ClusterManager:
    """Manage multiple Kubernetes clusters"""

    def __init__(self, clusters_path: Path, event_bus: EventBus, logger: Logger):
        self.clusters_path = clusters_path
        self.event_bus = event_bus
        self.logger = logger
        self.clusters = {}
        self.current_cluster = None
        self.discover_clusters()

    def discover_clusters(self):
        """Discover available clusters from the clusters directory"""
        if not self.clusters_path.exists():
            self.logger.warning(f"Clusters path does not exist: {self.clusters_path}")
            return

        discovered = 0
        for cluster_dir in self.clusters_path.iterdir():
            if cluster_dir.is_dir():
                kubeconfig_files = (
                    list(cluster_dir.glob("kubeconfig")) +
                    list(cluster_dir.glob("*kubeconfig*.yaml")) +
                    list(cluster_dir.glob("*kubeconfig*.yml")) +
                    list(cluster_dir.glob("config"))
                )

                if kubeconfig_files:
                    self.clusters[cluster_dir.name] = {
                        "name": cluster_dir.name,
                        "path": cluster_dir,
                        "kubeconfig": kubeconfig_files[0],
                        "status": "Unknown",
                        "last_tested": None,
                    }
                    discovered += 1

        self.logger.info(f"Discovered {discovered} clusters")

    def get_available_clusters(self) -> list[dict[str, str]]:
        """Get list of available clusters"""
        return list(self.clusters.values())

    def set_current_cluster(self, cluster_name: str) -> bool:
        """Set the current active cluster"""
        if cluster_name in self.clusters:
            old_cluster = self.current_cluster
            self.current_cluster = cluster_name

            self.event_bus.emit_sync(
                EventType.CLUSTER_CHANGED,
                "cluster_manager",
                old_cluster=old_cluster,
                new_cluster=cluster_name,
            )

            self.logger.info(f"Switched to cluster: {cluster_name}")
            return True

        self.logger.error(f"Cluster not found: {cluster_name}")
        return False

    def get_current_cluster(self) -> dict | None:
        """Get current cluster info"""
        if self.current_cluster and self.current_cluster in self.clusters:
            return self.clusters[self.current_cluster]
        return None

    def get_current_kubeconfig(self) -> Path | None:
        """Get current cluster's kubeconfig path"""
        cluster = self.get_current_cluster()
        if cluster:
            return cluster["kubeconfig"]
        return None

    def test_cluster_connection(self, cluster_name: str) -> tuple[bool, str]:
        """Test connection to a specific cluster"""
        if cluster_name not in self.clusters:
            return False, f"Cluster {cluster_name} not found"

        cluster = self.clusters[cluster_name]
        kubeconfig = cluster["kubeconfig"]

        try:
            # Use kubectl from the expected location
            kubectl_path = self.clusters_path.parent / "tools" / "kubectl"
            if not kubectl_path.exists():
                return False, f"kubectl not found at {kubectl_path}"

            cmd = [str(kubectl_path), "cluster-info"]
            env = os.environ.copy()
            env["KUBECONFIG"] = str(kubeconfig)

            result = subprocess.run(
                cmd,
                check=False, capture_output=True,
                text=True,
                env=env,
                timeout=10,
            )

            success = result.returncode == 0
            status = "Connected" if success else "Failed"
            message = f"Cluster {cluster_name}: {status}"

            # Update cluster status
            self.clusters[cluster_name]["status"] = status
            self.clusters[cluster_name]["last_tested"] = __import__("time").time()

            if success:
                self.logger.info(message)
            else:
                self.logger.error(f"{message} - {result.stderr}")
                message = f"{message} - {result.stderr}"

            return success, message

        except subprocess.TimeoutExpired:
            error_msg = f"Connection test timed out for {cluster_name}"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Connection test failed for {cluster_name}: {e!s}"
            self.logger.error(error_msg)
            return False, error_msg
