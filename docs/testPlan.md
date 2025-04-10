# Test Plan: TranscriptorApp

**Version:** 1.0
**Date:** 2025-04-07

## 1. Introduction

### 1.1 Purpose

This document outlines the testing strategy for `TranscriptorApp`, a command-line application designed to download audio from video URLs, transcribe it using the Lemonfox API, and output the results in various formats. The goal of this plan is to ensure the application's functionality, reliability, and usability meet the specified requirements.

### 1.2 Application Overview

`TranscriptorApp` takes one or more video URLs, uses `yt-dlp` for audio extraction, interacts with the Lemonfox (OpenAI-compatible) API for transcription via the `openai` library, and generates `.txt` and `.srt` transcript files.

## 2. Scope

### 2.1 In Scope

- Testing core features: audio download/extraction, transcription API interaction, output formatting (TXT, SRT).
- Verification of command-line argument parsing and handling (including multiple URLs, output directory, model selection, format selection, API key usage, etc.).
- Testing batch processing of multiple URLs, including sequential execution and error handling for individual URLs within a batch.
- Basic error handling verification (e.g., invalid URLs, missing API key, API errors).
- Basic installation and setup verification on a supported environment.
- Unit, Integration, and End-to-End (E2E) testing strategies as defined below.
- Manual functional testing for broader coverage and usability checks.

### 2.2 Out of Scope

- Graphical User Interface (GUI) or Web User Interface (Web UI) testing (none exists).
- Formal performance, load, or stress testing.
- Exhaustive testing of every possible URL supported by `yt-dlp`.
- Exhaustive testing of all Lemonfox model variations or advanced API features beyond basic selection and speaker labels.
- Security vulnerability testing (penetration testing, dependency scanning beyond basic checks).
- Testing across a wide matrix of operating systems or Python versions beyond the recommended setup.
- Testing the accuracy of the underlying Whisper model provided by Lemonfox (treated as a black box).

## 3. Test Environment

- **Operating System:** Linux (e.g., Ubuntu 22.04 or similar). Tests should ideally be runnable on macOS and Windows with minor adjustments if needed.
- **Python Version:** 3.9+ (as recommended in `README.md`).
- **External Tools:** `ffmpeg` and `ffprobe` (latest stable recommended) installed system-wide and accessible in the system `PATH`.
- **Python Packages:** Dependencies listed in `requirements.txt` installed within a virtual environment (`yt-dlp`, `openai`, `python-dotenv`). Testing framework (`pytest`) and mocking library (`unittest.mock`) will be used.
- **API Key:** A valid Lemonfox API key configured in a `.env` file or environment variable (`LEMONFOX_API_KEY`). A separate key for testing might be advisable if significant E2E testing is performed.
- **Network:** Active internet connection required for E2E tests involving `yt-dlp` downloads and Lemonfox API calls.

## 4. Testing Strategies

### 4.1 Unit Testing

- **Goal:** Verify the correctness of individual functions and classes in isolation, without external dependencies (network, filesystem, APIs).
- **Tools:**
  - **Framework:** `pytest`
  - **Mocking:** `unittest.mock`
- **Scope/Targets:**
  - `core/formatter.py`: Test `_format_timestamp`, `generate_txt`, `generate_srt`.
  - `interfaces/cli/main.py`: Test argument parsing logic if complex, or any helper functions specific to the CLI.
  - `core/downloader.py`/`core/transcriber.py`: Limited scope. Focus on internal helpers, heavily mocking external library calls (`yt_dlp`, `openai`).
  - `core/pipeline.py`: Test any internal helper logic if refactored out.
- **Best Practices:**
  - Unit tests should primarily target the logic _within_ a function/class, assuming its direct dependencies (which are mocked) behave correctly.
  - Utilize `pytest.mark.parametrize` where applicable to test functions with multiple input variations efficiently.

### 4.2 Integration Testing

- **Goal:** Verify the interaction and data flow within the `core.pipeline.run_pipeline` function, mocking external dependencies (`yt-dlp`, Lemonfox API, filesystem).
- **Tools:**
  - **Framework:** `pytest` (using fixtures for setup/teardown, e.g., from `conftest.py`).
  - **Mocking:** `unittest.mock` to mock function calls within the pipeline (e.g., `core.downloader.download_audio_python_api`, `core.transcriber.transcribe_audio_lemonfox`, `core.formatter.generate_txt`, `core.formatter.generate_srt`) and external libraries (`yt_dlp.YoutubeDL`).
  - **Filesystem Helpers:** `pytest` fixtures (e.g., `tmp_path`) for managing temporary directories and files.
  - **Test Data:** Defined in `tests/integration/conftest.py` or specific test files.
- **Scope/Targets:**
  - Test the `core.pipeline.run_pipeline` function directly, passing a configuration dictionary.
  - Mock `core.downloader.download_audio_python_api` to return a path to a dummy audio file created in `tmp_path`.
  - Mock `core.transcriber.transcribe_audio_lemonfox` to return a predefined mock result dictionary.
  - Mock `core.formatter.generate_txt` and `core.formatter.generate_srt` to verify they are called correctly.
  - Mock `yt_dlp.YoutubeDL` used for filename extraction within the pipeline.
  - Verify the pipeline function correctly handles data returned from mocked components.
  - Verify the pipeline function correctly handles different configuration options passed via the `config` dictionary (e.g., `keep_audio`, `speaker_labels`).
  - Verify the pipeline function returns the expected summary dictionary (`processed_count`, `failed_urls`).
  - Verify expected formatter functions are called with correct arguments based on the mock transcription result and calculated output paths.
  - Test scenarios like single URL success, multiple URLs with failures, formatting failures, etc.

### 4.3 End-to-End (E2E) Testing

- **Goal:** Test the complete application flow from the command line, including interaction with real external dependencies (network, `yt-dlp`, Lemonfox API).
- **Tools:**
  - **Framework:** `pytest` (for structuring tests, fixtures like `tmp_path`, and test execution).
  - **Execution:** Python's `subprocess` module (specifically `subprocess.run`) to execute the CLI script (`.venv/bin/python interfaces/cli/main.py ...`).
  - **Assertion/Verification:** Standard Python assertions, `pathlib.Path` checks for files/directories, file content comparison, exit code checking.
- **Scope/Targets (Implemented in `tests/e2e/test_cli_flow.py`):**
  - Run the `interfaces/cli/main.py` script with single valid URLs (YouTube Short, TikTok) and default options. Verify exit code 0 and creation of default `txt`/`srt` files in a temporary directory.
  - Run with multiple valid URLs. Verify successful processing of both, correct output file count, successful exit code, and expected summary log.
  - Run with specific options like `--formats srt` and `--keep-audio`. Verify correct output files are generated/kept.
  - Run with `--keep-audio` and verify the audio file persists.
  - Run with one valid and one invalid URL. Verify successful processing of the valid URL, error logging (stderr) for the invalid one, continuation of the script, correct summary log (stdout/stderr), and non-zero exit code.
  - Verify successful execution when `LEMONFOX_API_KEY` is loaded from the `.env` file (confirming the 'key not found' error is _not_ shown).
  - Run with an invalid (non-video) URL format. Verify appropriate error message (stderr) and non-zero exit code.
- **Challenges & Considerations:** Dependency on live services, API costs, test flakiness, need for stable test URLs. Relies on `.env` file for API key during testing.

### 4.4 Manual Functional Testing

- **Goal:** Exploratory testing, usability checks, and verification of scenarios difficult or costly to automate fully.
- **Tools:** Command line, text editor, media player.
- **Scope/Targets:**
  - **Installation/Setup:** Follow `README.md` instructions on a clean environment.
  - **Diverse URLs:** Test with various real-world URLs from YouTube, TikTok, etc. (publicly accessible). Include long videos, videos with unusual titles/metadata.
  - **Transcription Quality:** Subjectively review transcript output for basic accuracy with default and potentially other models (e.g., `whisper-large-v3`). Check timestamp accuracy in SRT files.
  - **Speaker Labels:** Test `--speaker-labels` with a suitable video (e.g., interview) and check if labels appear correctly in output (if supported by Lemonfox model).
  - **Language Support:** Test `--language` hint with a non-English video.
  - **Error Messages:** Verify clarity and helpfulness of error messages for common issues (invalid URL, API key error, download failure).
  - **CLI Usability:** Check if `--help` output is clear and options behave as described.
  - **Filename Generation:** Test `--output-filename-template` with different `yt-dlp` fields and verify results, especially with special characters.
  - **Edge Cases:** Test with very short or silent audio.

## 5. Pass/Fail Criteria

- **Unit Tests:** Pass if all assertions within the test function hold true. Code coverage metrics should ideally be tracked.
- **Integration Tests:** Pass if the interactions between mocked components occur as expected, data flows correctly, and expected output files (in temp directories) are generated with the correct content based on mock data.
- **E2E Tests:** Pass if the CLI command executes successfully (exit code 0 for success scenarios, non-zero for expected failures), expected output files are created in the correct location with plausible content, and logs reflect the expected operations/errors.
- **Manual Tests:** Pass if the application behaves as described in the documentation/requirements for the tested scenario, outputs are correct, and no unexpected crashes or usability issues are encountered. Minor transcription inaccuracies inherent to the model are acceptable unless grossly incorrect.

## 6. Test Organization & Execution

- **Directory Structure:** Organize test files logically:
  - Unit tests: `tests/unit/`
  - Integration tests: `tests/integration/` (using `conftest.py` for shared fixtures/data)
  - E2E tests: `tests/e2e/`
  - Test data (if needed beyond mocks): `tests/data/`
- **Test Runner:** Execute tests using the `pytest` command from the project root. `pytest` will automatically discover tests in subdirectories.
  ```bash
  # Run all tests (unit, integration, e2e)
  pytest
  # Run only unit tests
  pytest tests/unit/
  # Run only integration tests
  pytest tests/integration/
  # Run only E2E tests
  pytest tests/e2e/
  ```
- **Coverage Reporting:** Measure test coverage using `pytest-cov` (included in `requirements-dev.txt`). Run with:
  ```bash
  # Coverage for all tests against the core logic
  pytest --cov=core tests/
  # Coverage for unit tests only
  pytest --cov=core tests/unit/
  # Coverage for integration tests only
  pytest --cov=core tests/integration/
  ```
  The report helps identify untested parts of the codebase.
- **CI Integration:** Integrate automated execution of unit and integration tests (and potentially E2E smoke tests), including coverage reporting, into a Continuous Integration (CI) pipeline (e.g., GitHub Actions) to ensure tests run automatically on code changes.
