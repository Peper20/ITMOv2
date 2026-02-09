# ITMO "AI-инструменты в жизни инженера" Constitution

## Core Principles

### I. Russian Language Priority
All educational materials MUST be in Russian to ensure maximum comprehension for the target audience.
-   **Educational Content**: Guides, READMEs, lectures MUST be in Russian.
-   **Code Comments**: In-code documentation and comments MUST be in Russian.
-   **Technical Terms**: Standard English technical terms (e.g., "User Story", "Pull Request", "Endpoint") SHOULD be kept in English or transliterated with English in brackets upon first use.
-   **Code**: Variable names, function names, and syntax MUST remain in English.

### II. Library-First Development
Every functional module SHOULD be designed as a standalone library before being integrated into the main application.
-   **Independence**: Libraries MUST be testable in isolation.
-   **Documentation**: Each library MUST have its own README and interface documentation.
-   **Reusability**: Code should be structured to be reusable across different contexts (e.g., CLI vs Web).

### III. CLI Interface Standard
Every core library or module MUST expose its functionality via a Command Line Interface (CLI).
-   **Interactivity**: Enables manual testing and experimentation without running the full web server.
-   **Automation**: Facilitates scripting and integration into pipelines.
-   **Formats**: CLI SHOULD support both human-readable text and structured JSON output for chaining.

### IV. Test-First Development (TDD)
Development MUST follow the Test-Driven Development cycle (Red-Green-Refactor) where applicable.
-   **Tests First**: Write the test before the implementation.
-   **Coverage**: Aim for high test coverage (>90%) for core business logic.
-   **Educational Value**: Demonstrates professional engineering practices to students.

### V. Integration Testing Focus
Emphasis MUST be placed on integration testing to verify system components work together.
-   **Contract Tests**: Verify interactions between libraries and services.
-   **Mocking**: Use mocks appropriately for external APIs (like OpenWeatherMap) to ensure deterministic tests.
-   **End-to-End**: Validate critical user flows (e.g., Subscription -> Notification) spanning multiple components.

## Governance

### Compliance
All new practices and code contributions MUST comply with these principles. Deviations require explicit justification in the Pull Request description.

### Amendments
Changes to this constitution require a formal review process and consensus among the core course maintainers.

**Version**: 1.0.0 | **Ratified**: 2025-11-20 | **Last Amended**: 2025-11-20
