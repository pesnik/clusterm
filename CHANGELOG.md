# Changelog

All notable changes to Clusterm will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.3.0] - 2025-08-25

### Changes
- feat: Add intelligent command input with prompt_toolkit integration
- Release v0.2.0: Command Pad Intelligence
- fix: modal opened on center
- Refactor monolithic TUI into robust modular architecture
- Update README.md
## [0.2.0] - 2025-08-25

### 🚀 Added
- **Command Pad**: Revolutionary context-aware command history system
  - Commands stored per cluster and namespace combination
  - Smart usage frequency tracking and analytics
  - Real-time search and filtering capabilities
  - Multiple view modes (Frequent, Recent, All Commands)
- **Smart Command Execution**: Auto-detection of kubectl/helm commands
  - No more manual command type selection
  - Intelligent parsing of command prefixes
  - Natural command entry workflow
- **Context-Aware Storage**: Production-grade command management
  - Zero noise - only relevant commands per environment
  - Automatic context switching on cluster/namespace changes
  - Legacy data migration support
- **Enhanced UI/UX**:
  - Improved modal positioning and centering
  - Better button layouts with emoji icons
  - Comprehensive escape key handling
  - Real-time command pad updates

### 🔧 Changed
- Renamed application from "ClusterM" to "Clusterm" for better branding
- Updated execute command modal to remove dropdown selection
- Enhanced error handling and diagnostic messages
- Improved application title with version display

### 🏗️ Architecture
- Introduced modular command history management system
- Event-driven command pad updates
- Context-aware data persistence
- Production-ready configuration management

### 📖 Documentation
- Updated README with Command Pad feature showcase
- Added comprehensive usage instructions
- Updated project structure documentation
- Enhanced feature descriptions and benefits

## [0.1.0] - 2025-08-24

### 🚀 Added
- Initial release with modular TUI architecture
- Multi-cluster Kubernetes management
- Resource monitoring (deployments, pods, services, namespaces)
- Helm chart integration and deployment
- Plugin system for extensibility
- Event-driven architecture
- Comprehensive logging system
- Testing framework with pytest
- Configuration management system

### 🏗️ Architecture
- Modular design with separation of concerns
- Plugin-based extensibility
- Event bus for component communication
- Centralized configuration management
- Structured logging infrastructure

### 📖 Documentation
- Architecture Decision Records (ADRs)
- Comprehensive README
- Plugin development guide
- Project structure documentation

---

## Version Numbering

Clusterm follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions  
- **PATCH** version for backwards-compatible bug fixes

## Release Process

1. Update version in `src/__version__.py`
2. Update `CHANGELOG.md` with release notes
3. Create git tag: `git tag v0.2.0`
4. Push changes: `git push origin main --tags`