#!/usr/bin/env python3
"""
ClusterM - Kubernetes Deployment Manager TUI
A modular, extensible interface for managing Kubernetes deployments
"""

import sys
from pathlib import Path
from src.ui.app import ClusterMApp


def main():
    """Main entry point"""
    # Parse command line arguments
    config_path = None
    if len(sys.argv) > 1:
        config_path = Path(sys.argv[1])
    
    # Create and run the application
    try:
        app = ClusterMApp(config_path)
        app.run()
    except KeyboardInterrupt:
        print("\nExiting ClusterM...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting ClusterM: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()