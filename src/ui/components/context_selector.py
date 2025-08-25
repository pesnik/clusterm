"""
Context Selector Component
Provides cluster and namespace selection dropdowns for improved UX
"""

from typing import List, Dict, Any, Optional
from textual.containers import Container, Horizontal
from textual.widgets import Static, Select
from textual.widget import Widget
from textual.message import Message
from textual import on


class ContextSelector(Widget):
    """
    Context selector widget with cluster and namespace dropdowns
    Allows users to switch clusters and namespaces independently
    """
    
    class ContextChanged(Message):
        """Message sent when context (cluster or namespace) changes"""
        def __init__(self, cluster: str, namespace: str, change_type: str):
            self.cluster = cluster
            self.namespace = namespace
            self.change_type = change_type  # 'cluster' or 'namespace'
            super().__init__()
    
    def __init__(self, k8s_manager, **kwargs):
        super().__init__(**kwargs)
        self.k8s_manager = k8s_manager
        self.current_cluster = "default"
        self.current_namespace = "default"
        self._cluster_options = []
        self._namespace_options = []
        
        # Initialize current context
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
            # Fallback to defaults if context retrieval fails
            self.current_cluster = "default"
            self.current_namespace = "default"
    
    def compose(self):
        """Compose the context selector widget"""
        with Container(classes="context-selector"):
            yield Static("🌐 Context", classes="context-title")
            
            with Horizontal(classes="context-controls"):
                with Container(classes="cluster-selector-container"):
                    yield Static("Cluster:", classes="selector-label")
                    yield Select(
                        self._get_cluster_options(),
                        value=self.current_cluster,
                        id="cluster-select",
                        classes="cluster-select"
                    )
                
                with Container(classes="namespace-selector-container"):
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
                self._cluster_options = [
                    (cluster.get('name', 'Unknown'), cluster.get('name', 'Unknown'))
                    for cluster in clusters
                ]
                
                if not self._cluster_options:
                    self._cluster_options = [("default", "default")]
            else:
                self._cluster_options = [("default", "default")]
        except Exception:
            self._cluster_options = [("default", "default")]
        
        return self._cluster_options
    
    def _get_namespace_options(self) -> List[tuple]:
        """Get available namespace options for current cluster"""
        try:
            namespaces = self.k8s_manager.get_namespaces()
            self._namespace_options = [
                (ns['metadata']['name'], ns['metadata']['name'])
                for ns in namespaces
            ]
            
            if not self._namespace_options:
                self._namespace_options = [("default", "default")]
        except Exception:
            self._namespace_options = [("default", "default")]
        
        return self._namespace_options
    
    @on(Select.Changed, "#cluster-select")
    def cluster_changed(self, event: Select.Changed):
        """Handle cluster selection change"""
        if event.value is None:
            return
        
        new_cluster = str(event.value)
        if new_cluster != self.current_cluster:
            old_cluster = self.current_cluster
            self.current_cluster = new_cluster
            
            # Switch cluster in k8s_manager
            try:
                if hasattr(self.k8s_manager, 'cluster_manager'):
                    success = self.k8s_manager.cluster_manager.set_current_cluster(new_cluster)
                    if success:
                        # Update namespace options for new cluster
                        self._refresh_namespace_options()
                        
                        # Send context change message
                        self.post_message(self.ContextChanged(
                            new_cluster, self.current_namespace, "cluster"
                        ))
                    else:
                        # Revert on failure
                        self.current_cluster = old_cluster
                        cluster_select = self.query_one("#cluster-select", Select)
                        cluster_select.value = old_cluster
            except Exception as e:
                # Revert on error
                self.current_cluster = old_cluster
                cluster_select = self.query_one("#cluster-select", Select)
                cluster_select.value = old_cluster
    
    @on(Select.Changed, "#namespace-select")
    def namespace_changed(self, event: Select.Changed):
        """Handle namespace selection change"""
        if event.value is None:
            return
        
        new_namespace = str(event.value)
        if new_namespace != self.current_namespace:
            self.current_namespace = new_namespace
            
            # Update namespace in k8s_manager
            try:
                if hasattr(self.k8s_manager, 'current_namespace'):
                    setattr(self.k8s_manager, 'current_namespace', new_namespace)
                
                # Send context change message
                self.post_message(self.ContextChanged(
                    self.current_cluster, new_namespace, "namespace"
                ))
            except Exception:
                # Namespace switching is less critical, continue anyway
                pass
    
    def _refresh_namespace_options(self):
        """Refresh namespace options after cluster change"""
        try:
            namespace_select = self.query_one("#namespace-select", Select)
            new_options = self._get_namespace_options()
            
            # Update the select options
            namespace_select.set_options(new_options)
            
            # Reset to default namespace for new cluster
            self.current_namespace = "default" if ("default", "default") in new_options else new_options[0][1]
            namespace_select.value = self.current_namespace
            
        except Exception:
            # If refresh fails, keep current state
            pass
    
    def refresh_context(self):
        """Refresh context and update selectors"""
        try:
            # Update cluster options
            cluster_select = self.query_one("#cluster-select", Select)
            cluster_options = self._get_cluster_options()
            cluster_select.set_options(cluster_options)
            
            # Update namespace options
            self._refresh_namespace_options()
            
            # Update current context
            self._update_current_context()
            
        except Exception:
            # If refresh fails, keep current state
            pass
    
    def get_current_context(self) -> Dict[str, str]:
        """Get current cluster and namespace context"""
        return {
            "cluster": self.current_cluster,
            "namespace": self.current_namespace
        }
    
    def set_context(self, cluster: Optional[str] = None, namespace: Optional[str] = None):
        """Programmatically set context"""
        try:
            if cluster and cluster != self.current_cluster:
                cluster_select = self.query_one("#cluster-select", Select)
                cluster_select.value = cluster
            
            if namespace and namespace != self.current_namespace:
                namespace_select = self.query_one("#namespace-select", Select)
                namespace_select.value = namespace
                
        except Exception:
            # If setting fails, keep current state
            pass