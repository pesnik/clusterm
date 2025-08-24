"""
Tests for cluster management
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from src.k8s.cluster import ClusterManager


class TestClusterManager:
    """Test cluster management functionality"""
    
    def test_discover_clusters(self, mock_k8s_paths, mock_event_bus, mock_logger):
        """Test cluster discovery"""
        clusters_path = mock_k8s_paths["clusters_path"]
        
        # Create mock cluster directory with kubeconfig
        cluster_dir = clusters_path / "test-cluster"
        cluster_dir.mkdir()
        kubeconfig = cluster_dir / "kubeconfig.yaml"
        kubeconfig.write_text("apiVersion: v1\nkind: Config")
        
        # Initialize cluster manager
        manager = ClusterManager(clusters_path, mock_event_bus, mock_logger)
        
        # Verify cluster was discovered
        assert "test-cluster" in manager.clusters
        assert manager.clusters["test-cluster"]["kubeconfig"] == kubeconfig
    
    def test_set_current_cluster(self, mock_k8s_paths, mock_event_bus, mock_logger):
        """Test setting current cluster"""
        clusters_path = mock_k8s_paths["clusters_path"]
        
        # Create mock cluster
        cluster_dir = clusters_path / "test-cluster"
        cluster_dir.mkdir()
        (cluster_dir / "config").write_text("mock config")
        
        manager = ClusterManager(clusters_path, mock_event_bus, mock_logger)
        
        # Set current cluster
        result = manager.set_current_cluster("test-cluster")
        
        assert result == True
        assert manager.current_cluster == "test-cluster"
        
        # Verify event was emitted
        mock_event_bus.emit_sync.assert_called()
    
    def test_get_current_kubeconfig(self, mock_k8s_paths, mock_event_bus, mock_logger):
        """Test getting current kubeconfig"""
        clusters_path = mock_k8s_paths["clusters_path"]
        
        # Create mock cluster
        cluster_dir = clusters_path / "test-cluster"
        cluster_dir.mkdir()
        kubeconfig = cluster_dir / "kubeconfig.yaml"
        kubeconfig.write_text("mock config")
        
        manager = ClusterManager(clusters_path, mock_event_bus, mock_logger)
        manager.set_current_cluster("test-cluster")
        
        # Get current kubeconfig
        current_config = manager.get_current_kubeconfig()
        
        assert current_config == kubeconfig
    
    @patch('subprocess.run')
    def test_test_cluster_connection(self, mock_run, mock_k8s_paths, mock_event_bus, mock_logger):
        """Test cluster connection testing"""
        clusters_path = mock_k8s_paths["clusters_path"]
        
        # Create mock cluster
        cluster_dir = clusters_path / "test-cluster"
        cluster_dir.mkdir()
        (cluster_dir / "config").write_text("mock config")
        
        # Mock successful kubectl response
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Kubernetes master is running"
        mock_run.return_value.stderr = ""
        
        manager = ClusterManager(clusters_path, mock_event_bus, mock_logger)
        
        # Test connection
        success, message = manager.test_cluster_connection("test-cluster")
        
        assert success == True
        assert "Connected" in message