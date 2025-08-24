"""
Core exceptions for ClusterM
"""

class ClusterMError(Exception):
    """Base exception class for ClusterM"""
    pass


class ConfigError(ClusterMError):
    """Configuration related errors"""
    pass


class K8sError(ClusterMError):
    """Kubernetes operation errors"""
    pass


class PluginError(ClusterMError):
    """Plugin system errors"""
    pass


class UIError(ClusterMError):
    """UI related errors"""
    pass