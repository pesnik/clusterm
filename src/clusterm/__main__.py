#!/usr/bin/env python3
"""
Clusterm - Kubernetes Deployment Manager TUI
Main entry point for the clusterm package
"""

import sys
from pathlib import Path

from .ui.app import ClustermApp


def main():
    """Main entry point"""
    # Parse command line arguments
    config_path = None
    if len(sys.argv) > 1:
        config_path = Path(sys.argv[1])

    # Create and run the application
    try:
        app = ClustermApp(config_path)
        app.run()
    except KeyboardInterrupt:
        print("\nExiting Clusterm...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting Clusterm: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()