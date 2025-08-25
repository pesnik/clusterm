#!/usr/bin/env python3
"""
Demo and test script for Clusterm's Intelligent Command Input features
Showcases the production-grade prompt_toolkit integration
"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.ui.components.intelligent_command_input import KubectlHelmCompleter, KubectlHelmValidator
from src.core.live_completions import LiveCompletionProvider
from src.core.command_history import CommandHistoryManager
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document
from prompt_toolkit.styles import Style
from pathlib import Path
import tempfile


class MockK8sManager:
    """Mock K8s manager for demo purposes"""
    
    def __init__(self):
        self.current_namespace = "default"
        self.cluster_manager = MockClusterManager()
    
    def get_namespaces(self):
        return [
            {"metadata": {"name": "default"}},
            {"metadata": {"name": "kube-system"}},
            {"metadata": {"name": "production"}},
            {"metadata": {"name": "development"}},
            {"metadata": {"name": "staging"}}
        ]
    
    def get_pods(self, namespace=None):
        return [
            {"metadata": {"name": "nginx-deployment-7d5c4f5b8c-abc123"}},
            {"metadata": {"name": "redis-master-6b8f5c7d9e-def456"}},
            {"metadata": {"name": "postgres-db-5a7b6c8d9f-ghi789"}},
            {"metadata": {"name": "api-server-8c9d0e1f2a-jkl012"}}
        ]
    
    def get_services(self, namespace=None):
        return [
            {"metadata": {"name": "nginx-service"}},
            {"metadata": {"name": "redis-service"}},
            {"metadata": {"name": "postgres-service"}},
            {"metadata": {"name": "api-service"}}
        ]
    
    def get_deployments(self):
        return [
            {"metadata": {"name": "nginx-deployment"}},
            {"metadata": {"name": "redis-master"}},
            {"metadata": {"name": "postgres-db"}},
            {"metadata": {"name": "api-server"}}
        ]
    
    def get_helm_releases(self):
        return [
            {"name": "my-nginx"},
            {"name": "redis-cluster"},
            {"name": "postgresql"},
            {"name": "prometheus"}
        ]


class MockClusterManager:
    """Mock cluster manager for demo"""
    
    def get_current_cluster(self):
        return {"name": "demo-cluster"}


def demo_completions():
    """Demo the completion system"""
    print("🧠 Intelligent Command Input - Completion Demo")
    print("=" * 50)
    
    # Create mock components
    with tempfile.TemporaryDirectory() as tmpdir:
        history_manager = CommandHistoryManager(Path(tmpdir))
        k8s_manager = MockK8sManager()
        
        # Add some sample commands to history
        sample_commands = [
            "kubectl get pods --all-namespaces",
            "kubectl describe pod nginx-deployment-7d5c4f5b8c-abc123",
            "kubectl logs redis-master-6b8f5c7d9e-def456 -f",
            "helm list --all-namespaces",
            "helm status my-nginx",
            "kubectl get services -n production"
        ]
        
        for cmd in sample_commands:
            history_manager.add_command(cmd, f"Demo command: {cmd}")
        
        # Create completer
        completer = KubectlHelmCompleter(history_manager, k8s_manager)
        
        # Test various completion scenarios
        test_cases = [
            ("", "Empty input - should suggest common commands"),
            ("kubectl", "kubectl - should suggest subcommands"),
            ("kubectl get", "kubectl get - should suggest resources"),
            ("kubectl get po", "kubectl get po - should suggest pod names"),
            ("kubectl logs ", "kubectl logs - should suggest pod names"),
            ("helm", "helm - should suggest subcommands"),
            ("helm list", "helm list - should suggest flags"),
            ("kubectl get pods -n ", "kubectl get pods -n - should suggest namespaces"),
            ("kubectl get pods -o ", "kubectl get pods -o - should suggest output formats")
        ]
        
        for input_text, description in test_cases:
            print(f"\n📝 Test: {description}")
            print(f"   Input: '{input_text}'")
            
            # Create document and get completions
            document = Document(input_text, len(input_text))
            completions = list(completer.get_completions(document, CompleteEvent()))
            
            print(f"   Completions ({len(completions)}):")
            for i, completion in enumerate(completions[:5]):  # Show first 5
                print(f"     {i+1}. {completion.text}")
            if len(completions) > 5:
                print(f"     ... and {len(completions) - 5} more")


def demo_validation():
    """Demo the validation system"""
    print("\n🔍 Intelligent Command Input - Validation Demo")
    print("=" * 50)
    
    k8s_manager = MockK8sManager()
    validator = KubectlHelmValidator(k8s_manager)
    
    test_cases = [
        ("kubectl get pods", "✅ Valid kubectl command"),
        ("helm list", "✅ Valid helm command"),
        ("kubectl invalid-subcommand", "❌ Invalid kubectl subcommand"),
        ("helm unknown-command", "❌ Invalid helm subcommand"),
        ("kubectl get", "⚠️ Incomplete kubectl command"),
        ("random-command", "❌ Unknown command"),
        ("kubectl", "⚠️ Incomplete command")
    ]
    
    for command, expected in test_cases:
        print(f"\n📝 Test: {expected}")
        print(f"   Command: '{command}'")
        
        document = Document(command)
        try:
            validator.validate(document)
            print("   Result: ✅ Valid")
        except Exception as e:
            print(f"   Result: ❌ {e}")


async def demo_interactive_session():
    """Demo an interactive prompt_toolkit session"""
    print("\n🚀 Interactive Intelligent Input Demo")
    print("=" * 50)
    print("Starting interactive session with all intelligent features...")
    print("Features enabled:")
    print("  • Tab completion with live cluster data")
    print("  • ↑/↓ command history navigation")
    print("  • Real-time validation")
    print("  • Context-aware suggestions")
    print("  • Syntax highlighting")
    print("\nType 'exit' or press Ctrl+C to quit")
    print("-" * 50)
    
    # Setup components
    with tempfile.TemporaryDirectory() as tmpdir:
        history_manager = CommandHistoryManager(Path(tmpdir))
        k8s_manager = MockK8sManager()
        
        # Pre-populate with realistic commands
        realistic_commands = [
            "kubectl get pods --all-namespaces",
            "kubectl get services -n production",
            "kubectl describe deployment nginx-deployment",
            "kubectl logs nginx-deployment-7d5c4f5b8c-abc123 -f",
            "kubectl exec -it redis-master-6b8f5c7d9e-def456 -- /bin/bash",
            "helm list --all-namespaces",
            "helm status my-nginx -n production",
            "helm upgrade my-nginx ./chart --set image.tag=v2.0",
            "kubectl get nodes -o wide",
            "kubectl top pods --sort-by=memory"
        ]
        
        for cmd in realistic_commands:
            history_manager.add_command(cmd)
        
        # Create intelligent session
        completer = KubectlHelmCompleter(history_manager, k8s_manager)
        validator = KubectlHelmValidator(k8s_manager)
        
        style = Style.from_dict({
            'command': '#00aa00 bold',      # Green for kubectl/helm
            'subcommand': '#0066cc bold',   # Blue for subcommands
            'resource': '#cc6600',          # Orange for resources
            'flag': '#6600cc',              # Purple for flags
            'error': '#cc0000 bold',        # Red for errors
            'suggestion': '#666666 italic'  # Gray for suggestions
        })
        
        session = PromptSession(
            message=[('class:command', '🧠 clusterm> ')],
            completer=completer,
            validator=validator,
            validate_while_typing=True,
            style=style,
            complete_style='multi-column',
            mouse_support=True,
            enable_history_search=True,
            search_ignore_case=True
        )
        
        try:
            while True:
                try:
                    command = await session.prompt_async()
                    command = command.strip()
                    
                    if command.lower() in ['exit', 'quit']:
                        break
                    
                    if command:
                        print(f"✅ Would execute: {command}")
                        # Add to history for future completions
                        history_manager.add_command(command)
                    
                except KeyboardInterrupt:
                    break
                except EOFError:
                    break
        
        except Exception as e:
            print(f"Session error: {e}")
        
        print("\n👋 Interactive session ended")


def demo_live_completions():
    """Demo the live completion provider"""
    print("\n📡 Live Completions Provider Demo")
    print("=" * 50)
    
    k8s_manager = MockK8sManager()
    provider = LiveCompletionProvider(k8s_manager)
    
    print("Context Information:")
    context = provider.get_context_info()
    for key, value in context.items():
        print(f"  {key}: {value}")
    
    print("\nAvailable Completions:")
    
    resource_types = ['pods', 'services', 'deployments', 'namespaces']
    for resource_type in resource_types:
        completions = provider.get_completions(resource_type)
        print(f"  {resource_type}: {', '.join(completions[:3])}{'...' if len(completions) > 3 else ''}")
    
    print(f"\nKubectl Resources: {len(provider.get_kubectl_resources())} available")
    print(f"Output Formats: {', '.join(provider.get_output_formats()[:5])}...")
    print(f"Field Selectors: {', '.join(provider.get_field_selectors()[:3])}...")


def main():
    """Main demo function"""
    print("🧠 Clusterm Intelligent Command Input - Complete Feature Demo")
    print("=" * 70)
    print("This demonstrates the production-grade prompt_toolkit integration")
    print("with real-time completions, validation, and context awareness.")
    print("=" * 70)
    
    # Run demos
    demo_completions()
    demo_validation() 
    demo_live_completions()
    
    # Ask for interactive demo
    response = input("\n🚀 Would you like to try the interactive demo? (y/N): ")
    if response.lower() == 'y':
        try:
            asyncio.run(demo_interactive_session())
        except Exception as e:
            print(f"Interactive demo error: {e}")
    
    print("\n✨ Demo completed!")
    print("\nTo use in Clusterm:")
    print("1. Launch Clusterm: python main.py")
    print("2. Press Ctrl+I or go to 'Smart Input' tab")
    print("3. Enjoy intelligent command completion! 🎉")


if __name__ == "__main__":
    main()