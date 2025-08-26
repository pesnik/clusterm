"""Core exceptions for ClusterM
"""

class ClusterMError(Exception):
    """Base exception class for ClusterM"""



class ConfigError(ClusterMError):
    """Configuration related errors"""



class K8sError(ClusterMError):
    """Kubernetes operation errors"""



class PluginError(ClusterMError):
    """Plugin system errors"""



class UIError(ClusterMError):
    """UI related errors"""

