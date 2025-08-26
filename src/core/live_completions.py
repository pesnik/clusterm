"""Live completion data provider for kubectl and helm commands
Fetches real-time data from the cluster to provide contextual completions
"""

import json
import subprocess
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class CompletionCache:
    """Cache for completion data with TTL"""

    data: dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = 30  # Cache TTL in seconds

    def is_expired(self) -> bool:
        return datetime.now() - self.last_updated > timedelta(seconds=self.ttl_seconds)

    def update(self, new_data: dict[str, Any]):
        self.data = new_data
        self.last_updated = datetime.now()


class LiveCompletionProvider:
    """Provides live completion data from Kubernetes cluster"""

    def __init__(self, k8s_manager=None):
        self.k8s_manager = k8s_manager
        self.cache = CompletionCache()
        self.fetching = False

        # Initialize with basic data
        self._initialize_static_completions()

    def _initialize_static_completions(self):
        """Initialize with static completion data"""
        self.cache.data = {
            "namespaces": ["default", "kube-system", "kube-public", "kube-node-lease"],
            "pods": [],
            "services": [],
            "deployments": [],
            "configmaps": [],
            "secrets": [],
            "nodes": [],
            "helm_releases": [],

            # Static kubectl resources
            "kubectl_resources": [
                "pods", "po", "services", "svc", "deployments", "deploy",
                "configmaps", "cm", "secrets", "namespaces", "ns", "nodes", "no",
                "persistentvolumes", "pv", "persistentvolumeclaims", "pvc",
                "ingresses", "ing", "networkpolicies", "netpol", "serviceaccounts", "sa",
                "roles", "rolebindings", "clusterroles", "clusterrolebindings",
                "events", "endpoints", "ep", "componentstatuses", "cs",
                "daemonsets", "ds", "replicasets", "rs", "statefulsets", "sts",
                "cronjobs", "cj", "jobs", "horizontalpodautoscalers", "hpa",
                "poddisruptionbudgets", "pdb", "volumeattachments", "storageclasses", "sc",
            ],

            # Kubectl API resources by group
            "api_resources": {
                "core": ["pods", "services", "configmaps", "secrets", "namespaces", "nodes"],
                "apps": ["deployments", "daemonsets", "replicasets", "statefulsets"],
                "extensions": ["ingresses", "networkpolicies"],
                "batch": ["jobs", "cronjobs"],
                "autoscaling": ["horizontalpodautoscalers"],
                "policy": ["poddisruptionbudgets"],
                "rbac": ["roles", "rolebindings", "clusterroles", "clusterrolebindings"],
                "storage": ["storageclasses", "volumeattachments", "persistentvolumes", "persistentvolumeclaims"],
            },

            # Common kubectl field selectors
            "field_selectors": [
                "metadata.name=",
                "metadata.namespace=",
                "spec.nodeName=",
                "status.phase=",
                "status.podIP=",
                "spec.restartPolicy=",
                "spec.serviceAccountName=",
            ],

            # Common label selectors
            "label_selectors": [
                "app=", "version=", "component=", "tier=", "release=",
                "app.kubernetes.io/name=", "app.kubernetes.io/instance=",
                "app.kubernetes.io/version=", "app.kubernetes.io/component=",
                "app.kubernetes.io/part-of=", "app.kubernetes.io/managed-by=",
            ],

            # Output formats
            "output_formats": [
                "json", "yaml", "wide", "name", "custom-columns=", "custom-columns-file=",
                "go-template=", "go-template-file=", "jsonpath=", "jsonpath-file=",
            ],

            # Common port ranges and protocols
            "common_ports": [
                "80:8080", "443:8443", "3000:3000", "8080:8080", "5432:5432",
                "3306:3306", "6379:6379", "27017:27017", "9200:9200",
            ],

            "protocols": ["TCP", "UDP", "SCTP"],

            # Common container commands
            "container_commands": ["/bin/bash", "/bin/sh", "/bin/zsh", "bash", "sh"],

            # Helm chart repositories (common ones)
            "helm_repos": ["stable", "bitnami", "nginx", "prometheus-community", "jetstack", "elastic"],

            # Common helm values
            "helm_values": [
                "image.tag=", "image.repository=", "image.pullPolicy=",
                "service.type=", "service.port=", "ingress.enabled=",
                "resources.requests.cpu=", "resources.requests.memory=",
                "resources.limits.cpu=", "resources.limits.memory=",
                "replicaCount=", "nodeSelector=", "tolerations=", "affinity=",
            ],
        }

    def get_completions(self, resource_type: str, context: str | None = None) -> list[str]:
        """Get completions for a specific resource type"""
        self._refresh_if_needed()

        # Map resource type to cache key
        cache_key = self._map_resource_type(resource_type)
        return self.cache.data.get(cache_key, [])

    def get_resource_names(self, resource_type: str, namespace: str | None = None) -> list[str]:
        """Get specific resource names from the cluster"""
        self._refresh_if_needed()

        if resource_type in ["pod", "pods", "po"]:
            return self.cache.data.get("pods", [])
        if resource_type in ["service", "services", "svc"]:
            return self.cache.data.get("services", [])
        if resource_type in ["deployment", "deployments", "deploy"]:
            return self.cache.data.get("deployments", [])
        if resource_type in ["configmap", "configmaps", "cm"]:
            return self.cache.data.get("configmaps", [])
        if resource_type in ["secret", "secrets"]:
            return self.cache.data.get("secrets", [])
        if resource_type in ["namespace", "namespaces", "ns"]:
            return self.cache.data.get("namespaces", [])
        if resource_type in ["node", "nodes", "no"]:
            return self.cache.data.get("nodes", [])
        return []

    def get_helm_releases(self, namespace: str | None = None) -> list[str]:
        """Get Helm release names"""
        self._refresh_if_needed()
        return self.cache.data.get("helm_releases", [])

    def get_container_names(self, pod_name: str, namespace: str | None = None) -> list[str]:
        """Get container names for a specific pod"""
        # This would require more detailed pod information
        # For now, return common container names
        return ["app", "web", "api", "db", "redis", "nginx", "main", "sidecar"]

    def _map_resource_type(self, resource_type: str) -> str:
        """Map resource type to cache key"""
        mapping = {
            "pod": "pods", "po": "pods",
            "service": "services", "svc": "services",
            "deployment": "deployments", "deploy": "deployments",
            "configmap": "configmaps", "cm": "configmaps",
            "secret": "secrets",
            "namespace": "namespaces", "ns": "namespaces",
            "node": "nodes", "no": "nodes",
        }
        return mapping.get(resource_type, resource_type)

    def _refresh_if_needed(self):
        """Refresh completion data if cache is expired"""
        if self.cache.is_expired() and not self.fetching:
            self._fetch_live_data_async()

    def _fetch_live_data_async(self):
        """Fetch live data asynchronously"""
        if self.fetching:
            return

        self.fetching = True
        threading.Thread(target=self._fetch_live_data, daemon=True).start()

    def _fetch_live_data(self):
        """Fetch live data from cluster"""
        try:
            new_data = self.cache.data.copy()

            # Use k8s_manager if available
            if self.k8s_manager:
                self._fetch_via_k8s_manager(new_data)
            else:
                self._fetch_via_kubectl(new_data)

            # Update cache
            self.cache.update(new_data)

        except Exception:
            # On error, extend cache TTL to avoid rapid retries
            self.cache.last_updated = datetime.now() - timedelta(seconds=self.cache.ttl_seconds - 10)
        finally:
            self.fetching = False

    def _fetch_via_k8s_manager(self, data: dict[str, Any]):
        """Fetch data using k8s_manager"""
        try:
            if self.k8s_manager:
                # Fetch namespaces
                namespaces = self.k8s_manager.get_namespaces()
                data["namespaces"] = [ns["metadata"]["name"] for ns in namespaces]

                # Get current namespace
                current_namespace = getattr(self.k8s_manager, "current_namespace", "default")

                # Fetch pods
                pods = self.k8s_manager.get_pods(current_namespace)
                data["pods"] = [pod["metadata"]["name"] for pod in pods]

                # Fetch services
                services = self.k8s_manager.get_services(current_namespace)
                data["services"] = [svc["metadata"]["name"] for svc in services]

                # Fetch deployments
                deployments = self.k8s_manager.get_deployments()
                data["deployments"] = [dep["metadata"]["name"] for dep in deployments]

                # Fetch helm releases
                try:
                    releases = self.k8s_manager.get_helm_releases()
                    data["helm_releases"] = [rel.get("name", "") for rel in releases]
                except:
                    pass

        except Exception:
            # If k8s_manager fails, fall back to kubectl
            self._fetch_via_kubectl(data)

    def _fetch_via_kubectl(self, data: dict[str, Any]):
        """Fetch data using direct kubectl commands"""
        try:
            # Fetch namespaces
            result = subprocess.run(["kubectl", "get", "namespaces", "-o", "json"],
                                  check=False, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                ns_data = json.loads(result.stdout)
                data["namespaces"] = [item["metadata"]["name"] for item in ns_data.get("items", [])]

            # Fetch pods (in default namespace for now)
            result = subprocess.run(["kubectl", "get", "pods", "-o", "json"],
                                  check=False, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                pods_data = json.loads(result.stdout)
                data["pods"] = [item["metadata"]["name"] for item in pods_data.get("items", [])]

            # Fetch services
            result = subprocess.run(["kubectl", "get", "services", "-o", "json"],
                                  check=False, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                svc_data = json.loads(result.stdout)
                data["services"] = [item["metadata"]["name"] for item in svc_data.get("items", [])]

            # Fetch deployments
            result = subprocess.run(["kubectl", "get", "deployments", "-o", "json"],
                                  check=False, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                deploy_data = json.loads(result.stdout)
                data["deployments"] = [item["metadata"]["name"] for item in deploy_data.get("items", [])]

            # Fetch helm releases
            try:
                result = subprocess.run(["helm", "list", "-o", "json"],
                                      check=False, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    releases_data = json.loads(result.stdout)
                    data["helm_releases"] = [item.get("name", "") for item in releases_data]
            except:
                pass

            # Fetch nodes
            result = subprocess.run(["kubectl", "get", "nodes", "-o", "json"],
                                  check=False, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                nodes_data = json.loads(result.stdout)
                data["nodes"] = [item["metadata"]["name"] for item in nodes_data.get("items", [])]

        except Exception:
            # Graceful degradation - keep existing cached data
            pass

    def get_kubectl_resources(self) -> list[str]:
        """Get all available kubectl resource types"""
        return self.cache.data.get("kubectl_resources", [])

    def get_output_formats(self) -> list[str]:
        """Get available output formats"""
        return self.cache.data.get("output_formats", [])

    def get_field_selectors(self) -> list[str]:
        """Get common field selectors"""
        return self.cache.data.get("field_selectors", [])

    def get_label_selectors(self) -> list[str]:
        """Get common label selectors"""
        return self.cache.data.get("label_selectors", [])

    def force_refresh(self):
        """Force a refresh of completion data"""
        self.cache.last_updated = datetime.now() - timedelta(seconds=self.cache.ttl_seconds + 1)
        self._refresh_if_needed()

    def get_context_info(self) -> dict[str, str]:
        """Get current context information"""
        try:
            if self.k8s_manager and hasattr(self.k8s_manager, "cluster_manager"):
                current_cluster = self.k8s_manager.cluster_manager.get_current_cluster()
                cluster_name = current_cluster["name"] if current_cluster else "unknown"
                namespace = getattr(self.k8s_manager, "current_namespace", "default")

                return {
                    "cluster": cluster_name,
                    "namespace": namespace,
                    "context": f"{cluster_name}:{namespace}",
                }
        except:
            pass

        return {"cluster": "unknown", "namespace": "default", "context": "unknown:default"}
