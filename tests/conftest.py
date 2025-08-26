"""
Pytest configuration and fixtures
"""


import pytest

from src.core.config import Config
from src.core.events import EventBus
from src.core.logger import Logger


@pytest.fixture
def temp_config_dir(tmp_path):
    """Temporary configuration directory"""
    config_dir = tmp_path / ".clusterm"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def mock_config(temp_config_dir):
    """Mock configuration for testing"""
    config = Config(temp_config_dir / "config.yaml")
    return config


@pytest.fixture
def mock_event_bus():
    """Mock event bus for testing"""
    return EventBus()


@pytest.fixture
def mock_logger():
    """Mock logger for testing"""
    return Logger()


@pytest.fixture
def mock_k8s_paths(tmp_path):
    """Mock K8s directory structure"""
    k8s_path = tmp_path / "k8s"
    k8s_path.mkdir()

    # Create clusters directory
    clusters_path = k8s_path / "clusters"
    clusters_path.mkdir()

    # Create tools directory
    tools_path = k8s_path / "tools"
    tools_path.mkdir()

    # Create mock kubectl
    kubectl = tools_path / "kubectl"
    kubectl.write_text("#!/bin/bash\necho 'mock kubectl'")
    kubectl.chmod(0o755)

    # Create helm charts directory
    charts_path = k8s_path / "projects" / "helm-charts"
    charts_path.mkdir(parents=True)

    return {
        "k8s_path": k8s_path,
        "clusters_path": clusters_path,
        "tools_path": tools_path,
        "charts_path": charts_path
    }
