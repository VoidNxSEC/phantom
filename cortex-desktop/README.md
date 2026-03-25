# Cortex Desktop v0.1.0

**Graphical User Interface for the Phantom Data Engineering Pipeline**

Cortex Desktop serves as the primary graphical interface for the Phantom ecosystem. Built with Tauri and Svelte 5, it provides a performant, cross-platform desktop experience for managing data classification workflows and interacting with supported LLM providers for data analysis.

## Core Capabilities

- **Pipeline Visualization**: Monitor and orchestrate the Phantom DAG pipeline directly from the desktop.
- **LLM Integration**: Native support for analyzing processed data via Tensor Forge, OpenAI, and Anthropic APIs.
- **State Management**: Centralized, reactive state architecture utilizing Svelte 5 runes.
- **Local Connectivity**: Seamless integration with the local Phantom core API (default: `http://localhost:8087`).
- **Cross-Platform**: Lightweight, memory-safe execution via Tauri's Rust backend.

## Tech Stack

- **Framework**: SvelteKit / Svelte 5
- **Desktop Runtime**: Tauri v2
- **Styling**: TailwindCSS (Modern, component-driven UI)
- **Tooling**: TypeScript, Vite

## Development Setup

### Prerequisites

- Node.js (via Nix or traditional installation)
- Rust toolchain (required for Tauri)
- Phantom Core API (running on port `8087`)

### Installation & Execution

1. **Install dependencies:***(Note: For Nix users, ensure you are within the nix develop shell)*
2. **Run the development server:**&#x54;his will concurrently start the Vite frontend server and the Tauri Rust backend.

### Project Structure

```text
cortex-desktop/
├── src/
│   ├── lib/
│   │   ├── api.ts              # Phantom Core API client schema
│   │   ├── state.svelte.ts     # Global application state (Svelte 5 Runes)
│   │   └── components/         # Reusable UI components
│   ├── routes/                 # SvelteKit routing logic
│   └── app.css                 # Global styles and Tailwind configuration
├── src-tauri/                  # Rust backend for desktop integration
├── package.json                # Frontend dependencies and scripts
└── tailwind.config.js          # Tailwind styling definitions
```

## Backend Connectivity

Cortex Desktop requires the Phantom API to be active. Ensure the core services are running:

```bash
# In the root phantom directory
./start_api.sh
```

Configure your specific LLM provider credentials within the GUI settings pane to enable intelligent chat capabilities.

## Known Issues

### Native File Dialog Crash (Linux/NixOS) `[PENDING]`

When interacting with the system's native file selection dialog on Linux (specifically when executed within certain Nix environments), the application might crash with the following output:

```text
(cortex-desktop:435378): GLib-GIO-ERROR **: 17:44:03.897: No GSettings schemas are installed on the system
```

**Workaround**: Ensure your environment correctly exposes GSettings schemas. If using Nix, add `glib` and `gsettings-desktop-schemas` to your build inputs, and wrap the executable to include the proper `XDG_DATA_DIRS`.

## License

This project is licensed under the Apache 2.0 License.

## Contributing

Pull requests are accepted. For architectural modifications or significant UI changes, please open an issue describing the proposed design prior to execution.
