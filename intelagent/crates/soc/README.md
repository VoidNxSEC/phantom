# IntelAgent SOC - System Operations Center

**Phase 0: Foundation** - GTK4 application with command palette and Phantom integration.

## Architecture

```
SOC (GTK4 App)
├─ Command Palette  → User input, command execution
├─ Log Viewer       → Real-time log display
└─ PhantomWorker    → Tight coupling with Phantom engine
```

## Features (Phase 0)

- ✅ GTK4 + libadwaita modern UI
- ✅ Command palette (Vim-style command input)
- ✅ Real-time log viewer
- ✅ Phantom integration stub (ready for actual implementation)
- ✅ Async command execution (Tokio)

## Commands Available

```
> help                                    - Show available commands
> process-document --file <path>          - Process document via Phantom
```

## Building

```bash
# From intelagent directory
nix develop -c cargo build --package intelagent-soc

# Or run directly
nix develop -c cargo run --package intelagent-soc
```

## Running

```bash
cd /home/kernelcore/dev/projects/phantom/intelagent
nix develop -c cargo run --package intelagent-soc
```

## Development

### File Structure

```
crates/soc/
├─ src/
│  ├─ main.rs              # GTK4 app entry point
│  ├─ ui/
│  │  ├─ command_palette.rs  # Command input + execution
│  │  └─ log_viewer.rs       # Log display widget
│  └─ engine/
│     └─ phantom_worker.rs   # Phantom integration
└─ Cargo.toml
```

### Next Steps (Phase 1)

1. Connect PhantomWorker to actual Phantom API
2. Implement async task execution with proper error handling
3. Add agent pool (multiple Phantom workers)
4. Implement ribbon interface (tabs for different contexts)
5. Add multi-viewport management

## Tech Stack

- **UI Framework**: GTK4 + libadwaita
- **Language**: Rust (2021 edition)
- **Async**: Tokio
- **Logging**: tracing + tracing-subscriber

## Notes

This is **Phase 0** - a functional foundation. The UI is intentionally minimal to focus on:
- Solid GTK4 foundation
- Command palette UX
- Phantom integration architecture

Future phases will add:
- Visual workflow canvas
- Multi-panel viewports
- Tool palettes (drag-and-drop)
- Quality gates integration
- MCP servers
- Privacy layers (ZK proofs)
- DAO governance

---

**Built with**: GTK4, Rust, Tokio, libadwaita
**License**: MIT
**Author**: kernelcore <kernelcore@voidnix.dev>
