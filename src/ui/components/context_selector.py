"""
Context Selector Component with Working Dropdowns
Allows independent cluster and namespace switching
"""

from typing import List, Dict, Any
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Select
from textual.message import Message
from textual import on


class ContextSelector(Vertical):
    """Context selector with functional cluster and namespace dropdowns"""
    
    class ContextChanged(Message):
        """Message sent when context changes"""
        def __init__(self, cluster: str, namespace: str, change_type: str):
            self.cluster = cluster
            self.namespace = namespace
            self.change_type = change_type
            super().__init__()
    
    def __init__(self, k8s_manager, **kwargs):
        super().__init__(**kwargs)
        self.k8s_manager = k8s_manager
        self.current_cluster = "default"
        self.current_namespace = "default"
        
        # Get initial context
        self._update_current_context()
    
    def _update_current_context(self):
        """Update current context from k8s_manager"""
        try:
            if hasattr(self.k8s_manager, 'cluster_manager'):
                current_cluster = self.k8s_manager.cluster_manager.get_current_cluster()
                if current_cluster:
                    self.current_cluster = current_cluster.get('name', 'default')
            
            if hasattr(self.k8s_manager, 'current_namespace'):
                self.current_namespace = getattr(self.k8s_manager, 'current_namespace', 'default')
        except Exception:
            self.current_cluster = "default"
            self.current_namespace = "default"
    
    def compose(self):
        """Compose the context selector with dropdowns"""
        with Horizontal(classes="context-selectors"):
            # Cluster selector
            with Vertical(classes="selector-group"):
                yield Static("Cluster:", classes="selector-label")
                yield Select(
                    self._get_cluster_options(),
                    value=self.current_cluster,
                    id="cluster-select",
                    classes="cluster-select"
                )
            
            # Namespace selector  
            with Vertical(classes="selector-group"):
                yield Static("Namespace:", classes="selector-label")
                yield Select(
                    self._get_namespace_options(),
                    value=self.current_namespace,
                    id="namespace-select", 
                    classes="namespace-select"
                )
    
    def _get_cluster_options(self) -> List[tuple]:
        """Get available cluster options"""
        try:
            if hasattr(self.k8s_manager, 'cluster_manager'):
                clusters = self.k8s_manager.cluster_manager.get_available_clusters()
                if clusters:
                    return [(cluster.get('name', 'Unknown'), cluster.get('name', 'Unknown')) for cluster in clusters]
            return [("default", "default")]
        except Exception:
            return [("default", "default")]
    
    def _get_namespace_options(self) -> List[tuple]:
        """Get available namespace options"""
        try:
            namespaces = self.k8s_manager.get_namespaces()
            if namespaces:
                return [(ns['metadata']['name'], ns['metadata']['name']) for ns in namespaces]
            return [("default", "default")]
        except Exception:
            return [("default", "default")]
    
    @on(Select.Changed, "#cluster-select")
    def cluster_changed(self, event: Select.Changed):
        """Handle cluster selection change"""
        if event.value and str(event.value) != self.current_cluster:
            old_cluster = self.current_cluster
            new_cluster = str(event.value)
            
            try:
                # Actually switch the cluster
                if hasattr(self.k8s_manager, 'cluster_manager'):
                    success = self.k8s_manager.cluster_manager.set_current_cluster(new_cluster)
                    if success:
                        self.current_cluster = new_cluster
                        
                        # Refresh namespace options for new cluster
                        self._refresh_namespace_selector()
                        
                        # Notify parent about cluster change
                        self.post_message(self.ContextChanged(
                            self.current_cluster, self.current_namespace, "cluster"
                        ))
                    else:
                        # Revert selector on failure
                        cluster_select = self.query_one("#cluster-select", Select)
                        cluster_select.value = old_cluster
            except Exception:
                # Revert on error
                cluster_select = self.query_one("#cluster-select", Select)
                cluster_select.value = old_cluster
    
    @on(Select.Changed, "#namespace-select")
    def namespace_changed(self, event: Select.Changed):
        """Handle namespace selection change"""
        if event.value and str(event.value) != self.current_namespace:
            new_namespace = str(event.value)
            
            # Update current namespace
            self.current_namespace = new_namespace
            if hasattr(self.k8s_manager, 'current_namespace'):
                setattr(self.k8s_manager, 'current_namespace', new_namespace)
            
            # Notify parent about namespace change
            self.post_message(self.ContextChanged(
                self.current_cluster, new_namespace, "namespace"
            ))
    
    def _refresh_namespace_selector(self):
        """Refresh namespace options after cluster change"""
        try:
            namespace_select = self.query_one("#namespace-select", Select)
            new_options = self._get_namespace_options()
            namespace_select.set_options(new_options)
            
            # Reset to default namespace for new cluster
            if ("default", "default") in new_options:
                self.current_namespace = "default"
                namespace_select.value = "default"
            elif new_options:
                self.current_namespace = new_options[0][1]
                namespace_select.value = new_options[0][1]
                
        except Exception:
            pass
    
    def get_current_context(self) -> Dict[str, str]:
        """Get current context"""
        return {
            "cluster": self.current_cluster,
            "namespace": self.current_namespace
        }
    
    def refresh_selectors(self):
        """Refresh selector values to match current context"""
        try:
            cluster_select = self.query_one("#cluster-select", Select)
            cluster_select.value = self.current_cluster
            
            namespace_select = self.query_one("#namespace-select", Select)
            namespace_select.value = self.current_namespace
        except Exception:
            pass