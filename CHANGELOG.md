# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Support for processing multiple video URLs provided as command-line arguments (space-separated).
- Enhanced error handling to continue processing subsequent URLs if one fails.
- Batch summary logging at the end of processing.

## [1.0.0] - YYYY-MM-DD

- Initial release.
- Download audio from video URLs using `yt-dlp`.
- Transcribe audio using Lemonfox API (OpenAI-compatible).
- Output transcripts in TXT and SRT formats.
- Configurable model, output directory, formats, etc.
