# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.0] - 2025-04-10

### Refactored

- Extracted core transcription logic (`downloader`, `formatter`, `pipeline`, `transcriber`) into a separate installable library (`transcriptor-core`).
- Created project structure and packaging files (`pyproject.toml`, `requirements.txt`, `README.md`) for `transcriptor-core`.
- Removed the internal `core/` directory from the main `transcriptor-app`.
- Updated `transcriptor-app`'s `requirements.txt` to depend on `transcriptor-core` (using local editable install for development).
- Updated import paths across `transcriptor-app` (interfaces, tests) to use `transcriptor_core`.
- Moved unit tests (`tests/unit/`) and integration tests (`tests/integration/`) from `transcriptor-app` to `transcriptor-core`.
- Added development dependencies (`pytest`, `pytest-cov`) to `transcriptor-core`.
- Removed original unit and integration test directories from `transcriptor-app`.
- Fixed relative import errors in moved integration tests within `transcriptor-core`.

## [1.2.1] - 2025-04-10

### Added

- Local Web User Interface (Phase 1 MVP) using FastAPI and modular vanilla JavaScript (`interfaces/web/`).
- API endpoints (`/submit_job`, `/status/{job_id}`, `/result/{job_id}`, `/download/{job_id}/{filename}`) for Web UI.
- Background job processing via `threading` (`interfaces/web/processing.py`).
- Dynamic job list in Web UI with status polling and stage-based progress updates.

### Changed

- Refactored `core/pipeline.py` to accept a status update callback.
- Updated `interfaces/web/processing.py` to provide granular status updates via callback.
- Reduced Web UI polling interval to 1 second (`interfaces/web/static/jobManager.js`).
- Updated "Add another URL" button color in Web UI (`interfaces/web/templates/index.html`).
- Reorganized documentation files (`developmentPlan.md`, `technical_design.md`, `userFlow.md`, `testPlan.md`, `yt-dlp_readme.md`) into a new `docs/` directory.
- Updated links in `README.md` and `docs/technical_design.md` to reflect documentation move.

### Fixed

- Corrected `SyntaxError` in `interfaces/web/processing.py` (duplicated arguments).
- Resolved issue where Web UI status/progress bar wasn't updating through all stages by implementing status callbacks.

## [1.2.0] - 2025-04-09

### Changed

- Refactored project structure for better modularity:
  - Renamed `src` directory to `core`.
  - Created `interfaces/cli` directory for command-line interface.
  - Moved CLI entry point (`main.py`) to `interfaces/cli/main.py`.
- Decoupled core pipeline logic (`core/pipeline.py`) from `argparse` by accepting a configuration dictionary instead of a namespace object.
- Updated CLI (`interfaces/cli/main.py`) to create the configuration dictionary and call the refactored pipeline.
- Updated all unit, integration, and E2E tests (`tests/`) to reflect the new structure, import paths, and pipeline signature.
- Updated documentation (`README.md`, `technical_design.md`, `testPlan.md`) to align with the refactored structure.

## [1.1.3] - 2025-04-08

### Added

- End-to-End (E2E) tests (`tests/e2e/`) using `pytest` and `subprocess` to verify core CLI functionality against real services (yt-dlp, Lemonfox API).
- E2E tests cover single/multiple URL success, options (`--formats`, `--keep-audio`), partial failure, missing API key loading, and invalid URL handling.

### Fixed

- Adjusted application logging (`src/main.py`) to send INFO level logs to `stdout` and WARNING/ERROR levels to `stderr` for better separation and compatibility with CLI expectations.
- Updated E2E tests to check correct output streams (`stdout`/`stderr`) for log messages and summary info.
- Corrected E2E test helper (`run_transcriptor_cli`) to use the Python interpreter from the virtual environment (`.venv/bin/python`).

## [1.1.2] - 2025-04-07

### Added

- Integration tests (`tests/integration/`) covering success flows, failure handling, and argument flags, using mocked external dependencies.

### Changed

- Refactored core processing logic from `main.py` into `pipeline.py` for better modularity and testability.
- Refactored integration tests into separate files (`test_success_flow.py`, `test_failure_handling.py`, `test_argument_flags.py`) using `conftest.py`.

## [1.1.1] - 2025-04-07

### Added

- Unit tests for `YtdlpLogger`, transcriber string response handling, and formatter negative timestamp handling.
- `pytest-cov` dependency for test coverage reporting.

### Changed

- Updated development dependencies in `requirements-dev.txt`.

## [1.1.0] - 2025-04-07

### Added

- Support for processing multiple video URLs provided as command-line arguments (space-separated).
- Enhanced error handling to continue processing subsequent URLs if one fails.
- Batch summary logging at the end of processing.
- Testing framework setup using `pytest`.
- `requirements-dev.txt` for development dependencies.
- Unit tests for `formatter`, `downloader`, and `transcriber` modules.
- `testPlan.md` outlining the testing strategy.

### Fixed

- Floating point precision issue in SRT timestamp generation (`_format_timestamp`).
- Handling of `None` text values in `generate_srt`.
- Indentation errors in `transcriber.py` exception handling.
- Missing imports and assertion logic in unit tests.

## [1.0.0] - 2025-04-06

- Initial release.
- Download audio from video URLs using `yt-dlp`.
- Transcribe audio using Lemonfox API (OpenAI-compatible).
- Output transcripts in TXT and SRT formats.
- Configurable model, output directory, formats, etc.
