# Architecture Documentation

This directory contains the architecture documentation for ClusterM, including Architecture Decision Records (ADRs) that capture the key design decisions made during development.

## Contents

- [ADR-0001: Modular Architecture](./ADR-0001-modular-architecture.md) - Decision to adopt a modular, layered architecture
- [ADR-0002: Plugin System](./ADR-0002-plugin-system.md) - Design of the extensible plugin system
- [ADR-0003: Event-Driven Architecture](./ADR-0003-event-driven-architecture.md) - Implementation of event bus for component communication
- [ADR-0004: Configuration Management](./ADR-0004-configuration-management.md) - Centralized configuration system design
- [ADR-0005: UI Component Architecture](./ADR-0005-ui-component-architecture.md) - Modular UI component design

## Architecture Overview

ClusterM follows a layered, modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    Main Application                      │
├─────────────────────────────────────────────────────────┤
│                   UI Layer (Textual)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Screens   │  │ Components  │  │   Modals    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│                  Core Infrastructure                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Event Bus   │  │   Config    │  │   Logger    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│                Business Logic Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │K8s Manager  │  │   Plugins   │  │ Extensions  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│                 External Interfaces                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   kubectl   │  │    helm     │  │Kubernetes   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## Design Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Dependency Inversion**: High-level modules don't depend on low-level modules
3. **Event-Driven Communication**: Loose coupling through events
4. **Extensibility**: Plugin system allows for feature extensions
5. **Testability**: Dependency injection enables comprehensive testing
6. **Configuration-Driven**: Behavior controlled through configuration
7. **Error Resilience**: Graceful error handling and recovery

## Key Patterns Used

- **Model-View-Presenter (MVP)**: Separation of UI and business logic
- **Observer Pattern**: Event bus for component communication
- **Strategy Pattern**: Plugin system for extensible functionality
- **Factory Pattern**: Component creation and initialization
- **Singleton Pattern**: Global services like logger and config
- **Command Pattern**: Action execution and undo capabilities