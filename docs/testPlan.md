# Test Plan: TranscriptorApp Application

**Version:** 1.0
**Date:** 2025-04-07 (Revised 2025-04-10)

## 1. Introduction

### 1.1 Purpose

This document outlines the testing strategy for the `TranscriptorApp` application interfaces (CLI and Web UI). It focuses on End-to-End (E2E) and Manual Functional testing to ensure the application, using the `transcriptor-core` library, functions correctly from a user's perspective. Testing for the internal `transcriptor-core` library (Unit, Integration) is covered separately in `transcriptor-core/docs/testing.md`.

### 1.2 Application Overview

`TranscriptorApp` provides CLI and Web interfaces that utilize the `transcriptor-core` library to download audio, transcribe it via the Lemonfox API, and generate transcript files.

## 2. Scope

### 2.1 In Scope

- End-to-End (E2E) testing of the Command-Line Interface (CLI) flow, including interaction with real external services (`yt-dlp`, Lemonfox API).
- Manual functional testing of both the CLI and the local Web User Interface (Web UI).
- Verification of command-line argument parsing and handling.
- Verification of Web UI interactions (job submission, status polling, result display/download).
- Testing application-level error handling and user feedback for both interfaces.
- Basic installation and setup verification of the application itself.

### 2.2 Out of Scope

- Unit and Integration testing of the `transcriptor-core` library (covered in `transcriptor-core/docs/testing.md`).
- Formal performance, load, or stress testing.
- Exhaustive testing of every possible URL supported by `yt-dlp`.
- Exhaustive testing of all Lemonfox model variations or advanced API features beyond basic selection and speaker labels.
- Security vulnerability testing (penetration testing, dependency scanning beyond basic checks).
- Testing across a wide matrix of operating systems or Python versions beyond the recommended setup.
- Testing the accuracy of the underlying Whisper model provided by Lemonfox (treated as a black box).
- Automated E2E testing for the Web UI (currently only manual testing is planned).

## 3. Test Environment

- **Operating System:** Linux (e.g., Ubuntu 22.04 or similar). Tests should ideally be runnable on macOS and Windows with minor adjustments if needed.
- **Python Version:** 3.9+ (as recommended in `README.md`).
- **External Tools:** `ffmpeg` and `ffprobe` (latest stable recommended) installed system-wide and accessible in the system `PATH`.
- **Python Packages:** Dependencies listed in `transcriptor-app/requirements.txt` installed within a virtual environment (including `transcriptor-core`, `fastapi`, `uvicorn`, `python-dotenv`, etc.). Testing framework (`pytest`) installed from `transcriptor-app/requirements-dev.txt`.
- **API Key:** A valid Lemonfox API key configured in a `.env` file in the `transcriptor-app` root directory. A separate key for testing might be advisable if significant E2E testing is performed.
- **Network:** Active internet connection required for E2E tests involving `yt-dlp` downloads and Lemonfox API calls.
- **Web Browser:** A modern web browser (e.g., Chrome, Firefox) for manual Web UI testing.

## 4. Testing Strategies

### 4.1 Unit & Integration Testing (Core Library)

- **Goal:** Verify internal logic and component interactions of the `transcriptor-core` library.
- **Location:** `transcriptor-core/tests/`
- **Details:** See `transcriptor-core/docs/testing.md`.

### 4.2 End-to-End (E2E) Testing (CLI)

- **Goal:** Test the complete CLI application flow, including interaction with real external dependencies (network, `yt-dlp`, Lemonfox API), using the installed `transcriptor-core` library.
- **Location:** `transcriptor-app/tests/e2e/`.
- **Tools:**
  - **Framework:** `pytest` (for structuring tests, fixtures like `tmp_path`, test execution).
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
- **Challenges & Considerations:** Dependency on live services, API costs, test flakiness, need for stable test URLs. Relies on `.env` file for API key during testing. Requires network access.

### 4.3 Manual Functional Testing (CLI & Web UI)

- **Goal:** Exploratory testing, usability checks, and verification of scenarios difficult or costly to automate fully for both CLI and Web UI.
- **Tools:** Command line, Web Browser, text editor, media player.
- **Scope/Targets (CLI):**
  - **Installation/Setup:** Follow `README.md` instructions on a clean environment.
  - **Diverse URLs:** Test with various real-world URLs from YouTube, TikTok, etc. (publicly accessible). Include long videos, videos with unusual titles/metadata.
  - **Transcription Quality:** Subjectively review transcript output for basic accuracy with default and potentially other models (e.g., `whisper-large-v3`). Check timestamp accuracy in SRT files.
  - **Speaker Labels:** Test `--speaker-labels` with a suitable video (e.g., interview) and check if labels appear correctly in output (if supported by Lemonfox model).
  - **Language Support:** Test `--language` hint with a non-English video.
  - **Error Messages:** Verify clarity and helpfulness of error messages for common issues (invalid URL, API key error, download failure).
  - **CLI Usability:** Check if `--help` output is clear and options behave as described.
  - **Filename Generation:** Test `--output-filename-template` with different `yt-dlp` fields and verify results, especially with special characters.
  - **Edge Cases:** Test with very short or silent audio.
- **Scope/Targets (Web UI):**
  - **Server Startup:** Verify `uvicorn` starts correctly.
  - **UI Loading:** Check if the interface loads correctly at `http://127.0.0.1:8000`.
  - **Form Interaction:** Test URL input (single/multiple), option selection (model, formats, advanced).
  - **Job Submission:** Verify jobs start correctly after clicking "Start Transcription".
  - **Status Polling:** Observe job cards updating through different stages (Pending, Downloading, Transcribing, Formatting, Completed/Failed, Cancelling, Cancelled).
  - **Cancel/Retry:** Test clicking the Cancel button on a processing job and verify the status updates correctly. Test clicking the Retry button on a failed job and verify a new job is submitted and the old card is updated.
  - **Result Display:** Check if download links appear correctly for completed jobs.
  - **File Download:** Verify downloaded files contain expected transcript content.
  - **Error Handling:** Test submitting invalid URLs, check how errors are displayed on job cards. Test scenarios where background processing might fail.
  - **Responsiveness:** Basic check if the UI remains usable while jobs are processing.
  - **Cross-Browser:** Basic checks on Chrome/Firefox.

## 5. Pass/Fail Criteria

- **E2E Tests (CLI):** Pass if the CLI command executes successfully (exit code 0 for success scenarios, non-zero for expected failures), expected output files are created in the correct location with plausible content, and logs reflect the expected operations/errors.
- **Manual Tests (CLI & Web UI):** Pass if the application behaves as described in the documentation/requirements for the tested scenario, outputs are correct, and no unexpected crashes or usability issues are encountered. Minor transcription inaccuracies inherent to the model are acceptable unless grossly incorrect.

## 6. Test Organization & Execution

- **Directory Structure:**
  - `transcriptor-app/tests/e2e/`: End-to-end tests for the CLI application.
  - `transcriptor-core/tests/`: Contains unit and integration tests for the core library (see `transcriptor-core/docs/testing.md`).
- **Test Runner:** Execute tests using `python -m pytest`.

  ```bash
  # Run application E2E tests (from transcriptor-app dir)
  python -m pytest tests/e2e/

  # Run core unit & integration tests (from transcriptor-core dir)
  # cd ../transcriptor-core
  # python -m pytest
  # cd ../transcriptor-app
  ```

- **Coverage Reporting:** Coverage is measured for the `transcriptor-core` library as described in its testing document. Coverage for the application interface code itself is not currently measured via automation.
- **CI Integration:** Integrate automated execution of application E2E tests into a Continuous Integration (CI) pipeline (e.g., GitHub Actions) for the `transcriptor-app` repository. Core library tests should run in the CI pipeline for the `transcriptor-core` repository.
