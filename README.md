# Clusterm

A comprehensive Terminal User Interface (TUI) for Kubernetes cluster management that bridges the gap between complex command-line operations and user-friendly interfaces.

### Overview

Clusterm transforms Kubernetes management into an intuitive, visual experience. Built for DevOps teams where technical and non-technical members need to collaborate on cluster operations, it provides a comprehensive dashboard for deployments, pods, services, and Helm releases across multiple clusters.

-----

### Key Features

**Multi-Cluster Management**

  * **Auto-discovery** of clusters from directory structure
  * Seamless switching between **development, staging, and production** environments
  * **Connection testing** and cluster health validation
  * **Dynamic kubeconfig handling** per cluster

**Comprehensive Resource Views**

  * **Deployments:** Status, replicas, age, and namespace information
  * **Pods:** Phase, readiness, restart counts, and node assignments
  * **Services:** Types, IPs, ports, and load balancer status
  * **Helm Releases:** Versions, revisions, and deployment history
  * **Namespaces:** Status and resource organization

**Interactive Operations**

  * **Command Execution:** Run arbitrary `kubectl`/`helm` commands through the UI
  * **Resource Description:** Detailed information about any selected resource
  * **Log Viewing:** Real-time and historical log access
  * **Helm Management:** Deploy, upgrade, rollback, and status checking
  * **Namespace Switching:** Context-aware resource filtering

**User-Friendly Interface**

  * **Tabbed Layout:** Organized resource views
  * **Keyboard Shortcuts:** Efficient navigation and operations
  * **Real-time Updates:** Live status monitoring
  * **Visual Status Indicators:** Clear health and state representation

-----

### Installation

#### Prerequisites

  * Python 3.8 or higher
  * `kubectl` binary
  * Helm 3.x (optional, for Helm operations)
  * Access to Kubernetes cluster(s)

#### Install Dependencies

```bash
pip install textual PyYAML
```

#### Download and Setup

```bash
git clone https://github.com/pesnik/clusterm.git
cd clusterm
chmod +x clusterm.py
```

-----

### Directory Structure

Clusterm expects the following directory structure:

```
/app/
├── k8s/
│   ├── clusters/
│   │   ├── production/
│   │   │   └── prod-kubeconfig.yaml
│   │   ├── staging/
│   │   │   └── staging-kubeconfig.yaml
│   │   └── development/
│   │       └── dev-kubeconfig.yaml
│   ├── projects/
│   │   └── helm-charts/
│   │       ├── webapp/
│   │       ├── api-service/
│   │       └── monitoring/
│   └── tools/
│       ├── kubectl
│       └── linux-amd64/
│           └── helm
└── clusterm.py
```

-----

### Usage

#### Starting Clusterm

```bash
python clusterm.py
# or specify a custom path
python clusterm.py /path/to/your/k8s/directory
```

#### Keyboard Shortcuts

  * `q` - Quit application
  * `r` - Refresh all resource data
  * `d` - Deploy selected Helm chart
  * `l` - View logs for selected resource
  * `c` - Switch between available clusters
  * `t` - Test cluster connection
  * `x` - Execute custom `kubectl`/`helm` command

#### Basic Workflow

1.  **Select Cluster:** Use `c` or click "Switch Cluster" to choose your target environment.
2.  **Browse Resources:** Navigate through tabs to explore deployments, pods, services, etc.
3.  **Select Resources:** Click on any resource to select it for operations.
4.  **Execute Operations:** Use buttons or shortcuts to describe, view logs, or manage resources.
5.  **Deploy Applications:** Select a Helm chart and press `d` for a guided deployment.
6.  **Run Commands:** Press `x` to execute any `kubectl` or `helm` command through the UI.

-----

### Configuration

#### Adding New Clusters

1.  Create a directory in `k8s/clusters/[cluster-name]/`.
2.  Place your kubeconfig file in that directory.
3.  Restart Clusterm—it will auto-discover the new cluster.

#### Adding Helm Charts

1.  Place your Helm charts in `k8s/projects/helm-charts/[chart-name]/`.
2.  Ensure each chart has a valid `Chart.yaml` and `values.yaml`.
3.  Charts will appear automatically in the deployment interface.

#### Command Execution

The command execution feature (`x` key) allows running any `kubectl` or `helm` command:

```
# kubectl Examples
get pods --all-namespaces
describe deployment webapp
logs -f pod-name
scale deployment webapp --replicas=5
```

```
# Helm Examples
list --all-namespaces
status webapp-production
history webapp-production
rollback webapp-production 2
```

-----

### Deployment Management

Clusterm provides a guided deployment interface for Helm charts:

1.  Select a chart from the left panel.
2.  Press `d` or click "Deploy Selected".
3.  Configure deployment parameters:
      * **Namespace:** Target namespace (created if it doesn't exist)
      * **Replicas:** Number of pod replicas
      * **Environment:** `dev`/`staging`/`production`
      * **Monitoring:** Enable/disable monitoring stack
4.  Click "Deploy" to execute.

-----

### Monitoring and Logs

  * **Real-time Monitoring:** Resource status updates automatically with visual health indicators, age and uptime tracking, and replica counts.
  * **Log Access:** View logs for pods, deployments, and other resources.

-----

### Troubleshooting

  * **`kubectl` not found:** Ensure the binary is executable (`chmod +x k8s/tools/kubectl`).
  * **Helm binary not found:** Unzip the binary into the `k8s/tools/linux-amd64/` directory.
  * **Cluster connection failed:** Verify the kubeconfig file and check network connectivity.
  * **No resources visible:** Check your current namespace and RBAC permissions.

-----

### Development

  * **Architecture:** `K8sManager` handles commands, `ClusterManager` handles cluster discovery, and `TUI Components` manage the interface.
  * **Extending Functionality:** The codebase is structured for easy extension, allowing you to add new resource types, command handlers, and deployment workflows.
  * **Contributing:** Fork the repository, create a feature branch, add tests, and submit a pull request.

-----

### Security Considerations

  * Store kubeconfig files with appropriate permissions (`600`).
  * Use RBAC to limit cluster access scope.
  * Audit command execution logs for security compliance.

-----

### License

MIT License - see LICENSE file for details

### Support

  * **Issues:** GitHub Issues
  * **Documentation:** Wiki
  * **Community:** Discussions

Built for DevOps teams who value both power and usability in their Kubernetes management tools.
