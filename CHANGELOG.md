# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-01-06

### Refactor
- **Project Structure**: Reorganized codebase into a standard `src/` layout.
- **Modularization**: Separated EVE and PVE logic into dedicated modules (`src/eve`, `src/pve`).
- **Entry Points**: Moved and renamed entry scripts to `src/main.py`, `src/map_editor.py`, and `src/cli.py`.

### Added
- **Tests**: Added basic unit tests for simulation loop in `tests/test_simulation.py`.
- **Docs**: Centralized documentation in `docs/` directory.

### Fixed
- **Imports**: Updated import paths to support the new directory structure.
