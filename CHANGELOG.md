# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
