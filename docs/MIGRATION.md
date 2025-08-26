# Migration Guide: Cluster-Aware Project Structure

This guide helps you migrate from the old flat project structure to the new cluster-aware organization introduced in Clusterm v0.4.0.

## What Changed

### Old Structure (v0.3.x and earlier)
```
~/.clusterm/k8s/
├── clusters/
│   ├── production/
│   │   └── kubeconfig
│   └── staging/
│       └── kubeconfig
└── projects/
    └── helm-charts/         # All charts mixed together
        ├── nginx-app/       # Which cluster? Which namespace?
        ├── postgres-db/     # Production or staging?
        ├── monitoring/      # Not clear where it belongs
        └── api-gateway/     # Could be deployed anywhere
```

### New Structure (v0.4.0+)
```
~/.clusterm/k8s/
├── clusters/
│   ├── production/
│   │   ├── kubeconfig
│   │   └── projects/        # Production-specific projects
│   │       ├── default/     # Default namespace projects
│   │       │   ├── nginx-app/
│   │       │   └── api-gateway/
│   │       ├── monitoring/  # Monitoring namespace projects
│   │       │   └── prometheus-stack/
│   │       └── ingress/     # Ingress namespace projects
│   │           └── nginx-ingress/
│   └── staging/
│       ├── kubeconfig
│       └── projects/        # Staging-specific projects
│           ├── default/     # Staging default namespace
│           │   └── test-app/
│           └── development/ # Development namespace
│               └── debug-tools/
└── tools/
    ├── kubectl
    └── helm
```

## Migration Steps

### Step 1: Backup Your Current Setup
```bash
# Create backup of your current structure
cp -r ~/.clusterm/k8s ~/.clusterm/k8s-backup-$(date +%Y%m%d)
```

### Step 2: Understand Your Current Projects
```bash
# List your current Helm charts
ls ~/.clusterm/k8s/projects/helm-charts/

# For each chart, determine:
# 1. Which cluster(s) it belongs to
# 2. Which namespace it should deploy to
# 3. Environment-specific configurations
```

### Step 3: Create New Directory Structure

**Option A: Automatic Migration (Recommended)**

Create a migration script:

```bash
#!/bin/bash
# migrate-projects.sh

OLD_PROJECTS="$HOME/.clusterm/k8s/projects/helm-charts"
CLUSTERS_DIR="$HOME/.clusterm/k8s/clusters"

# Check if old structure exists
if [ ! -d "$OLD_PROJECTS" ]; then
    echo "No old projects found to migrate"
    exit 0
fi

echo "🔄 Migrating Helm charts to cluster-aware structure..."

# Create example structure for each cluster
for cluster_dir in "$CLUSTERS_DIR"/*; do
    if [ -d "$cluster_dir" ]; then
        cluster_name=$(basename "$cluster_dir")
        echo "📁 Setting up cluster: $cluster_name"
        
        # Create namespace directories
        mkdir -p "$cluster_dir/projects/"{default,monitoring,ingress,development}
        
        echo "  ✅ Created namespace directories"
    fi
done

echo ""
echo "📋 Manual Migration Required:"
echo "Your old charts are still in: $OLD_PROJECTS"
echo ""
echo "For each chart, decide which cluster(s) and namespace(s) it belongs to:"
ls "$OLD_PROJECTS" | while read chart; do
    echo "  📦 $chart"
    echo "      → Move to: clusters/{CLUSTER}/projects/{NAMESPACE}/$chart"
done

echo ""
echo "Example commands:"
echo "# Move nginx-app to production/default"
echo "mv '$OLD_PROJECTS/nginx-app' '$CLUSTERS_DIR/production/projects/default/'"
echo ""
echo "# Move monitoring stack to production/monitoring"
echo "mv '$OLD_PROJECTS/prometheus' '$CLUSTERS_DIR/production/projects/monitoring/'"
echo ""
echo "# Copy shared charts to multiple clusters"
echo "cp -r '$OLD_PROJECTS/shared-app' '$CLUSTERS_DIR/production/projects/default/'"
echo "cp -r '$OLD_PROJECTS/shared-app' '$CLUSTERS_DIR/staging/projects/default/'"
```

**Option B: Manual Migration**

For each cluster you have:

```bash
# Example: Migrate to production cluster
CLUSTER="production"
mkdir -p ~/.clusterm/k8s/clusters/$CLUSTER/projects/{default,monitoring,ingress}

# Move production-specific charts
mv ~/.clusterm/k8s/projects/helm-charts/nginx-app \
   ~/.clusterm/k8s/clusters/$CLUSTER/projects/default/

mv ~/.clusterm/k8s/projects/helm-charts/prometheus \
   ~/.clusterm/k8s/clusters/$CLUSTER/projects/monitoring/

# For staging cluster
CLUSTER="staging"  
mkdir -p ~/.clusterm/k8s/clusters/$CLUSTER/projects/{default,development}

# Copy or move staging charts
cp -r ~/.clusterm/k8s/projects/helm-charts/test-app \
      ~/.clusterm/k8s/clusters/$CLUSTER/projects/default/
```

### Step 4: Update Chart Configurations

You may need to update your charts for environment-specific values:

**Before (single values.yaml):**
```yaml
# values.yaml
replicaCount: 1  # Same for all environments
image:
  tag: latest    # Same tag everywhere
resources: {}    # No resource limits
```

**After (environment-aware):**
```yaml
# Production: clusters/production/projects/default/my-app/values.yaml
replicaCount: 3
image:
  tag: "v1.2.3"  # Stable tag
resources:
  limits:
    memory: "1Gi"
    cpu: "500m"

# Staging: clusters/staging/projects/default/my-app/values.yaml  
replicaCount: 1
image:
  tag: "latest"  # Latest for testing
resources:
  limits:
    memory: "512Mi"
    cpu: "250m"
```

### Step 5: Test the Migration

1. **Launch Clusterm:**
   ```bash
   python main.py
   ```

2. **Switch between clusters/namespaces:**
   - Use the context selector dropdowns
   - Verify that charts only show for the selected context

3. **Deploy a test chart:**
   - Select production + default namespace
   - Should only see production/default charts
   - Deploy one to verify it works

4. **Verify isolation:**
   - Switch to staging + development namespace  
   - Should see completely different set of charts

### Step 6: Clean Up (Optional)

Once you've verified everything works:

```bash
# Remove old projects directory
rm -rf ~/.clusterm/k8s/projects/helm-charts

# Remove backup after confirming everything works
rm -rf ~/.clusterm/k8s-backup-*
```

## Benefits After Migration

### ✅ Context Filtering
- Charts automatically filtered by cluster/namespace selection
- No more irrelevant charts cluttering your workspace

### ✅ Environment Safety  
- Impossible to accidentally deploy staging charts to production
- Clear visual separation between environments

### ✅ Team Organization
- Different teams can manage different namespaces
- Clear ownership boundaries

### ✅ Scalability
- Easily add new clusters without affecting existing ones
- Namespace-level organization scales with your infrastructure

## Troubleshooting

### Charts Not Showing
- **Check cluster selection:** Ensure you've selected the right cluster
- **Check namespace:** Charts only appear for the selected namespace
- **Verify structure:** Charts should be in `clusters/{cluster}/projects/{namespace}/{chart}/`
- **Check Chart.yaml:** Each chart directory needs a valid `Chart.yaml` file

### Deploy Failures
- **Wrong cluster:** Verify you're connected to the intended cluster
- **Namespace mismatch:** Deployment namespace should match the chart's location
- **Values conflicts:** Different environments may need different values.yaml

### Can't Find Old Charts
- **Check backup:** Your backup is in `~/.clusterm/k8s-backup-{date}`
- **Old location:** Original charts may still be in `~/.clusterm/k8s/projects/helm-charts/`

## Migration Verification Checklist

- [ ] **Backup created** - Old structure safely backed up
- [ ] **Charts moved** - All charts moved to appropriate cluster/namespace directories
- [ ] **Structure verified** - New directory structure matches expected layout
- [ ] **App launches** - Clusterm starts without errors
- [ ] **Context switching** - Can switch between clusters and namespaces
- [ ] **Chart filtering** - Charts appear only for selected context
- [ ] **Deployment tested** - Successfully deployed at least one chart
- [ ] **Isolation verified** - Different contexts show different charts
- [ ] **Team informed** - Team members know about new structure

## Getting Help

If you encounter issues during migration:

1. **Check logs:** `~/.clusterm/logs/clusterm.log`
2. **Enable debug:** Set `log_level: DEBUG` in config
3. **Verify structure:** Compare with example structure in README
4. **Restore backup:** If needed, restore from backup and try again

For additional support, please open an issue on the GitHub repository with:
- Your current directory structure
- Migration steps you've tried
- Error messages or logs
- Expected vs actual behavior