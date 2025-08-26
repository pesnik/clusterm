"""Context Selector Component with Working Dropdowns
Allows independent cluster and namespace switching
"""

from textual import on
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Select, Static


class ContextSelector(Vertical):
    """Context selector with functional cluster and namespace dropdowns"""

    class ContextChanged(Message):
        """Message sent when context changes"""

        def __init__(self, cluster: str, namespace: str, change_type: str):
            self.cluster = cluster
            self.namespace = namespace
            self.change_type = change_type
            super().__init__()

    def __init__(self, k8s_manager, logger=None, **kwargs):
        super().__init__(**kwargs)
        self.k8s_manager = k8s_manager
        self.logger = logger
        self.current_cluster = "default"
        self.current_namespace = "default"

        if self.logger:
            self.logger.debug("ContextSelector.__init__: Entry - Initializing ContextSelector")
            self.logger.debug(f"ContextSelector.__init__: Initial state - cluster: {self.current_cluster}, namespace: {self.current_namespace}")

        # Get initial context
        self._update_current_context()

        if self.logger:
            self.logger.info(f"ContextSelector.__init__: Initialization complete - cluster: {self.current_cluster}, namespace: {self.current_namespace}")

    def _update_current_context(self):
        """Update current context from k8s_manager"""
        if self.logger:
            self.logger.debug("ContextSelector._update_current_context: Entry")

        try:
            old_cluster = self.current_cluster
            old_namespace = self.current_namespace

            if hasattr(self.k8s_manager, "cluster_manager"):
                if self.logger:
                    self.logger.debug("ContextSelector._update_current_context: Getting current cluster from cluster_manager")

                current_cluster = self.k8s_manager.cluster_manager.get_current_cluster()
                if current_cluster:
                    self.current_cluster = current_cluster.get("name", "default")
                    if self.logger:
                        self.logger.debug(f"ContextSelector._update_current_context: Updated cluster to: {self.current_cluster}")

            if hasattr(self.k8s_manager, "current_namespace"):
                if self.logger:
                    self.logger.debug("ContextSelector._update_current_context: Getting current namespace from k8s_manager")

                self.current_namespace = getattr(self.k8s_manager, "current_namespace", "default")
                if self.logger:
                    self.logger.debug(f"ContextSelector._update_current_context: Updated namespace to: {self.current_namespace}")

            if self.logger and (old_cluster != self.current_cluster or old_namespace != self.current_namespace):
                self.logger.info(f"ContextSelector._update_current_context: Context updated - cluster: {old_cluster} -> {self.current_cluster}, namespace: {old_namespace} -> {self.current_namespace}")

        except Exception as e:
            if self.logger:
                self.logger.error(f"ContextSelector._update_current_context: Error updating context: {e}", extra={
                    "error_type": type(e).__name__,
                })
            self.current_cluster = "default"
            self.current_namespace = "default"

    def compose(self):
        """Compose the context selector with dropdowns"""
        if self.logger:
            self.logger.debug("ContextSelector.compose: Entry - Composing context selector UI")

        with Horizontal(classes="context-selectors"):
            # Cluster selector
            with Vertical(classes="selector-group"):
                if self.logger:
                    self.logger.debug("ContextSelector.compose: Creating cluster selector")

                yield Static("Cluster:", classes="selector-label")
                cluster_options = self._get_cluster_options()

                if self.logger:
                    self.logger.debug(f"ContextSelector.compose: Cluster options: {cluster_options}")

                yield Select(
                    cluster_options,
                    value=self.current_cluster,
                    id="cluster-select",
                    classes="cluster-select",
                )

            # Namespace selector
            with Vertical(classes="selector-group"):
                if self.logger:
                    self.logger.debug("ContextSelector.compose: Creating namespace selector")

                yield Static("Namespace:", classes="selector-label")
                namespace_options = self._get_namespace_options()

                if self.logger:
                    self.logger.debug(f"ContextSelector.compose: Namespace options: {namespace_options}")

                yield Select(
                    namespace_options,
                    value=self.current_namespace,
                    id="namespace-select",
                    classes="namespace-select",
                )

        if self.logger:
            self.logger.info("ContextSelector.compose: UI composition completed successfully")

    def _get_cluster_options(self) -> list[tuple]:
        """Get available cluster options"""
        if self.logger:
            self.logger.debug("ContextSelector._get_cluster_options: Entry")

        try:
            if hasattr(self.k8s_manager, "cluster_manager"):
                if self.logger:
                    self.logger.debug("ContextSelector._get_cluster_options: Getting clusters from cluster_manager")

                clusters = self.k8s_manager.cluster_manager.get_available_clusters()
                if clusters:
                    options = [(cluster.get("name", "Unknown"), cluster.get("name", "Unknown")) for cluster in clusters]
                    if self.logger:
                        self.logger.debug(f"ContextSelector._get_cluster_options: Found {len(clusters)} clusters: {[c[0] for c in options]}")
                    return options

            if self.logger:
                self.logger.debug("ContextSelector._get_cluster_options: No clusters found, using default")
            return [("default", "default")]

        except Exception as e:
            if self.logger:
                self.logger.error(f"ContextSelector._get_cluster_options: Error getting clusters: {e}", extra={
                    "error_type": type(e).__name__,
                })
            return [("default", "default")]

    def _get_namespace_options(self) -> list[tuple]:
        """Get available namespace options"""
        if self.logger:
            self.logger.debug("ContextSelector._get_namespace_options: Entry")

        try:
            if self.logger:
                self.logger.debug("ContextSelector._get_namespace_options: Getting namespaces from k8s_manager")

            namespaces = self.k8s_manager.get_namespaces()
            if namespaces:
                options = [(ns["metadata"]["name"], ns["metadata"]["name"]) for ns in namespaces]
                if self.logger:
                    self.logger.debug(f"ContextSelector._get_namespace_options: Found {len(namespaces)} namespaces: {[ns[0] for ns in options]}")
                return options

            if self.logger:
                self.logger.debug("ContextSelector._get_namespace_options: No namespaces found, using default")
            return [("default", "default")]

        except Exception as e:
            if self.logger:
                self.logger.error(f"ContextSelector._get_namespace_options: Error getting namespaces: {e}", extra={
                    "error_type": type(e).__name__,
                })
            return [("default", "default")]

    @on(Select.Changed, "#cluster-select")
    def cluster_changed(self, event: Select.Changed):
        """Handle cluster selection change"""
        if self.logger:
            self.logger.debug(f"ContextSelector.cluster_changed: Entry - Event value: {event.value}, current: {self.current_cluster}")

        if event.value and str(event.value) != self.current_cluster:
            old_cluster = self.current_cluster
            new_cluster = str(event.value)

            if self.logger:
                self.logger.info(f"ContextSelector.cluster_changed: Cluster change requested: {old_cluster} -> {new_cluster}")

            try:
                # Actually switch the cluster
                if hasattr(self.k8s_manager, "cluster_manager"):
                    if self.logger:
                        self.logger.debug("ContextSelector.cluster_changed: Calling set_current_cluster on cluster_manager")

                    success = self.k8s_manager.cluster_manager.set_current_cluster(new_cluster)

                    if success:
                        self.current_cluster = new_cluster
                        if self.logger:
                            self.logger.info(f"ContextSelector.cluster_changed: Successfully switched to cluster: {new_cluster}")

                        # Refresh namespace options for new cluster
                        if self.logger:
                            self.logger.debug("ContextSelector.cluster_changed: Refreshing namespace selector")
                        self._refresh_namespace_selector()

                        # Notify parent about cluster change
                        if self.logger:
                            self.logger.debug("ContextSelector.cluster_changed: Posting ContextChanged message")
                        self.post_message(self.ContextChanged(
                            self.current_cluster, self.current_namespace, "cluster",
                        ))

                        if self.logger:
                            self.logger.info(f"ContextSelector.cluster_changed: Cluster change complete: {new_cluster}")
                    else:
                        if self.logger:
                            self.logger.error(f"ContextSelector.cluster_changed: Failed to switch to cluster: {new_cluster}")
                        # Revert selector on failure
                        cluster_select = self.query_one("#cluster-select", Select)
                        cluster_select.value = old_cluster

                elif self.logger:
                    self.logger.error("ContextSelector.cluster_changed: No cluster_manager available")

            except Exception as e:
                if self.logger:
                    self.logger.error(f"ContextSelector.cluster_changed: Error changing cluster: {e}", extra={
                        "error_type": type(e).__name__,
                        "old_cluster": old_cluster,
                        "new_cluster": new_cluster,
                    })
                # Revert on error
                try:
                    cluster_select = self.query_one("#cluster-select", Select)
                    cluster_select.value = old_cluster
                except:
                    pass
        elif self.logger:
            self.logger.debug(f"ContextSelector.cluster_changed: No cluster change needed - value: {event.value}, current: {self.current_cluster}")

    @on(Select.Changed, "#namespace-select")
    def namespace_changed(self, event: Select.Changed):
        """Handle namespace selection change"""
        if self.logger:
            self.logger.debug(f"ContextSelector.namespace_changed: Entry - Event value: {event.value}, current: {self.current_namespace}")

        if event.value and str(event.value) != self.current_namespace:
            old_namespace = self.current_namespace
            new_namespace = str(event.value)

            if self.logger:
                self.logger.info(f"ContextSelector.namespace_changed: Namespace change requested: {old_namespace} -> {new_namespace}")

            try:
                # Update current namespace
                self.current_namespace = new_namespace
                if hasattr(self.k8s_manager, "current_namespace"):
                    if self.logger:
                        self.logger.debug("ContextSelector.namespace_changed: Updating k8s_manager current_namespace")
                    self.k8s_manager.current_namespace = new_namespace

                # Notify parent about namespace change
                if self.logger:
                    self.logger.debug("ContextSelector.namespace_changed: Posting ContextChanged message")
                self.post_message(self.ContextChanged(
                    self.current_cluster, new_namespace, "namespace",
                ))

                if self.logger:
                    self.logger.info(f"ContextSelector.namespace_changed: Namespace change complete: {new_namespace}")

            except Exception as e:
                if self.logger:
                    self.logger.error(f"ContextSelector.namespace_changed: Error changing namespace: {e}", extra={
                        "error_type": type(e).__name__,
                        "old_namespace": old_namespace,
                        "new_namespace": new_namespace,
                    })
        elif self.logger:
            self.logger.debug(f"ContextSelector.namespace_changed: No namespace change needed - value: {event.value}, current: {self.current_namespace}")

    def _refresh_namespace_selector(self):
        """Refresh namespace options after cluster change"""
        if self.logger:
            self.logger.debug("ContextSelector._refresh_namespace_selector: Entry")

        try:
            namespace_select = self.query_one("#namespace-select", Select)
            new_options = self._get_namespace_options()

            if self.logger:
                self.logger.debug(f"ContextSelector._refresh_namespace_selector: Setting {len(new_options)} namespace options")

            namespace_select.set_options(new_options)

            old_namespace = self.current_namespace

            # Reset to default namespace for new cluster
            if ("default", "default") in new_options:
                self.current_namespace = "default"
                namespace_select.value = "default"
                if self.logger:
                    self.logger.debug("ContextSelector._refresh_namespace_selector: Set to default namespace")
            elif new_options:
                self.current_namespace = new_options[0][1]
                namespace_select.value = new_options[0][1]
                if self.logger:
                    self.logger.debug(f"ContextSelector._refresh_namespace_selector: Set to first available namespace: {self.current_namespace}")

            if self.logger and old_namespace != self.current_namespace:
                self.logger.info(f"ContextSelector._refresh_namespace_selector: Namespace updated after cluster change: {old_namespace} -> {self.current_namespace}")

        except Exception as e:
            if self.logger:
                self.logger.error(f"ContextSelector._refresh_namespace_selector: Error refreshing namespace selector: {e}", extra={
                    "error_type": type(e).__name__,
                })

    def get_current_context(self) -> dict[str, str]:
        """Get current context"""
        if self.logger:
            self.logger.debug(f"ContextSelector.get_current_context: Returning context - cluster: {self.current_cluster}, namespace: {self.current_namespace}")

        return {
            "cluster": self.current_cluster,
            "namespace": self.current_namespace,
        }

    def refresh_selectors(self):
        """Refresh selector values to match current context"""
        if self.logger:
            self.logger.debug(f"ContextSelector.refresh_selectors: Entry - Refreshing selectors to cluster: {self.current_cluster}, namespace: {self.current_namespace}")

        try:
            cluster_select = self.query_one("#cluster-select", Select)
            cluster_select.value = self.current_cluster

            if self.logger:
                self.logger.debug(f"ContextSelector.refresh_selectors: Updated cluster selector to: {self.current_cluster}")

            namespace_select = self.query_one("#namespace-select", Select)
            namespace_select.value = self.current_namespace

            if self.logger:
                self.logger.debug(f"ContextSelector.refresh_selectors: Updated namespace selector to: {self.current_namespace}")
                self.logger.info("ContextSelector.refresh_selectors: Selectors refreshed successfully")

        except Exception as e:
            if self.logger:
                self.logger.error(f"ContextSelector.refresh_selectors: Error refreshing selectors: {e}", extra={
                    "error_type": type(e).__name__,
                    "current_cluster": self.current_cluster,
                    "current_namespace": self.current_namespace,
                })
