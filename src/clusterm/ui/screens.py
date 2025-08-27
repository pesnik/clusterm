"""Screen components for the application
"""

from datetime import UTC
from typing import Any

from textual import on
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Static,
    TabbedContent,
    TabPane,
)

from .components.command_input import CommandInput
from .components.command_pad import CommandPad
from .components.context_selector import ContextSelector
from .components.modals import CommandModal, ConfigModal, LogModal
from .components.panels import LogPanel, StatusPanel


class MainScreen(Screen):
    """Main application screen"""

    current_namespace = reactive(None)
    selected_chart = reactive(None)
    selected_resource = reactive(None)

    def __init__(self, k8s_manager, config, event_bus, logger, command_history, **kwargs):
        super().__init__(**kwargs)
        self.k8s_manager = k8s_manager
        self.config = config
        self.event_bus = event_bus
        self.logger = logger
        self.command_history = command_history

        self.logger.debug("MainScreen.__init__: Initializing MainScreen", extra={
            "k8s_manager_type": type(k8s_manager).__name__,
            "config_keys": list(config.config_data.keys()) if hasattr(config, "config_data") else "N/A",
            "has_event_bus": event_bus is not None,
            "command_history_size": len(command_history.commands) if hasattr(command_history, "commands") else "N/A",
        })

        # Resource tables
        self.tables: dict[str, DataTable] = {}
        self.logger.debug("MainScreen.__init__: Initialized empty tables dictionary")

        # Subscribe to events
        self.logger.debug("MainScreen.__init__: Setting up event handlers")
        self._setup_event_handlers()

        self.logger.info("MainScreen.__init__: MainScreen initialization completed successfully")

    def _setup_event_handlers(self):
        """Setup event handlers"""
        self.logger.debug("MainScreen._setup_event_handlers: Entry")

        try:
            from ..core.events import EventType

            self.logger.debug("MainScreen._setup_event_handlers: Importing EventType successful")

            self.event_bus.subscribe(EventType.CLUSTER_CHANGED, self._on_cluster_changed)
            self.logger.debug("MainScreen._setup_event_handlers: Subscribed to CLUSTER_CHANGED")

            self.event_bus.subscribe(EventType.DEPLOYMENT_UPDATED, self._on_deployment_updated)
            self.logger.debug("MainScreen._setup_event_handlers: Subscribed to DEPLOYMENT_UPDATED")

            self.event_bus.subscribe(EventType.NAMESPACE_CHANGED, self._on_namespace_changed)
            self.logger.debug("MainScreen._setup_event_handlers: Subscribed to NAMESPACE_CHANGED")

            self.logger.info("MainScreen._setup_event_handlers: All event handlers setup successfully")

        except Exception as e:
            self.logger.error(f"MainScreen._setup_event_handlers: Failed to setup event handlers: {e}", extra={
                "error_type": type(e).__name__,
                "error_details": str(e),
            })
            raise

        self.logger.debug("MainScreen._setup_event_handlers: Exit")

    def compose(self):
        """Compose the main screen"""
        self.logger.debug("MainScreen.compose: Entry - Starting UI composition")

        self.logger.debug("MainScreen.compose: Yielding Header component")
        yield Header(show_clock=True)

        with Container(id="main-container"):
            # Status bar
            yield StatusPanel(id="status-panel")

            with Horizontal(id="main-content"):
                # Left panel - Charts, actions, and context selector
                with Vertical(id="charts-panel", classes="panel"):
                    # Context selector dropdowns
                    yield ContextSelector(self.k8s_manager, logger=self.logger, id="context-selector")

                    with Vertical(classes="action-buttons"):
                        yield Button("🔗 Test Connection", id="test-connection-btn", classes="action-btn")
                        yield Button("⚡ Execute Command", id="execute-command-btn", classes="action-btn")

                    with Vertical(classes="charts-section"):
                        yield Static("📦 Helm Charts", classes="section-title")
                        yield DataTable(id="charts-table")
                        yield Button("🚀 Deploy Selected", variant="primary", id="deploy-chart-btn", classes="deploy-btn")

                # Right panel - Resource tabs
                with TabbedContent(id="resources-tabs"):
                    with TabPane("Deployments", id="deployments-tab"):
                        yield DataTable(id="deployments-table", classes="resource-tab-table")

                        with Horizontal(classes="resource-tab-actions"):
                            yield Button("View Logs", id="deployment-logs-btn", classes="resource-tab-button")
                            yield Button("Refresh", id="refresh-deployments-btn", classes="resource-tab-button")

                    with TabPane("Pods", id="pods-tab"):
                        yield DataTable(id="pods-table", classes="resource-tab-table")

                        with Horizontal(classes="resource-tab-actions"):
                            yield Button("Describe", id="describe-pod-btn", classes="resource-tab-button")
                            yield Button("Logs", id="pod-logs-btn", classes="resource-tab-button")

                    with TabPane("Services", id="services-tab"):
                        yield DataTable(id="services-table", classes="resource-tab-table")

                        with Horizontal(classes="resource-tab-actions"):
                            yield Button("Describe", id="describe-service-btn", classes="resource-tab-button")

                    with TabPane("Helm Releases", id="helm-tab"):
                        yield DataTable(id="helm-table", classes="resource-tab-table")

                        with Horizontal(classes="resource-tab-actions"):
                            yield Button("Status", id="helm-status-btn", classes="resource-tab-button")
                            yield Button("History", id="helm-history-btn", classes="resource-tab-button")

                    with TabPane("Namespaces", id="namespaces-tab"):
                        yield DataTable(id="namespaces-table", classes="resource-tab-table")

                        with Horizontal(classes="resource-tab-actions"):
                            yield Button("Describe", id="describe-namespace-btn", classes="resource-tab-button")

                    with TabPane("Command Pad", id="command-pad-tab"):
                        yield CommandPad(self.command_history, logger=self.logger, id="command-pad")

                    with TabPane("Smart Input", id="smart-input-tab"):
                        yield CommandInput(
                            self.command_history,
                            self.k8s_manager,
                            logger=self.logger,
                            id="interactive-input",
                        )

            # Bottom panel - Logs
            yield LogPanel(id="log-panel")

        self.logger.debug("MainScreen.compose: Yielding Footer component")
        yield Footer()

        self.logger.info("MainScreen.compose: UI composition completed successfully")

    def on_mount(self):
        """Initialize the screen"""
        self.logger.debug("MainScreen.on_mount: Entry - Starting screen initialization")

        try:
            # Setup all tables
            self.logger.debug("MainScreen.on_mount: Scheduling _setup_all_tables")
            self.call_after_refresh(self._setup_all_tables)

            self.logger.debug("MainScreen.on_mount: Scheduling _refresh_all_data")
            self.call_after_refresh(self._refresh_all_data)

            self.logger.debug("MainScreen.on_mount: Scheduling _update_status_panel")
            self.call_after_refresh(self._update_status_panel)

            def log_startup():
                try:
                    log_panel = self.query_one("#log-panel", LogPanel)
                    log_panel.write_log("Clusterm started successfully")
                except:
                    pass

            self.call_after_refresh(log_startup)

            # Sync context selector with initial state and get actual namespace
            def sync_context_selector():
                try:
                    context_selector = self.query_one("#context-selector", ContextSelector)
                    # Get the actual namespace from context selector (it was initialized from cluster data)
                    if context_selector.current_namespace:
                        self.current_namespace = context_selector.current_namespace
                    else:
                        # Fallback if context selector failed to initialize
                        self.current_namespace = "default"

                    # Don't call refresh_selectors here - let the context selector handle its own refresh via on_mount
                    self.logger.info(f"MainScreen: Synced with context selector - namespace: {self.current_namespace}")
                except Exception as e:
                    self.logger.error(f"MainScreen: Failed to sync with context selector: {e}")
                    # Safe fallback
                    self.current_namespace = "default"

            self.logger.debug("MainScreen.on_mount: Scheduling sync_context_selector")
            self.call_after_refresh(sync_context_selector)

            self.logger.info("MainScreen.on_mount: Screen initialization completed successfully")

        except Exception as e:
            self.logger.error(f"MainScreen.on_mount: Failed during mount: {e}", extra={
                "error_type": type(e).__name__,
                "error_details": str(e),
            })
            raise

    def _setup_charts_table(self):
        """Setup the Helm charts table"""
        self.logger.debug("MainScreen._setup_charts_table: Entry")

        try:
            self.logger.debug("MainScreen._setup_charts_table: Querying charts table component")
            charts_table = self.query_one("#charts-table", DataTable)

            self.logger.debug("MainScreen._setup_charts_table: Adding columns to charts table")
            charts_table.add_columns("Chart", "Version", "Description")

            self.logger.debug("MainScreen._setup_charts_table: Getting available charts from k8s_manager")
            charts = self.k8s_manager.get_available_charts(self.current_namespace)
            self.logger.debug(f"MainScreen._setup_charts_table: Retrieved {len(charts)} charts for namespace {self.current_namespace}")

            for i, chart in enumerate(charts):
                self.logger.debug(f"MainScreen._setup_charts_table: Processing chart {i+1}/{len(charts)}: {chart.get('name', 'unknown')}")
                description = chart["description"]
                if len(description) > 40:
                    description = description[:37] + "..."

                charts_table.add_row(
                    chart["name"],
                    chart["version"],
                    description,
                )
                self.logger.debug(f"MainScreen._setup_charts_table: Added chart row: {chart['name']} v{chart['version']}")

            # Auto-select first chart if none selected
            if charts and not self.selected_chart:
                self.selected_chart = charts[0]["name"]
                self.logger.info(f"MainScreen._setup_charts_table: Auto-selected first chart: {self.selected_chart}")
                # Update status
                self._update_status_panel_with_chart()

            self.logger.info(f"MainScreen._setup_charts_table: Successfully setup charts table with {len(charts)} entries")

        except Exception as e:
            self.logger.error(f"MainScreen._setup_charts_table: Error setting up charts table: {e}", extra={
                "error_type": type(e).__name__,
                "error_details": str(e),
            })

    def _update_charts_table(self):
        """Update the charts table with current namespace data"""
        self.logger.debug(f"MainScreen._update_charts_table: Entry - Updating for namespace: {self.current_namespace}")

        try:
            charts_table = self.query_one("#charts-table", DataTable)
            self.logger.debug("MainScreen._update_charts_table: Clearing existing chart data")
            charts_table.clear()

            charts = self.k8s_manager.get_available_charts(self.current_namespace)
            self.logger.debug(f"MainScreen._update_charts_table: Retrieved {len(charts)} charts for namespace {self.current_namespace}")

            for i, chart in enumerate(charts):
                self.logger.debug(f"MainScreen._update_charts_table: Processing chart {i+1}/{len(charts)}: {chart.get('name', 'unknown')}")
                description = chart["description"]
                if len(description) > 40:
                    description = description[:37] + "..."

                charts_table.add_row(
                    chart["name"],
                    chart["version"],
                    description,
                )
                self.logger.debug(f"MainScreen._update_charts_table: Added chart row: {chart['name']} v{chart['version']}")

            # Auto-select first chart if none selected or if selected chart is not in current list
            chart_names = [chart["name"] for chart in charts]
            if charts and (not self.selected_chart or self.selected_chart not in chart_names):
                self.selected_chart = charts[0]["name"]
                self.logger.info(f"MainScreen._update_charts_table: Auto-selected first chart: {self.selected_chart}")
                # Update status
                self._update_status_panel_with_chart()

            self.logger.info(f"MainScreen._update_charts_table: Successfully updated charts table with {len(charts)} entries for namespace {self.current_namespace}")

        except Exception as e:
            self.logger.error(f"MainScreen._update_charts_table: Error updating charts table: {e}", extra={
                "error_type": type(e).__name__,
                "error_details": str(e),
                "current_namespace": self.current_namespace,
            })

    def _setup_all_tables(self):
        """Setup all data tables"""
        self.logger.debug("MainScreen._setup_all_tables: Entry - Setting up all data tables")

        try:
            # Setup charts table
            self.logger.debug("MainScreen._setup_all_tables: Setting up charts table")
            self._setup_charts_table()

            # Setup resource tables
            deployments_table = self.query_one("#deployments-table", DataTable)
            deployments_table.add_columns("Name", "Status", "Replicas", "Age", "Namespace")

            pods_table = self.query_one("#pods-table", DataTable)
            pods_table.add_columns("Name", "Status", "Ready", "Restarts", "Age", "Node")

            services_table = self.query_one("#services-table", DataTable)
            services_table.add_columns("Name", "Type", "Cluster-IP", "External-IP", "Port(s)", "Age")

            helm_table = self.query_one("#helm-table", DataTable)
            helm_table.add_columns("Name", "Namespace", "Revision", "Updated", "Status", "Chart")

            namespaces_table = self.query_one("#namespaces-table", DataTable)
            namespaces_table.add_columns("Name", "Status", "Age")

            # Store table references
            self.logger.debug("MainScreen._setup_all_tables: Storing table references")
            self.tables["deployments"] = deployments_table
            self.tables["pods"] = pods_table
            self.tables["services"] = services_table
            self.tables["helm"] = helm_table
            self.tables["namespaces"] = namespaces_table

            self.logger.info(f"MainScreen._setup_all_tables: Successfully setup all {len(self.tables)} tables")

        except Exception as e:
            self.logger.error(f"MainScreen._setup_all_tables: Error setting up tables: {e}", extra={
                "error_type": type(e).__name__,
                "error_details": str(e),
            })

    def _refresh_all_data(self):
        """Refresh all resource data"""
        self.logger.debug("MainScreen._refresh_all_data: Entry - Starting data refresh")

        try:
            log_panel = self.query_one("#log-panel", LogPanel)

            if not self.tables:
                self.logger.warning("MainScreen._refresh_all_data: Tables not set up yet, skipping data refresh")
                return  # Tables not set up yet

            self.logger.debug(f"MainScreen._refresh_all_data: Refreshing data for namespace: {self.current_namespace}")

            log_panel.write_log(f"🔄 Refreshing data for namespace: {self.current_namespace}")

            # Refresh charts table for current namespace
            self.logger.debug("MainScreen._refresh_all_data: Updating charts table")
            self._update_charts_table()

            # Refresh deployments for current namespace
            self.logger.debug("MainScreen._refresh_all_data: Getting deployments")
            deployments = self.k8s_manager.get_deployments(self.current_namespace)
            self.logger.debug(f"MainScreen._refresh_all_data: Retrieved {len(deployments)} deployments")
            self._update_deployments_table(deployments)

            # Refresh pods
            self.logger.debug("MainScreen._refresh_all_data: Getting pods")
            pods = self.k8s_manager.get_pods(self.current_namespace)
            self.logger.debug(f"MainScreen._refresh_all_data: Retrieved {len(pods)} pods")
            self._update_pods_table(pods)

            # Refresh services
            self.logger.debug("MainScreen._refresh_all_data: Getting services")
            services = self.k8s_manager.get_services(self.current_namespace)
            self.logger.debug(f"MainScreen._refresh_all_data: Retrieved {len(services)} services")
            self._update_services_table(services)

            # Refresh helm releases
            self.logger.debug("MainScreen._refresh_all_data: Getting helm releases")
            helm_releases = self.k8s_manager.get_helm_releases(self.current_namespace)
            self.logger.debug(f"MainScreen._refresh_all_data: Retrieved {len(helm_releases)} helm releases")
            self._update_helm_table(helm_releases)

            # Refresh namespaces
            self.logger.debug("MainScreen._refresh_all_data: Getting namespaces")
            namespaces = self.k8s_manager.get_namespaces()
            self.logger.debug(f"MainScreen._refresh_all_data: Retrieved {len(namespaces)} namespaces")
            self._update_namespaces_table(namespaces)

            try:
                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log(f"✅ Data refreshed successfully for namespace: {self.current_namespace}")
                log_panel.write_log(f"📊 Resource counts - Deployments: {len(deployments)}, Pods: {len(pods)}, Services: {len(services)}")
            except:
                pass

            self.logger.info(f"MainScreen._refresh_all_data: Successfully refreshed all data for namespace: {self.current_namespace}")

        except Exception as e:
            self.logger.error(f"MainScreen._refresh_all_data: Error refreshing data: {e}", extra={
                "error_type": type(e).__name__,
                "error_details": str(e),
                "current_namespace": self.current_namespace,
            })
            try:
                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log(f"Error refreshing data: {e!s}", "ERROR")
            except:
                self.logger.error("MainScreen._refresh_all_data: Additional error writing to log panel")

    def _calculate_age(self, timestamp_str: str) -> str:
        """Calculate human-readable age from timestamp"""
        try:
            from datetime import datetime
            created_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            age_delta = datetime.now(UTC) - created_time

            if age_delta.days > 0:
                return f"{age_delta.days}d"
            if age_delta.seconds > 3600:
                return f"{age_delta.seconds // 3600}h"
            if age_delta.seconds > 60:
                return f"{age_delta.seconds // 60}m"
            return f"{age_delta.seconds}s"
        except Exception:
            return "Unknown"

    def _update_deployments_table(self, deployments):
        """Update deployments table"""
        self.logger.debug(f"MainScreen._update_deployments_table: Entry - Updating with {len(deployments)} deployments")

        if "deployments" not in self.tables:
            self.logger.warning("MainScreen._update_deployments_table: Deployments table not found, skipping update")
            return

        table = self.tables["deployments"]
        self.logger.debug("MainScreen._update_deployments_table: Clearing existing table data")
        table.clear()


        for i, deployment in enumerate(deployments):
            self.logger.debug(f"MainScreen._update_deployments_table: Processing deployment {i+1}/{len(deployments)}: {deployment.get('metadata', {}).get('name', 'unknown')}")
            name = deployment["metadata"]["name"]
            namespace = deployment["metadata"]["namespace"]
            status = deployment["status"]

            # Calculate replicas
            ready_replicas = status.get("readyReplicas", 0)
            total_replicas = status.get("replicas", 0)
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

            table.add_row(name, status_text, replicas_str, age, namespace)
            self.logger.debug(f"MainScreen._update_deployments_table: Added row for {name}: {status_text}, {replicas_str}, {age}")

        self.logger.info(f"MainScreen._update_deployments_table: Successfully updated deployments table with {len(deployments)} entries")

    def _update_pods_table(self, pods):
        """Update pods table"""
        self.logger.debug(f"MainScreen._update_pods_table: Entry - Updating with {len(pods)} pods")

        if "pods" not in self.tables:
            self.logger.warning("MainScreen._update_pods_table: Pods table not found, skipping update")
            return

        table = self.tables["pods"]
        self.logger.debug("MainScreen._update_pods_table: Clearing existing table data")
        table.clear()


        for i, pod in enumerate(pods):
            self.logger.debug(f"MainScreen._update_pods_table: Processing pod {i+1}/{len(pods)}: {pod.get('metadata', {}).get('name', 'unknown')}")
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

            table.add_row(name, phase, ready, str(restarts), age, node)
            self.logger.debug(f"MainScreen._update_pods_table: Added row for {name}: {phase}, {ready}, {restarts} restarts, {age}, node={node}")

        self.logger.info(f"MainScreen._update_pods_table: Successfully updated pods table with {len(pods)} entries")

    def _update_services_table(self, services):
        """Update services table"""
        self.logger.debug(f"MainScreen._update_services_table: Entry - Updating with {len(services)} services")

        if "services" not in self.tables:
            self.logger.warning("MainScreen._update_services_table: Services table not found, skipping update")
            return

        table = self.tables["services"]
        self.logger.debug("MainScreen._update_services_table: Clearing existing table data")
        table.clear()

        for i, service in enumerate(services):
            self.logger.debug(f"MainScreen._update_services_table: Processing service {i+1}/{len(services)}: {service.get('metadata', {}).get('name', 'unknown')}")
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

            age = self._calculate_age(service["metadata"]["creationTimestamp"])

            table.add_row(name, service_type, cluster_ip, external_ip, ports_display, age)
            self.logger.debug(f"MainScreen._update_services_table: Added row for {name}: {service_type}, {cluster_ip}, {ports_display}")

        self.logger.info(f"MainScreen._update_services_table: Successfully updated services table with {len(services)} entries")

    def _update_helm_table(self, releases):
        """Update helm releases table"""
        self.logger.debug(f"MainScreen._update_helm_table: Entry - Updating with {len(releases)} helm releases")

        if "helm" not in self.tables:
            self.logger.warning("MainScreen._update_helm_table: Helm table not found, skipping update")
            return

        table = self.tables["helm"]
        self.logger.debug("MainScreen._update_helm_table: Clearing existing table data")
        table.clear()

        for i, release in enumerate(releases):
            self.logger.debug(f"MainScreen._update_helm_table: Processing release {i+1}/{len(releases)}: {release.get('name', 'unknown')}")
            name = release.get("name", "Unknown")
            namespace = release.get("namespace", "Unknown")
            revision = str(release.get("revision", "Unknown"))
            updated = release.get("updated", "Unknown")
            status = release.get("status", "Unknown")
            chart = release.get("chart", "Unknown")

            table.add_row(name, namespace, revision, updated, status, chart)
            self.logger.debug(f"MainScreen._update_helm_table: Added row for {name}: {status}, rev={revision}, chart={chart}")

        self.logger.info(f"MainScreen._update_helm_table: Successfully updated helm table with {len(releases)} entries")

    def _update_namespaces_table(self, namespaces):
        """Update namespaces table"""
        self.logger.debug(f"MainScreen._update_namespaces_table: Entry - Updating with {len(namespaces)} namespaces")

        if "namespaces" not in self.tables:
            self.logger.warning("MainScreen._update_namespaces_table: Namespaces table not found, skipping update")
            return

        table = self.tables["namespaces"]
        self.logger.debug("MainScreen._update_namespaces_table: Clearing existing table data")
        table.clear()

        for i, ns in enumerate(namespaces):
            self.logger.debug(f"MainScreen._update_namespaces_table: Processing namespace {i+1}/{len(namespaces)}: {ns.get('metadata', {}).get('name', 'unknown')}")
            name = ns["metadata"]["name"]
            phase = ns["status"]["phase"]
            age = self._calculate_age(ns["metadata"]["creationTimestamp"])

            table.add_row(name, phase, age)
            self.logger.debug(f"MainScreen._update_namespaces_table: Added row for {name}: {phase}, {age}")

        self.logger.info(f"MainScreen._update_namespaces_table: Successfully updated namespaces table with {len(namespaces)} entries")

    def _update_status_panel(self):
        """Update the status panel"""
        self.logger.debug("MainScreen._update_status_panel: Entry")

        try:
            status_panel = self.query_one("#status-panel", StatusPanel)
            current_cluster = self.k8s_manager.cluster_manager.get_current_cluster()

            if current_cluster:
                cluster_name = current_cluster["name"]
                self.logger.debug(f"MainScreen._update_status_panel: Testing connection for cluster: {cluster_name}")
                # Test connection
                success, message = self.k8s_manager.cluster_manager.test_cluster_connection(cluster_name)
                self.logger.debug(f"MainScreen._update_status_panel: Connection test result: {success} - {message}")
                status_panel.update_cluster_status(cluster_name, success)
                self.logger.info(f"MainScreen._update_status_panel: Updated status panel for cluster {cluster_name}: {'connected' if success else 'disconnected'}")
            else:
                self.logger.warning("MainScreen._update_status_panel: No current cluster found")
                status_panel.update_cluster_status("No Cluster", False)

        except Exception as e:
            self.logger.error(f"MainScreen._update_status_panel: Error updating status panel: {e}", extra={
                "error_type": type(e).__name__,
                "error_details": str(e),
            })

    def _update_status_panel_with_chart(self):
        """Update the status panel to show selected chart"""
        try:
            status_panel = self.query_one("#status-panel", StatusPanel)
            status_panel.update_chart_status(self.selected_chart)  # type: ignore
        except Exception as e:
            self.logger.error(f"MainScreen._update_status_panel_with_chart: Error: {e}")

    def _on_resource_selected(self, resource_info: dict[str, Any]):
        """Handle resource selection"""
        self.logger.debug(f"MainScreen._on_resource_selected: Entry - Resource info: {resource_info}")

        self.selected_resource = resource_info

        try:
            log_panel = self.query_one("#log-panel", LogPanel)
            resource_type = resource_info["type"]
            resource_name = resource_info["data"][0]  # First column is typically name

            self.logger.info(f"MainScreen._on_resource_selected: Selected {resource_type}: {resource_name}")
            log_panel.write_log(f"Selected {resource_type}: {resource_name}")

        except Exception as e:
            self.logger.error(f"MainScreen._on_resource_selected: Error handling resource selection: {e}", extra={
                "error_type": type(e).__name__,
                "resource_info": resource_info,
            })

    def _on_cluster_changed(self, event):
        """Handle cluster change events"""
        self.logger.debug(f"MainScreen._on_cluster_changed: Entry - Event data: {event.data}")

        new_cluster = event.data.get("new_cluster", "Unknown")
        self.logger.info(f"MainScreen._on_cluster_changed: Processing cluster change to: {new_cluster}")

        try:
            # Update command history context when cluster changes
            self.logger.debug("MainScreen._on_cluster_changed: Updating command history context")
            self._update_command_history_context()

            self.logger.debug("MainScreen._on_cluster_changed: Refreshing command pad")
            self._refresh_command_pad()

            self.logger.debug("MainScreen._on_cluster_changed: Refreshing all data")
            self._refresh_all_data()

            self.logger.debug("MainScreen._on_cluster_changed: Updating status panel")
            self._update_status_panel()

            log_panel = self.query_one("#log-panel", LogPanel)
            log_panel.write_log(f"Switched to cluster: {new_cluster}")

            self.logger.info(f"MainScreen._on_cluster_changed: Successfully processed cluster change to: {new_cluster}")

        except Exception as e:
            self.logger.error(f"MainScreen._on_cluster_changed: Error handling cluster change: {e}", extra={
                "error_type": type(e).__name__,
                "new_cluster": new_cluster,
                "event_data": event.data,
            })

    def _on_deployment_updated(self, event):
        """Handle deployment update events"""
        self.logger.debug(f"MainScreen._on_deployment_updated: Entry - Event data: {event.data}")

        chart_name = event.data.get("chart_name", "Unknown")
        action = event.data.get("action", "updated")
        self.logger.info(f"MainScreen._on_deployment_updated: Processing deployment {action}: {chart_name}")

        try:
            self.logger.debug("MainScreen._on_deployment_updated: Refreshing all data")
            self._refresh_all_data()

            log_panel = self.query_one("#log-panel", LogPanel)
            log_panel.write_log(f"Deployment {action}: {chart_name}")

            self.logger.info(f"MainScreen._on_deployment_updated: Successfully processed deployment {action}: {chart_name}")

        except Exception as e:
            self.logger.error(f"MainScreen._on_deployment_updated: Error handling deployment update: {e}", extra={
                "error_type": type(e).__name__,
                "chart_name": chart_name,
                "action": action,
            })

    def _on_namespace_changed(self, event):
        """Handle namespace change events"""
        self.logger.debug(f"MainScreen._on_namespace_changed: Entry - Event data: {event.data}")

        new_namespace = event.data.get("namespace")
        self.logger.info(f"MainScreen._on_namespace_changed: Processing namespace change to: {new_namespace}")

        if new_namespace:
            try:
                self.current_namespace = new_namespace
                self.logger.debug(f"MainScreen._on_namespace_changed: Updated current_namespace to: {new_namespace}")

                # Update command history context when namespace changes
                self.logger.debug("MainScreen._on_namespace_changed: Updating command history context")
                self._update_command_history_context()

                self.logger.debug("MainScreen._on_namespace_changed: Refreshing command pad")
                self._refresh_command_pad()

                self.logger.debug("MainScreen._on_namespace_changed: Refreshing all data")
                self._refresh_all_data()

                self.logger.info(f"MainScreen._on_namespace_changed: Successfully processed namespace change to: {new_namespace}")

            except Exception as e:
                self.logger.error(f"MainScreen._on_namespace_changed: Error handling namespace change: {e}", extra={
                    "error_type": type(e).__name__,
                    "new_namespace": new_namespace,
                })
        else:
            self.logger.warning("MainScreen._on_namespace_changed: No namespace provided in event data")

    # Context change handler
    @on(ContextSelector.ContextChanged)
    def handle_context_change(self, message):
        """Handle context changes from ContextSelector"""
        log_panel = self.query_one("#log-panel", LogPanel)

        if message.change_type == "cluster":
            # Cluster changed - refresh everything
            log_panel.write_log(f"🔄 Cluster changed to: {message.cluster}")
            self.current_namespace = message.namespace
            self._update_command_history_context()
            self._refresh_command_pad()
            log_panel.write_log("🔄 Refreshing all resources for new cluster...")
            self._refresh_all_data()
            self._update_status_panel()

            log_panel.write_log(f"✅ Successfully switched to cluster: {message.cluster}")

        elif message.change_type == "namespace":
            # Namespace changed - refresh namespace-specific resources
            log_panel.write_log(f"📂 Namespace changed to: {message.namespace}")
            self.current_namespace = message.namespace
            self._update_command_history_context()
            self._refresh_command_pad()
            log_panel.write_log("🔄 Refreshing namespace-specific resources...")
            self._refresh_namespace_specific_data()

            log_panel.write_log(f"✅ Successfully switched to namespace: {message.namespace}")

    def _refresh_namespace_specific_data(self):
        """Refresh data that depends on namespace"""
        try:
            log_panel = self.query_one("#log-panel", LogPanel)

            # Update charts table for current namespace
            self.logger.debug("MainScreen._refresh_namespace_specific_data: Updating charts table")
            self._update_charts_table()

            # Update pods
            pods = self.k8s_manager.get_pods(self.current_namespace)
            self._update_pods_table(pods)

            # Update services
            services = self.k8s_manager.get_services(self.current_namespace)
            self._update_services_table(services)

            # Update deployments for current namespace
            deployments = self.k8s_manager.get_deployments(self.current_namespace)
            self._update_deployments_table(deployments)

            # Get charts count for logging
            charts = self.k8s_manager.get_available_charts(self.current_namespace)
            log_panel.write_log(f"📊 Found {len(charts)} charts, {len(pods)} pods, {len(services)} services, {len(deployments)} deployments")

        except Exception as e:
            try:
                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log(f"❌ Error refreshing namespace data: {e!s}", "ERROR")
            except:
                pass

    # Button handlers

    @on(Button.Pressed, "#test-connection-btn")
    def test_connection(self):
        """Test current cluster connection"""
        self.logger.debug("MainScreen.test_connection: Entry - Test connection button pressed")

        try:
            current_cluster = self.k8s_manager.cluster_manager.get_current_cluster()
            self.logger.debug(f"MainScreen.test_connection: Current cluster: {current_cluster}")
            if current_cluster:
                cluster_name = current_cluster["name"]
                self.logger.info(f"MainScreen.test_connection: Testing connection to cluster: {cluster_name}")

                success, message = self.k8s_manager.cluster_manager.test_cluster_connection(cluster_name)
                self.logger.debug(f"MainScreen.test_connection: Connection test result: {success} - {message}")

                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log(message, "INFO" if success else "ERROR")

                self.logger.debug("MainScreen.test_connection: Updating status panel")
                self._update_status_panel()

                self.logger.info(f"MainScreen.test_connection: Connection test completed - {cluster_name}: {'success' if success else 'failed'}")
            else:
                self.logger.warning("MainScreen.test_connection: No cluster selected for connection test")
                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log("No cluster selected", "ERROR")

        except Exception as e:
            self.logger.error(f"MainScreen.test_connection: Error during connection test: {e}", extra={
                "error_type": type(e).__name__,
                "error_details": str(e),
            })
            try:
                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log(f"Connection test failed: {e!s}", "ERROR")
            except:
                pass

    @on(Button.Pressed, "#execute-command-btn")
    def execute_command(self):
        """Execute kubectl/helm command"""
        self.logger.debug("MainScreen.execute_command: Entry - Execute command button pressed")

        try:
            self.logger.debug("MainScreen.execute_command: Creating CommandModal")
            modal = CommandModal()
            self.logger.debug("MainScreen.execute_command: Pushing CommandModal screen")
            self.app.push_screen(modal, self._handle_command_result)
            self.logger.info("MainScreen.execute_command: CommandModal opened successfully")

        except Exception as e:
            self.logger.error(f"MainScreen.execute_command: Error opening command modal: {e}", extra={
                "error_type": type(e).__name__,
                "error_details": str(e),
            })

    @on(Button.Pressed, "#deploy-chart-btn")
    def deploy_chart(self):
        """Deploy selected chart"""
        self.logger.debug(f"MainScreen.deploy_chart: Entry - Deploy chart button pressed, selected_chart: {self.selected_chart}")

        try:
            if not self.selected_chart:
                self.logger.warning("MainScreen.deploy_chart: No chart selected")
                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log("Please select a chart first", "ERROR")
                return

            self.logger.info(f"MainScreen.deploy_chart: Creating ConfigModal for chart: {self.selected_chart}")
            modal = ConfigModal(self.selected_chart)
            self.logger.debug("MainScreen.deploy_chart: Pushing ConfigModal screen")
            self.app.push_screen(modal, self._handle_deploy_result)
            self.logger.info(f"MainScreen.deploy_chart: ConfigModal opened for chart: {self.selected_chart}")

        except Exception as e:
            self.logger.error(f"MainScreen.deploy_chart: Error opening deploy modal: {e}", extra={
                "error_type": type(e).__name__,
                "selected_chart": self.selected_chart,
            })

    # Resource action handlers
    @on(Button.Pressed, "#describe-pod-btn")
    def describe_pod(self):
        """Describe selected pod"""
        self.logger.debug("MainScreen.describe_pod: Entry - Describe pod button pressed")

        try:
            pods_table = self.query_one("#pods-table", DataTable)
            self.logger.debug(f"MainScreen.describe_pod: Cursor row: {pods_table.cursor_row}")

            if pods_table.cursor_row is not None:
                row_data = pods_table.get_row_at(pods_table.cursor_row)
                pod_name = str(row_data[0])
                self.logger.info(f"MainScreen.describe_pod: Describing pod: {pod_name} in namespace: {self.current_namespace}")

                try:
                    log_panel = self.query_one("#log-panel", LogPanel)
                    log_panel.write_log(f"📋 Describing pod: {pod_name}")

                    self.logger.debug(f"MainScreen.describe_pod: Getting description for pod: {pod_name}")
                    description = self.k8s_manager.describe_resource("pod", pod_name, self.current_namespace)
                    self.logger.debug(f"MainScreen.describe_pod: Description retrieved, length: {len(description)}")

                    # Show description in a modal
                    from .components.modals import LogModal
                    modal = LogModal("Pod Description", description, "yaml")
                    self.app.push_screen(modal)

                    self.logger.info(f"MainScreen.describe_pod: Successfully opened pod description modal for: {pod_name}")

                except Exception as e:
                    self.logger.error(f"MainScreen.describe_pod: Error describing pod {pod_name}: {e}", extra={
                        "error_type": type(e).__name__,
                        "pod_name": pod_name,
                        "namespace": self.current_namespace,
                    })
                    log_panel = self.query_one("#log-panel", LogPanel)
                    log_panel.write_log(f"❌ Error describing pod: {e!s}", "ERROR")
            else:
                self.logger.warning("MainScreen.describe_pod: No pod selected")
                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log("Please select a pod first", "ERROR")

        except Exception as e:
            self.logger.error(f"MainScreen.describe_pod: Error in describe_pod handler: {e}", extra={
                "error_type": type(e).__name__,
            })

    @on(Button.Pressed, "#pod-logs-btn")
    def view_pod_logs(self):
        """View logs for selected pod"""
        self.logger.debug("MainScreen.view_pod_logs: Entry - View pod logs button pressed")

        try:
            pods_table = self.query_one("#pods-table", DataTable)
            self.logger.debug(f"MainScreen.view_pod_logs: Cursor row: {pods_table.cursor_row}")

            if pods_table.cursor_row is not None:
                row_data = pods_table.get_row_at(pods_table.cursor_row)
                pod_name = str(row_data[0])
                self.logger.info(f"MainScreen.view_pod_logs: Getting logs for pod: {pod_name} in namespace: {self.current_namespace}")

                try:
                    log_panel = self.query_one("#log-panel", LogPanel)
                    log_panel.write_log(f"📜 Getting logs for pod: {pod_name}")

                    self.logger.debug(f"MainScreen.view_pod_logs: Retrieving logs for pod: {pod_name}")
                    logs = self.k8s_manager.get_pod_logs(pod_name, self.current_namespace)
                    self.logger.debug(f"MainScreen.view_pod_logs: Logs retrieved, length: {len(logs)}")

                    # Show logs in a modal
                    from .components.modals import LogModal
                    modal = LogModal("Pod Logs", logs, "log")
                    self.app.push_screen(modal)

                    self.logger.info(f"MainScreen.view_pod_logs: Successfully opened pod logs modal for: {pod_name}")

                except Exception as e:
                    self.logger.error(f"MainScreen.view_pod_logs: Error getting pod logs for {pod_name}: {e}", extra={
                        "error_type": type(e).__name__,
                        "pod_name": pod_name,
                        "namespace": self.current_namespace,
                    })
                    log_panel = self.query_one("#log-panel", LogPanel)
                    log_panel.write_log(f"❌ Error getting pod logs: {e!s}", "ERROR")
            else:
                self.logger.warning("MainScreen.view_pod_logs: No pod selected")
                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log("Please select a pod first", "ERROR")

        except Exception as e:
            self.logger.error(f"MainScreen.view_pod_logs: Error in view_pod_logs handler: {e}", extra={
                "error_type": type(e).__name__,
            })

    @on(Button.Pressed, "#describe-service-btn")
    def describe_service(self):
        """Describe selected service"""
        services_table = self.query_one("#services-table", DataTable)
        if services_table.cursor_row is not None:
            row_data = services_table.get_row_at(services_table.cursor_row)
            service_name = str(row_data[0])

            try:
                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log(f"📋 Describing service: {service_name}")

                description = self.k8s_manager.describe_resource("service", service_name, self.current_namespace)

                # Show description in a modal
                from .components.modals import LogModal
                modal = LogModal("Service Description", description, "yaml")
                self.app.push_screen(modal)

            except Exception as e:
                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log(f"❌ Error describing service: {e!s}", "ERROR")
        else:
            log_panel = self.query_one("#log-panel", LogPanel)
            log_panel.write_log("Please select a service first", "ERROR")

    @on(Button.Pressed, "#describe-namespace-btn")
    def describe_namespace(self):
        """Describe selected namespace"""
        namespaces_table = self.query_one("#namespaces-table", DataTable)
        if namespaces_table.cursor_row is not None:
            row_data = namespaces_table.get_row_at(namespaces_table.cursor_row)
            namespace_name = str(row_data[0])

            try:
                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log(f"📋 Describing namespace: {namespace_name}")

                description = self.k8s_manager.describe_resource("namespace", namespace_name)

                # Show description in a modal
                from .components.modals import LogModal
                modal = LogModal("Namespace Description", description, "yaml")
                self.app.push_screen(modal)

            except Exception as e:
                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log(f"❌ Error describing namespace: {e!s}", "ERROR")
        else:
            log_panel = self.query_one("#log-panel", LogPanel)
            log_panel.write_log("Please select a namespace first", "ERROR")

    @on(Button.Pressed, "#deployment-logs-btn")
    def view_deployment_logs(self):
        """View logs for selected deployment"""
        deployments_table = self.query_one("#deployments-table", DataTable)
        if deployments_table.cursor_row is not None:
            row_data = deployments_table.get_row_at(deployments_table.cursor_row)
            deployment_name = str(row_data[0])

            try:
                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log(f"📜 Getting logs for deployment: {deployment_name}")

                # For deployments, we'll describe it since logs are from pods
                description = self.k8s_manager.describe_resource("deployment", deployment_name, self.current_namespace)

                # Show description in a modal
                from .components.modals import LogModal
                modal = LogModal("Deployment Details", description, "yaml")
                self.app.push_screen(modal)

            except Exception as e:
                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log(f"❌ Error getting deployment details: {e!s}", "ERROR")
        else:
            log_panel = self.query_one("#log-panel", LogPanel)
            log_panel.write_log("Please select a deployment first", "ERROR")

    def _handle_command_result(self, result):
        """Handle command execution result"""
        if not result or result[0] == "cancel":
            return

        _, cmd_type, cmd_args = result
        log_panel = self.query_one("#log-panel", LogPanel)

        # Update command history context
        self._update_command_history_context()

        # Inject current namespace context if not already specified
        if cmd_type == "kubectl":
            cmd_args = self._inject_namespace_context(cmd_args)
        elif cmd_type == "helm":
            cmd_args = self._inject_helm_context(cmd_args)

        # Build the full command for history
        full_command = f"{cmd_type} {cmd_args}"
        log_panel.write_log(f"Executing {full_command}")

        if cmd_type == "kubectl":
            success, output = self.k8s_manager.command_executor.execute_kubectl(cmd_args.split())
        else:
            working_dir = self._get_helm_working_directory(cmd_args)
            success, output = self.k8s_manager.command_executor.execute_helm(cmd_args.split(), cwd=working_dir)

        if success:
            # Add to command history on successful execution (context-aware)
            self.command_history.add_command(full_command)
            # Notify all CommandPad widgets across tabs via global message
            self._notify_command_executed(full_command, cmd_type)
            log_panel.write_log("Command executed successfully")
            if output.strip():
                modal = LogModal(f"{cmd_type.title()} Output", output)
                self.app.push_screen(modal)
        else:
            log_panel.write_log(f"Command failed: {output}", "ERROR")

        self._refresh_all_data()

    def _inject_namespace_context(self, cmd_args: str) -> str:
        """Inject current namespace context into kubectl command if not already specified"""
        if not cmd_args.strip():
            return cmd_args

        # Convert to list for easier manipulation
        args = cmd_args.split()

        # Check if namespace is already specified
        has_namespace = any(arg in ["-n", "--namespace", "--all-namespaces", "-A"] for arg in args)

        if has_namespace:
            # Namespace already specified, don't modify
            return cmd_args

        # Commands that typically work with namespaced resources
        namespace_aware_commands = [
            "get", "describe", "delete", "edit", "patch", "logs", "exec",
            "port-forward", "attach", "cp", "rollout", "scale", "top"
        ]

        # Check if this is a namespace-aware command
        if args and args[0] in namespace_aware_commands:
            # Commands where we should inject current namespace
            if self.current_namespace:
                # Insert namespace after the command (even for default to be explicit)
                args.insert(1, "--namespace")
                args.insert(2, self.current_namespace)
                return " ".join(args)

        return cmd_args

    def _get_selected_chart_info(self) -> dict | None:
        """Get information about the currently selected chart"""
        self.logger.debug(f"MainScreen._get_selected_chart_info: selected_chart={self.selected_chart}, current_namespace={self.current_namespace}")
        
        if not self.selected_chart or not self.current_namespace:
            self.logger.warning(f"MainScreen._get_selected_chart_info: Missing selection - chart: {self.selected_chart}, namespace: {self.current_namespace}")
            return None

        # Get the chart path
        namespace_path = self.k8s_manager.get_current_namespace_projects_path(self.current_namespace)
        if not namespace_path:
            return None

        # Look for chart in helm-charts directory
        chart_path = namespace_path / "helm-charts" / self.selected_chart
        if chart_path.exists() and (chart_path / "Chart.yaml").exists():
            return {
                "name": self.selected_chart,
                "path": chart_path,
                "namespace": self.current_namespace
            }

        return None

    def _get_helm_working_directory(self, cmd_args: str) -> str | None:
        """Get the appropriate working directory for helm commands"""
        if not cmd_args.strip():
            return None

        args = cmd_args.split()
        if not args:
            return None

        command = args[0].lower()

        # Commands that work with local charts and benefit from chart directory context
        chart_local_commands = ["show", "template", "lint", "package", "dependency"]

        # For these commands, if there's a "." or local path, use selected chart directory
        if command in chart_local_commands:
            chart_info = self._get_selected_chart_info()
            if chart_info and ("." in args or any(not arg.startswith("-") and "/" not in arg for arg in args[1:])):
                return str(chart_info["path"])

        # For install/upgrade with local paths
        elif command in ["install", "upgrade"] and len(args) >= 3:
            chart_ref = args[2] if command == "install" else args[2]
            if chart_ref in [".", "./"]:
                chart_info = self._get_selected_chart_info()
                if chart_info:
                    return str(chart_info["path"])

        return None

    def _inject_helm_context(self, cmd_args: str) -> str:
        """Inject current cluster/namespace context into helm command"""
        if not cmd_args.strip():
            return cmd_args

        args = cmd_args.split()
        if not args:
            return cmd_args

        command = args[0].lower()

        # Commands that work with charts and need context
        chart_commands = ["install", "upgrade", "template", "lint", "package", "dependency", "show"]

        # Commands that work with releases and need namespace
        release_commands = ["list", "status", "history", "rollback", "uninstall", "get", "test"]

        modified_args = args.copy()

        # Handle chart-based commands
        if command in chart_commands:
            modified_args = self._inject_chart_context(modified_args)
            modified_args = self._inject_helm_namespace(modified_args)

        # Handle release-based commands
        elif command in release_commands:
            modified_args = self._inject_helm_namespace(modified_args)

        return " ".join(modified_args)

    def _inject_chart_context(self, args: list[str]) -> list[str]:
        """Resolve chart references to full paths"""
        if len(args) < 2:
            return args

        command = args[0].lower()

        # For install/upgrade: helm install [release-name] [chart]
        if command in ["install", "upgrade"] and len(args) >= 3:
            chart_ref = args[2]  # Third argument is chart reference
            resolved_chart = self._resolve_chart_path(chart_ref)
            if resolved_chart != chart_ref:
                args[2] = resolved_chart

        # For template/lint: helm template [chart]
        elif command in ["template", "lint"] and len(args) >= 2:
            chart_ref = args[1]  # Second argument is chart reference
            resolved_chart = self._resolve_chart_path(chart_ref)
            if resolved_chart != chart_ref:
                args[1] = resolved_chart

        # For show: helm show [subcommand] [chart]
        elif command == "show" and len(args) >= 3:
            chart_ref = args[2]  # Third argument is chart reference  
            resolved_chart = self._resolve_chart_path(chart_ref)
            if resolved_chart != chart_ref:
                args[2] = resolved_chart

        return args

    def _resolve_chart_path(self, chart_ref: str) -> str:
        """Resolve chart reference to full path if it exists in current namespace"""
        # If it's already a path, don't modify
        if "/" in chart_ref or chart_ref.startswith("./") or chart_ref.startswith("../"):
            return chart_ref

        # Try to find chart in current namespace
        if not self.k8s_manager.current_projects_path:
            return chart_ref

        namespace_path = self.k8s_manager.get_current_namespace_projects_path(self.current_namespace)
        if not namespace_path:
            return chart_ref

        # Look for chart in helm-charts directory
        helm_charts_path = namespace_path / "helm-charts"
        if helm_charts_path.exists():
            chart_path = helm_charts_path / chart_ref
            if chart_path.exists() and (chart_path / "Chart.yaml").exists():
                return str(chart_path)

        return chart_ref

    def _inject_helm_namespace(self, args: list[str]) -> list[str]:
        """Add namespace to helm command if not specified"""
        # Check if namespace already specified
        has_namespace = any(arg in ["-n", "--namespace"] for arg in args)

        if has_namespace or not self.current_namespace:
            return args

        # Add namespace flag
        return args + ["--namespace", self.current_namespace]

    def _handle_deploy_result(self, result):
        """Handle deployment configuration result"""
        if not result or result[0] == "cancel":
            return

        _, chart_name, config = result
        log_panel = self.query_one("#log-panel", LogPanel)
        log_panel.write_log(f"Deploying {chart_name}...")

        success, output = self.k8s_manager.deploy_chart(chart_name, config)

        if success:
            log_panel.write_log(f"Successfully deployed {chart_name}")
        else:
            log_panel.write_log(f"Deployment failed: {output}", "ERROR")

        self._refresh_all_data()

    @on(DataTable.RowSelected, "#charts-table")
    def chart_selected(self, event):
        """Handle chart selection"""
        self.logger.debug(f"MainScreen.chart_selected: Entry - Row index: {event.row_index}")
        
        try:
            charts_table = self.query_one("#charts-table", DataTable)
            row_data = charts_table.get_row_at(event.row_index)
            self.selected_chart = str(row_data[0])

            self.logger.info(f"MainScreen.chart_selected: Selected chart: {self.selected_chart}")

            log_panel = self.query_one("#log-panel", LogPanel)
            log_panel.write_log(f"📦 Selected chart: {self.selected_chart}")
            
            # Also update status panel to show selected chart
            self._update_status_panel_with_chart()
            
        except Exception as e:
            self.logger.error(f"MainScreen.chart_selected: Error selecting chart: {e}", extra={
                "error_type": type(e).__name__,
                "row_index": event.row_index,
            })

    def _update_command_history_context(self):
        """Update command history context based on current cluster/namespace"""
        try:
            current_cluster = self.k8s_manager.cluster_manager.get_current_cluster()
            cluster_name = current_cluster["name"] if current_cluster else "default"
            namespace = self.current_namespace

            self.command_history.set_context(cluster_name, namespace)
        except Exception as e:
            self.logger.error(f"Error updating command history context: {e}")
            # Fallback to defaults
            self.command_history.set_context("default", "default")

    def _refresh_command_pad(self):
        """Refresh the command pad to show updated commands"""
        try:
            command_pad = self.query_one("#command-pad", CommandPad)
            command_pad.action_refresh()
        except Exception:
            # Command pad might not be visible/mounted
            pass

    def _notify_command_executed(self, command: str, command_type: str | None = None) -> None:
        """Notify all CommandPad widgets that a command was executed via direct message posting.

        This enables real-time refresh across all tabs when commands are executed,
        ensuring the command history is immediately visible everywhere.

        Args:
            command: The full command that was executed (e.g., "kubectl get pods")
            command_type: The type of command (kubectl, helm, etc.)

        """
        try:
            from .components.command_pad import CommandPad

            # Find all CommandPad widgets across all screens and notify them
            all_command_pads = list(self.app.query(CommandPad))

            # If no CommandPads found in current context, check screen stack
            if not all_command_pads:
                for screen in self.app.screen_stack:
                    screen_command_pads = list(screen.query(CommandPad))
                    all_command_pads.extend(screen_command_pads)

            if all_command_pads:
                message = CommandPad.CommandExecuted(command, command_type)
                for command_pad in all_command_pads:
                    command_pad.post_message(message)

        except Exception:
            # Silently fail - UI refresh isn't critical enough to affect command execution
            pass

    @on(CommandPad.CommandSelected)
    def handle_command_pad_selection(self, message):
        """Handle command selection from command pad"""
        if message.command is None:
            # Signal to show add dialog - not implemented yet
            log_panel = self.query_one("#log-panel", LogPanel)
            log_panel.write_log("Add current command feature not implemented yet")
            return

        # Update command history context
        self._update_command_history_context()

        # Execute the selected command
        cmd_type, cmd_args = message.command.command_type, message.command.command

        # Remove the command prefix if it exists in the stored command
        if cmd_args.lower().startswith(cmd_type.lower()):
            cmd_args = cmd_args[len(cmd_type):].strip()

        # Inject current namespace context if not already specified
        if cmd_type == "kubectl":
            cmd_args = self._inject_namespace_context(cmd_args)
        elif cmd_type == "helm":
            cmd_args = self._inject_helm_context(cmd_args)

        log_panel = self.query_one("#log-panel", LogPanel)
        full_command = f"{cmd_type} {cmd_args}"
        log_panel.write_log(f"📋 Selected from pad: {full_command}")

        # Execute the command (subprocess should capture all output)
        if cmd_type == "kubectl":
            success, output = self.k8s_manager.command_executor.execute_kubectl(cmd_args.split())
        else:
            working_dir = self._get_helm_working_directory(cmd_args)
            success, output = self.k8s_manager.command_executor.execute_helm(cmd_args.split(), cwd=working_dir)

        if success:
            # Increment usage count for this command
            self.command_history.add_command(full_command)
            # Notify all CommandPad widgets across tabs via global message
            self._notify_command_executed(full_command, cmd_type)
            log_panel.write_log("Command executed successfully")
            if output.strip():
                modal = LogModal(f"{cmd_type.title()} Output", output)
                self.app.push_screen(modal)
        else:
            log_panel.write_log(f"Command failed: {output}", "ERROR")

        self._refresh_all_data()

    @on(CommandInput.CommandEntered)
    def handle_intelligent_command(self, message):
        """Handle command from intelligent input"""
        # Update command history context
        self._update_command_history_context()

        log_panel = self.query_one("#log-panel", LogPanel)
        full_command = message.command
        cmd_type = message.command_type

        # Parse command to remove prefix
        if full_command.lower().startswith(cmd_type.lower()):
            cmd_args = full_command[len(cmd_type):].strip()
        else:
            cmd_args = full_command

        # Inject current namespace context if not already specified
        if cmd_type == "kubectl":
            cmd_args = self._inject_namespace_context(cmd_args)
        elif cmd_type == "helm":
            cmd_args = self._inject_helm_context(cmd_args)

        # Update full_command with potentially modified cmd_args
        full_command = f"{cmd_type} {cmd_args}"
        log_panel.write_log(f"🧠 Intelligent execution: {full_command}")

        if cmd_type == "kubectl":
            success, output = self.k8s_manager.command_executor.execute_kubectl(cmd_args.split())
        else:
            working_dir = self._get_helm_working_directory(cmd_args)
            success, output = self.k8s_manager.command_executor.execute_helm(cmd_args.split(), cwd=working_dir)

        if success:
            # Add to command history
            self.command_history.add_command(full_command)
            # Notify all CommandPad widgets across tabs via global message
            self._notify_command_executed(full_command, cmd_type)
            log_panel.write_log("✅ Smart command executed successfully")
            if output.strip():
                modal = LogModal(f"🧠 {cmd_type.title()} Smart Output", output)
                self.app.push_screen(modal)
        else:
            log_panel.write_log(f"❌ Smart command failed: {output}", "ERROR")

        self._refresh_all_data()
