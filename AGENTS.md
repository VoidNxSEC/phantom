# Repository Guidelines

## Project Structure & Module Organization

Phantom is a Python 3.11+ package under `src/phantom`. Core domains are split by package: `core/`, `rag/`, `analysis/`, `pipeline/`, `api/`, `cli/`, `providers/`, `nats/`, `cerebro/`, and `neotron/`. Tests live in `tests/unit`, `tests/integration`, and `tests/e2e`, with shared fixtures in `tests/conftest.py`. Documentation is in `docs/`, Nix packaging is in `flake.nix` and `nix/`, scripts are in `scripts/`, and the Svelte/Tauri desktop app is in `cortex-desktop/`. Sample inputs belong in `input_data/` or `demo_input/`.

## Build, Test, and Development Commands

Use `just` as the main command interface.

- `just dev`: enter the recommended Nix development shell.
- `just build`: run `nix build` for the project.
- `just check`: run full Nix flake checks.
- `just test`: run the complete pytest suite.
- `just test-cov`: run tests with coverage reports.
- `just lint`: run Ruff checks and mypy.
- `just fmt`: format Python files with Ruff.
- `just serve PORT=8008`: start the Phantom API locally.
- `just desktop`: run the Cortex desktop app via Tauri.

For frontend-only checks, run `npm run check` or `npm run build` inside `cortex-desktop/`.

## Coding Style & Naming Conventions

Python code uses Ruff with a 100-character line length, Python 3.11 target, and first-party imports under `phantom`. Prefer typed function signatures, specific exceptions, Pydantic models for validated data, and project logging helpers over `print`. Use `test_*.py` files and `test_*` functions. Keep module names lowercase with underscores.

## Testing Guidelines

Pytest discovers tests from `tests/` and uses markers for `unit`, `integration`, `e2e`, `slow`, `gpu`, and `llm`. Add unit tests near changed behavior and integration tests when API, pipeline, storage, or cross-module contracts change. Coverage targets `phantom` with a 70% minimum. Run targeted checks with `just test-file tests/unit/test_example.py` or `just test-match pattern`.

## Commit & Pull Request Guidelines

Follow Conventional Commits, as used in history: `feat(rag): add hybrid search`, `fix(ci): migrate flake workflow`, `docs(root): add guide`. Common scopes include `core`, `rag`, `analysis`, `pipeline`, `api`, `cli`, `docs`, `tests`, and `ci`. Pull requests should include a clear summary, linked issues, test results, and screenshots or recordings for `cortex-desktop` UI changes. Ensure `just test`, `just lint`, and relevant build checks pass before review.

## Security & Configuration Tips

Do not commit secrets, model credentials, local caches, or generated large artifacts. Keep environment-specific settings outside tracked files unless they are documented examples. Use `SECURITY.md` for vulnerability reporting expectations.
