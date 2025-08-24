"""
Table components for displaying Kubernetes resources
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Callable
from textual.widgets import DataTable
from textual.reactive import reactive


class ResourceTable(DataTable):
    """Enhanced data table for Kubernetes resources"""
    
    resource_type = reactive("")
    selected_resource = reactive(None)
    
    def __init__(self, 
                 resource_type: str, 
                 columns: List[str], 
                 on_selection: Optional[Callable] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.resource_type = resource_type
        self.columns = columns
        self.on_selection_callback = on_selection
    
    def on_mount(self):
        """Setup table columns when mounted"""
        self.add_columns(*self.columns)
    
    def on_data_table_row_selected(self, event):
        """Handle row selection"""
        if event.row_index is not None:
            row_data = self.get_row_at(event.row_index)
            self.selected_resource = {
                "type": self.resource_type,
                "data": row_data,
                "index": event.row_index
            }
            
            if self.on_selection_callback:
                self.on_selection_callback(self.selected_resource)
    
    def update_data(self, resources: List[Dict[str, Any]]):
        """Update table with new resource data"""
        self.clear()
        
        for resource in resources:
            row_data = self._extract_row_data(resource)
            if row_data:
                self.add_row(*row_data)
    
    def _extract_row_data(self, resource: Dict[str, Any]) -> Optional[List[str]]:
        """Extract row data from resource - override in subclasses"""
        return None
    
    def _calculate_age(self, timestamp_str: str) -> str:
        """Calculate human-readable age from timestamp"""
        try:
            created_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            age_delta = datetime.now(timezone.utc) - created_time
            
            if age_delta.days > 0:
                return f"{age_delta.days}d"
            elif age_delta.seconds > 3600:
                return f"{age_delta.seconds // 3600}h"
            elif age_delta.seconds > 60:
                return f"{age_delta.seconds // 60}m"
            else:
                return f"{age_delta.seconds}s"
        except Exception:
            return "Unknown"


class DeploymentTable(ResourceTable):
    """Table for displaying deployments"""
    
    def __init__(self, **kwargs):
        columns = ["Name", "Status", "Replicas", "Age", "Namespace"]
        super().__init__("deployment", columns, **kwargs)
    
    def _extract_row_data(self, deployment: Dict[str, Any]) -> List[str]:
        """Extract deployment data for table row"""
        name = deployment["metadata"]["name"]
        namespace = deployment["metadata"]["namespace"]
        status = deployment["status"]
        
        # Calculate replicas
        ready_replicas = status.get('readyReplicas', 0)
        total_replicas = status.get('replicas', 0)
        replicas_str = f"{ready_replicas}/{total_replicas}"
        
        # Calculate status
        if ready_replicas == total_replicas and total_replicas > 0:
            status_text = "Running"
        elif ready_replicas > 0:
            status_text = "Partial"
        else:
            status_text = "Failed"
        
        # Calculate age
        age = self._calculate_age(deployment["metadata"]["creationTimestamp"])
        
        return [name, status_text, replicas_str, age, namespace]


class PodTable(ResourceTable):
    """Table for displaying pods"""
    
    def __init__(self, **kwargs):
        columns = ["Name", "Status", "Ready", "Restarts", "Age", "Node"]
        super().__init__("pod", columns, **kwargs)
    
    def _extract_row_data(self, pod: Dict[str, Any]) -> List[str]:
        """Extract pod data for table row"""
        name = pod["metadata"]["name"]
        phase = pod["status"]["phase"]
        
        # Calculate ready containers
        container_statuses = pod["status"].get("containerStatuses", [])
        ready_count = sum(1 for c in container_statuses if c.get("ready", False))
        total_count = len(container_statuses)
        ready = f"{ready_count}/{total_count}"
        
        # Calculate restarts
        restarts = sum(c.get("restartCount", 0) for c in container_statuses)
        
        # Age and node
        age = self._calculate_age(pod["metadata"]["creationTimestamp"])
        node = pod["spec"].get("nodeName", "Unknown")
        
        return [name, phase, ready, str(restarts), age, node]


class ServiceTable(ResourceTable):
    """Table for displaying services"""
    
    def __init__(self, **kwargs):
        columns = ["Name", "Type", "Cluster-IP", "External-IP", "Port(s)", "Age"]
        super().__init__("service", columns, **kwargs)
    
    def _extract_row_data(self, service: Dict[str, Any]) -> List[str]:
        """Extract service data for table row"""
        name = service["metadata"]["name"]
        service_type = service["spec"]["type"]
        cluster_ip = service["spec"].get("clusterIP", "None")
        
        # External IP
        external_ips = service["spec"].get("externalIPs", [])
        external_ip = external_ips[0] if external_ips else "<none>"
        
        # Ports
        ports = service["spec"].get("ports", [])
        port_strs = []
        for port in ports:
            port_str = str(port["port"])
            if "targetPort" in port:
                port_str += f":{port['targetPort']}"
            if "protocol" in port and port["protocol"] != "TCP":
                port_str += f"/{port['protocol']}"
            port_strs.append(port_str)
        ports_display = ",".join(port_strs) if port_strs else "<none>"
        
        # Age
        age = self._calculate_age(service["metadata"]["creationTimestamp"])
        
        return [name, service_type, cluster_ip, external_ip, ports_display, age]


class HelmReleaseTable(ResourceTable):
    """Table for displaying Helm releases"""
    
    def __init__(self, **kwargs):
        columns = ["Name", "Namespace", "Revision", "Updated", "Status", "Chart"]
        super().__init__("helm_release", columns, **kwargs)
    
    def _extract_row_data(self, release: Dict[str, Any]) -> List[str]:
        """Extract helm release data for table row"""
        name = release.get("name", "Unknown")
        namespace = release.get("namespace", "Unknown")
        revision = str(release.get("revision", "Unknown"))
        updated = release.get("updated", "Unknown")
        status = release.get("status", "Unknown")
        chart = release.get("chart", "Unknown")
        
        return [name, namespace, revision, updated, status, chart]


class NamespaceTable(ResourceTable):
    """Table for displaying namespaces"""
    
    def __init__(self, **kwargs):
        columns = ["Name", "Status", "Age"]
        super().__init__("namespace", columns, **kwargs)
    
    def _extract_row_data(self, namespace: Dict[str, Any]) -> List[str]:
        """Extract namespace data for table row"""
        name = namespace["metadata"]["name"]
        phase = namespace["status"]["phase"]
        age = self._calculate_age(namespace["metadata"]["creationTimestamp"])
        
        return [name, phase, age]