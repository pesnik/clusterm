#!/usr/bin/env python3
"""
Test script to populate command history and test CommandPad
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.core.command_history import CommandHistoryManager
from src.core.config import Config
from src.core.logger import Logger

def populate_test_commands():
    """Add sample commands for testing CommandPad"""
    
    # Setup
    config = Config()
    logger = Logger(config)
    config_dir = Path(config.get("app.config_dir", "~/.clusterm")).expanduser()
    history_manager = CommandHistoryManager(config_dir, logger)
    
    # Sample commands to add
    sample_commands = [
        {
            "command": "kubectl get pods -n default",
            "description": "Get all pods in default namespace",
            "tags": ["kubectl", "pods", "default"]
        },
        {
            "command": "kubectl describe pod nginx-deployment",
            "description": "Describe nginx deployment pod",
            "tags": ["kubectl", "describe", "nginx"]
        },
        {
            "command": "helm list -A",
            "description": "List all Helm releases in all namespaces",
            "tags": ["helm", "list", "releases"]
        },
        {
            "command": "kubectl logs -f deployment/nginx",
            "description": "Follow logs for nginx deployment",
            "tags": ["kubectl", "logs", "nginx", "follow"]
        },
        {
            "command": "helm install nginx nginx-stable/nginx-ingress",
            "description": "Install nginx ingress controller",
            "tags": ["helm", "install", "nginx", "ingress"]
        },
        {
            "command": "kubectl get services -o wide",
            "description": "Get all services with wide output",
            "tags": ["kubectl", "services", "wide"]
        },
        {
            "command": "kubectl apply -f deployment.yaml",
            "description": "Apply deployment manifest",
            "tags": ["kubectl", "apply", "deployment"]
        },
        {
            "command": "helm upgrade nginx nginx-stable/nginx-ingress",
            "description": "Upgrade nginx ingress release",
            "tags": ["helm", "upgrade", "nginx"]
        },
        {
            "command": "kubectl port-forward svc/nginx 8080:80",
            "description": "Port forward nginx service",
            "tags": ["kubectl", "port-forward", "nginx"]
        },
        {
            "command": "kubectl get configmaps -n kube-system",
            "description": "Get configmaps in kube-system",
            "tags": ["kubectl", "configmaps", "kube-system"]
        }
    ]
    
    print("Adding sample commands to CommandPad history...")
    
    for cmd_data in sample_commands:
        history_manager.add_command(
            command=cmd_data["command"],
            description=cmd_data["description"],
            tags=cmd_data["tags"]
        )
        print(f"✅ Added: {cmd_data['command']}")
    
    # Add some usage counts to test filtering
    for i in range(5):
        history_manager.add_command("kubectl get pods -n default")
    
    for i in range(3):
        history_manager.add_command("helm list -A")
        
    for i in range(7):
        history_manager.add_command("kubectl logs -f deployment/nginx")
    
    print(f"\n✅ Successfully added {len(sample_commands)} commands to history!")
    print(f"📁 History file: {history_manager.history_file}")
    
    # Test retrieval
    all_commands = history_manager.get_all_commands()
    frequent_commands = history_manager.get_frequent_commands(5)
    
    print(f"\n📊 Statistics:")
    print(f"   Total commands: {len(all_commands)}")
    print(f"   Top 5 frequent commands: {len(frequent_commands)}")
    
    print(f"\n🔥 Most frequent commands:")
    for cmd in frequent_commands:
        print(f"   • {cmd.command} (used {cmd.usage_count} times)")

if __name__ == "__main__":
    populate_test_commands()
    print("\n🚀 Now run 'python main.py' and navigate to the Command Pad tab!")