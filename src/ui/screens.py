"""
Screen components for the application
"""

from typing import Dict, Any, Optional
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, TabbedContent, TabPane, DataTable, Static
from textual.screen import Screen
from textual.reactive import reactive
from textual import on

from .components.tables import (
    DeploymentTable, PodTable, ServiceTable, 
    HelmReleaseTable, NamespaceTable, ResourceTable
)
from .components.panels import LogPanel, StatusPanel
from .components.modals import CommandModal, ConfigModal, LogModal, ClusterSwitchModal


class MainScreen(Screen):
    """Main application screen"""
    
    current_namespace = reactive("default")
    selected_chart = reactive(None)
    selected_resource = reactive(None)
    
    def __init__(self, k8s_manager, config, event_bus, logger, **kwargs):
        super().__init__(**kwargs)
        self.k8s_manager = k8s_manager
        self.config = config
        self.event_bus = event_bus
        self.logger = logger
        
        # Resource tables
        self.tables: Dict[str, DataTable] = {}
        
        # Subscribe to events
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup event handlers"""
        from ..core.events import EventType
        
        self.event_bus.subscribe(EventType.CLUSTER_CHANGED, self._on_cluster_changed)
        self.event_bus.subscribe(EventType.DEPLOYMENT_UPDATED, self._on_deployment_updated)
        self.event_bus.subscribe(EventType.NAMESPACE_CHANGED, self._on_namespace_changed)
    
    def compose(self):
        """Compose the main screen"""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            # Status bar
            yield StatusPanel(id="status-panel")
            
            with Horizontal(id="main-content"):
                # Left panel - Charts and actions
                with Vertical(id="charts-panel", classes="panel"):
                    with Vertical(classes="action-buttons"):
                        yield Button("🔄 Switch Cluster", id="switch-cluster-btn", classes="action-btn")
                        yield Button("🔗 Test Connection", id="test-connection-btn", classes="action-btn") 
                        yield Button("⚡ Execute Command", id="execute-command-btn", classes="action-btn")
                    
                    with Vertical(classes="charts-section"):
                        yield Static("📦 Helm Charts", classes="section-title")
                        yield DataTable(id="charts-table")
                        yield Button("🚀 Deploy Selected", variant="primary", id="deploy-chart-btn", classes="deploy-btn")
                
                # Right panel - Resource tabs
                with TabbedContent(id="resources-tabs"):
                    with TabPane("Deployments", id="deployments-tab"):
                        yield DataTable(id="deployments-table")
                        
                        with Horizontal(classes="tab-actions"):
                            yield Button("View Logs", id="deployment-logs-btn")
                            yield Button("Refresh", id="refresh-deployments-btn")
                    
                    with TabPane("Pods", id="pods-tab"):
                        yield DataTable(id="pods-table")
                        
                        with Horizontal(classes="tab-actions"):
                            yield Button("Describe", id="describe-pod-btn")
                            yield Button("Logs", id="pod-logs-btn")
                    
                    with TabPane("Services", id="services-tab"):
                        yield DataTable(id="services-table")
                        
                        with Horizontal(classes="tab-actions"):
                            yield Button("Describe", id="describe-service-btn")
                    
                    with TabPane("Helm Releases", id="helm-tab"):
                        yield DataTable(id="helm-table")
                        
                        with Horizontal(classes="tab-actions"):
                            yield Button("Status", id="helm-status-btn")
                            yield Button("History", id="helm-history-btn")
                    
                    with TabPane("Namespaces", id="namespaces-tab"):
                        yield DataTable(id="namespaces-table")
                        
                        with Horizontal(classes="tab-actions"):
                            yield Button("Set Active", id="set-namespace-btn")
            
            # Bottom panel - Logs
            yield LogPanel(id="log-panel")
        
        yield Footer()
    
    def on_mount(self):
        """Initialize the screen"""
        # Setup all tables
        self.call_after_refresh(self._setup_all_tables)
        self.call_after_refresh(self._refresh_all_data)
        self.call_after_refresh(self._update_status_panel)
        
        def log_startup():
            try:
                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log("ClusterM started successfully")
            except:
                pass
        
        self.call_after_refresh(log_startup)
    
    def _setup_charts_table(self):
        """Setup the Helm charts table"""
        try:
            charts_table = self.query_one("#charts-table", DataTable)
            charts_table.add_columns("Chart", "Version", "Description")
            
            charts = self.k8s_manager.get_available_charts()
            for chart in charts:
                description = chart["description"]
                if len(description) > 40:
                    description = description[:37] + "..."
                
                charts_table.add_row(
                    chart["name"],
                    chart["version"],
                    description
                )
        except Exception as e:
            self.logger.error(f"Error setting up charts table: {e}")
    
    def _setup_all_tables(self):
        """Setup all data tables"""
        try:
            # Setup charts table
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
            self.tables["deployments"] = deployments_table
            self.tables["pods"] = pods_table
            self.tables["services"] = services_table
            self.tables["helm"] = helm_table
            self.tables["namespaces"] = namespaces_table
            
        except Exception as e:
            self.logger.error(f"Error setting up tables: {e}")
    
    def _refresh_all_data(self):
        """Refresh all resource data"""
        try:
            if not self.tables:
                return  # Tables not set up yet
                
            # Refresh deployments
            deployments = self.k8s_manager.get_deployments()
            self._update_deployments_table(deployments)
            
            # Refresh pods
            pods = self.k8s_manager.get_pods(self.current_namespace)
            self._update_pods_table(pods)
            
            # Refresh services
            services = self.k8s_manager.get_services(self.current_namespace)
            self._update_services_table(services)
            
            # Refresh helm releases
            helm_releases = self.k8s_manager.get_helm_releases()
            self._update_helm_table(helm_releases)
            
            # Refresh namespaces
            namespaces = self.k8s_manager.get_namespaces()
            self._update_namespaces_table(namespaces)
            
            try:
                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log("Data refreshed successfully")
            except:
                pass
            
        except Exception as e:
            try:
                log_panel = self.query_one("#log-panel", LogPanel)
                log_panel.write_log(f"Error refreshing data: {str(e)}", "ERROR")
            except:
                self.logger.error(f"Error refreshing data: {e}")
    
    def _calculate_age(self, timestamp_str: str) -> str:
        """Calculate human-readable age from timestamp"""
        try:
            from datetime import datetime, timezone
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
    
    def _update_deployments_table(self, deployments):
        """Update deployments table"""
        if "deployments" not in self.tables:
            return
            
        table = self.tables["deployments"]
        table.clear()
        
        for deployment in deployments:
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
            
            table.add_row(name, status_text, replicas_str, age, namespace)
    
    def _update_pods_table(self, pods):
        """Update pods table"""
        if "pods" not in self.tables:
            return
            
        table = self.tables["pods"]
        table.clear()
        
        for pod in pods:
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
    
    def _update_services_table(self, services):
        """Update services table"""
        if "services" not in self.tables:
            return
            
        table = self.tables["services"]
        table.clear()
        
        for service in services:
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
    
    def _update_helm_table(self, releases):
        """Update helm releases table"""
        if "helm" not in self.tables:
            return
            
        table = self.tables["helm"]
        table.clear()
        
        for release in releases:
            name = release.get("name", "Unknown")
            namespace = release.get("namespace", "Unknown")
            revision = str(release.get("revision", "Unknown"))
            updated = release.get("updated", "Unknown")
            status = release.get("status", "Unknown")
            chart = release.get("chart", "Unknown")
            
            table.add_row(name, namespace, revision, updated, status, chart)
    
    def _update_namespaces_table(self, namespaces):
        """Update namespaces table"""
        if "namespaces" not in self.tables:
            return
            
        table = self.tables["namespaces"]
        table.clear()
        
        for ns in namespaces:
            name = ns["metadata"]["name"]
            phase = ns["status"]["phase"]
            age = self._calculate_age(ns["metadata"]["creationTimestamp"])
            
            table.add_row(name, phase, age)
    
    def _update_status_panel(self):
        """Update the status panel"""
        try:
            status_panel = self.query_one("#status-panel", StatusPanel)
            current_cluster = self.k8s_manager.cluster_manager.get_current_cluster()
            
            if current_cluster:
                cluster_name = current_cluster["name"]
                # Test connection
                success, _ = self.k8s_manager.cluster_manager.test_cluster_connection(cluster_name)
                status_panel.update_cluster_status(cluster_name, success)
            else:
                status_panel.update_cluster_status("No Cluster", False)
        except Exception as e:
            self.logger.error(f"Error updating status panel: {e}")
    
    def _on_resource_selected(self, resource_info: Dict[str, Any]):
        """Handle resource selection"""
        self.selected_resource = resource_info
        
        log_panel = self.query_one("#log-panel", LogPanel)
        resource_type = resource_info["type"]
        resource_name = resource_info["data"][0]  # First column is typically name
        log_panel.write_log(f"Selected {resource_type}: {resource_name}")
    
    def _on_cluster_changed(self, event):
        """Handle cluster change events"""
        self._refresh_all_data()
        self._update_status_panel()
        
        log_panel = self.query_one("#log-panel", LogPanel)
        new_cluster = event.data.get("new_cluster", "Unknown")
        log_panel.write_log(f"Switched to cluster: {new_cluster}")
    
    def _on_deployment_updated(self, event):
        """Handle deployment update events"""
        self._refresh_all_data()
        
        log_panel = self.query_one("#log-panel", LogPanel)
        chart_name = event.data.get("chart_name", "Unknown")
        action = event.data.get("action", "updated")
        log_panel.write_log(f"Deployment {action}: {chart_name}")
    
    def _on_namespace_changed(self, event):
        """Handle namespace change events"""
        new_namespace = event.data.get("namespace")
        if new_namespace:
            self.current_namespace = new_namespace
            self._refresh_all_data()
    
    # Button handlers
    @on(Button.Pressed, "#switch-cluster-btn")
    def switch_cluster(self):
        """Handle cluster switching"""
        clusters = self.k8s_manager.cluster_manager.get_available_clusters()
        current_cluster = self.k8s_manager.cluster_manager.current_cluster
        
        modal = ClusterSwitchModal(clusters, current_cluster)
        self.app.push_screen(modal, self._handle_cluster_switch_result)
    
    @on(Button.Pressed, "#test-connection-btn")
    def test_connection(self):
        """Test current cluster connection"""
        current_cluster = self.k8s_manager.cluster_manager.get_current_cluster()
        if current_cluster:
            success, message = self.k8s_manager.cluster_manager.test_cluster_connection(
                current_cluster["name"]
            )
            
            log_panel = self.query_one("#log-panel", LogPanel)
            log_panel.write_log(message, "INFO" if success else "ERROR")
            self._update_status_panel()
        else:
            log_panel = self.query_one("#log-panel", LogPanel)
            log_panel.write_log("No cluster selected", "ERROR")
    
    @on(Button.Pressed, "#execute-command-btn")
    def execute_command(self):
        """Execute kubectl/helm command"""
        modal = CommandModal()
        self.app.push_screen(modal, self._handle_command_result)
    
    @on(Button.Pressed, "#deploy-chart-btn")
    def deploy_chart(self):
        """Deploy selected chart"""
        if not self.selected_chart:
            log_panel = self.query_one("#log-panel", LogPanel)
            log_panel.write_log("Please select a chart first", "ERROR")
            return
        
        modal = ConfigModal(self.selected_chart)
        self.app.push_screen(modal, self._handle_deploy_result)
    
    def _handle_cluster_switch_result(self, result):
        """Handle cluster switch modal result"""
        if not result:
            return
        
        action, cluster_name = result
        log_panel = self.query_one("#log-panel", LogPanel)
        
        if action == "switch" and cluster_name:
            if self.k8s_manager.cluster_manager.set_current_cluster(cluster_name):
                log_panel.write_log(f"Switched to cluster: {cluster_name}")
            else:
                log_panel.write_log(f"Failed to switch to cluster: {cluster_name}", "ERROR")
        
        elif action == "test" and cluster_name:
            success, message = self.k8s_manager.cluster_manager.test_cluster_connection(cluster_name)
            log_panel.write_log(message, "INFO" if success else "ERROR")
    
    def _handle_command_result(self, result):
        """Handle command execution result"""
        if not result or result[0] == "cancel":
            return
        
        action, cmd_type, cmd_args = result
        log_panel = self.query_one("#log-panel", LogPanel)
        log_panel.write_log(f"Executing {cmd_type} {cmd_args}")
        
        if cmd_type == "kubectl":
            success, output = self.k8s_manager.command_executor.execute_kubectl(cmd_args.split())
        else:
            success, output = self.k8s_manager.command_executor.execute_helm(cmd_args.split())
        
        if success:
            log_panel.write_log("Command executed successfully")
            if output.strip():
                modal = LogModal(f"{cmd_type.title()} Output", output)
                self.app.push_screen(modal)
        else:
            log_panel.write_log(f"Command failed: {output}", "ERROR")
        
        self._refresh_all_data()
    
    def _handle_deploy_result(self, result):
        """Handle deployment configuration result"""
        if not result or result[0] == "cancel":
            return
        
        action, chart_name, config = result
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
        charts_table = self.query_one("#charts-table", DataTable)
        row_data = charts_table.get_row_at(event.row_index)
        self.selected_chart = str(row_data[0])
        
        log_panel = self.query_one("#log-panel", LogPanel)
        log_panel.write_log(f"Selected chart: {self.selected_chart}")