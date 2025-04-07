# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
