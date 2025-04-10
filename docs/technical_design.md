# Technical Design Document: TranscriptorApp

**Version:** 1.0
**Date:** 2025-04-06

## 1. Introduction / Overview

### 1.1 Purpose

This document outlines the technical design for `TranscriptorApp`, an application designed to generate transcripts from video URLs, offering both a command-line and a local web-based user interface.

### 1.2 Application Description

`TranscriptorApp` accepts URLs from popular video platforms (YouTube, TikTok, Instagram), downloads the associated video content, extracts the audio, transcribes the audio to text using the Lemonfox API (an OpenAI-compatible Whisper endpoint), and outputs the transcript in various formats (`TXT`, `SRT`). It provides both a CLI and a local Web UI for interaction.

### 1.3 Goals

- Provide simple command-line and local web interfaces for users.
- Reliably download content from specified platforms.
- Accurately transcribe audio content.
- Offer common transcript output formats.
- Maintain a modular and extensible codebase using open-source libraries.

### 1.4 Target Audience

Developers involved in the implementation, testing, and future maintenance of `TranscriptorApp`.

## 2. Goals and Scope

### 2.1 In Scope (Version 1.0)

- **Input:** Accept one or more video URLs via command-line arguments (space-separated). Supported platforms: YouTube, TikTok, Instagram (leveraging `yt-dlp`'s capabilities).
- **Downloading:** Utilize `yt-dlp`'s Python API to download and extract audio for each URL.
- **Audio Format:** Extract audio into common formats like `MP3` or `Opus` (configurable).
- **Transcription:** Use the standard `openai` Python library, configured to point to the Lemonfox API endpoint, to perform transcription. Allow selection of Whisper model size (e.g., `tiny`, `base`, `small`, `medium`, `large` - assuming Lemonfox supports these via the `model` parameter) via CLI argument. Optionally support Lemonfox features like `speaker_labels`.
- **Output Formats:** Generate transcripts in plain text (`.txt`) and SubRip Subtitle (`.srt`) formats. Allow selection of desired formats via CLI argument.
- **Output Location:** Save output files to a user-specified directory or a default location.
- **Modularity:** Structure the code into distinct Python modules for downloading, transcription, and formatting.
- **Technology:** Rely on Python and specified open-source libraries (including FastAPI for the web interface).
- **Interfaces:** Command-Line Interface (CLI) and a local Web User Interface (Web UI) served via FastAPI.

### 2.2 Out of Scope (Version 1.0)

- Cloud-hosted Web Application (planned for future phase).
- User management, accounts, or authentication for the app itself.
- Platform-specific authentication (e.g., downloading private videos requiring login) via `yt-dlp`, although the library supports it.
- Explicit support for platforms beyond the capabilities of `yt-dlp`.
- Real-time transcription or translation.
- Database integration for storing jobs or transcripts.
- Advanced audio pre-processing before transcription.
- Speaker diarization (unless using Lemonfox's `speaker_labels`).
- Built-in batch processing (users can run the script multiple times).

## 3. Architecture and Design

### 3.1 High-Level Architecture

The application follows a pipeline architecture initiated from either a command-line interface or a local web interface.

- **Interface Layer (CLI or Web):** Parses user input (URL, options).
  - **CLI:** `interfaces/cli/main.py` using `argparse`.
  - **Web UI:** `interfaces/web/main.py` (FastAPI) receiving requests from the browser frontend (`interfaces/web/static/`).
- **Orchestration Layer:** Coordinates the workflow.
  - For CLI: `core/pipeline.py` called directly.
  - For Web UI: `interfaces/web/processing.py` initiates `core/pipeline.py` in a background thread and manages job state.
- **Core Library (`transcriptor-core`):** An external, installable Python package containing the core logic.
  - **Downloader Module:** Interacts with `yt-dlp` to fetch and extract audio.
  - **Transcriber Module:** Interacts with the Lemonfox API via the configured `openai` library client.
  - **Formatter Module:** Processes transcription output into desired file formats.
  - **Pipeline Module:** Orchestrates the download -> transcribe -> format process.
- **Filesystem:** Reads/writes audio and transcript files.

### 3.2 Modularity

The application relies on the external `transcriptor-core` library for its main functionality. The `transcriptor-app` project itself contains:

- **`interfaces/`**: Contains different ways to interact with the core engine.
  - `cli/`: The command-line interface (`main.py`).
  - `web/`: The local web user interface.
    - `main.py`: FastAPI backend server defining API endpoints (`/`, `/submit_job`, `/status`, `/result`, `/download`).
    - `processing.py`: Handles background job execution using `threading` and updates a shared job status dictionary. Calls `transcriptor_core.pipeline.run_pipeline`.
    - `static/`: Contains CSS (`style.css`) and modular JavaScript files (`main.js`, `apiClient.js`, `jobManager.js`, `uiInteractions.js`) for frontend logic.
    - `templates/`: Contains the main HTML template (`index.html`) using Jinja2.
- **`tests/e2e/`**: Contains end-to-end tests for the application interfaces.

### 3.3 Data Flow

**CLI Flow:**

1.  User executes `python interfaces/cli/main.py <URL1> <URL2> ... [options]`.
2.  `interfaces/cli/main.py` parses arguments (`argparse`), loads API key (`dotenv`), creates `config` dict.
3.  `interfaces/cli/main.py` calls `transcriptor_core.pipeline.run_pipeline(urls, api_key, config, ...)`.
4.  The `transcriptor_core` library executes the pipeline (downloader, transcriber, formatter).
5.  `run_pipeline` returns results summary.
6.  `interfaces/cli/main.py` prints summary and exits.

**Web UI Flow:**

1.  User starts server: `uvicorn interfaces.web.main:app ...`.
2.  User accesses `http://127.0.0.1:8000` in browser.
3.  `interfaces/web/main.py` serves `index.html`.
4.  Frontend JS (`main.js`, `uiInteractions.js`) handles UI setup.
5.  User enters URLs/options and clicks "Start Transcription".
6.  Frontend JS (`main.js`, `apiClient.js`) gathers data, sends POST request to `/submit_job`.
7.  `interfaces/web/main.py` (`submit_job_endpoint`):
    a. Receives request, validates URLs.
    b. Calls `interfaces.web.processing.start_job`, passing URLs, config, and the shared `jobs` dict.
    c. Returns `job_id` to frontend.
8.  `interfaces.web.processing.start_job`:
    a. Creates `job_id`, initializes job entry in `jobs` dict (status: "pending").
    b. Starts a background thread (`threading.Thread`) targeting `run_transcription_job_in_background`.
9.  `interfaces.web.processing.run_transcription_job_in_background` (in background thread):
    a. Defines an `update_status` callback function.
    b. Loads API key (`dotenv`).
    c. Creates output directories.
    d. Calls `transcriptor_core.pipeline.run_pipeline`, passing the `update_status` callback.
    e. The `transcriptor_core` library executes the pipeline, invoking `update_status('downloading')`, `update_status('transcribing')`, `update_status('formatting')` at appropriate times.
    f. `update_status` modifies the shared `jobs` dict.
    g. After `run_pipeline` finishes, `run_transcription_job_in_background` updates the final status (`completed` or `failed`), error message, and file list in the `jobs` dict based on `pipeline_results`.
10. Frontend JS (`jobManager.js`):
    a. Receives `job_id` from `/submit_job`.
    b. Calls `addJobToUI` to display the initial job card.
    c. Calls `startPollingJobStatus`, which periodically (`setInterval`) calls `updateJobStatus`.
11. Frontend JS (`jobManager.js` - `updateJobStatus`):
    a. Calls `apiClient.getJobStatus(job_id)`.
    b. `apiClient.js` sends GET request to `/status/{job_id}`.
    c. `interfaces/web/main.py` (`get_job_status_endpoint`) reads the current status/error from the `jobs` dict and returns it.
    d. `updateJobStatus` receives the status and calls `updateJobCardUI`.
12. Frontend JS (`jobManager.js` - `updateJobCardUI`): Updates the specific job card's text, colors, and progress bar based on the received status.
13. If status is `completed` or `failed`, polling stops (`stopPollingJobStatus`). If `completed`, `fetchAndPopulateResults` is called.
14. Frontend JS (`jobManager.js` - `fetchAndPopulateResults`):
    a. Calls `apiClient.getJobResult(job_id)`.
    b. `apiClient.js` sends GET request to `/result/{job_id}`.
    c. `interfaces/web/main.py` (`get_job_result_endpoint`) reads final details (files, counts, error) from `jobs` dict and returns them.
    d. `fetchAndPopulateResults` populates download links etc. on the job card.

### 3.4 Error Handling Strategy

- Functions within the `transcriptor_core` library use `try...except` blocks to catch relevant exceptions (e.g., `yt_dlp.utils.DownloadError`, `openai.APIError`, `FileNotFoundError`, general `Exception`) and return `None` or specific error indicators upon failure.
- Errors are logged using Python's `logging` module within the core library.
- The `transcriptor_core.pipeline.run_pipeline` function handles errors from its internal components for each URL, logs them, and adds the URL to a failed list, returning a summary.
- `interfaces/cli/main.py` uses the summary returned by `run_pipeline` to set the exit code.
- `interfaces/web/processing.py` catches exceptions during the call to `run_pipeline` and updates the job status/error in the shared dictionary.
- `interfaces/web/main.py` includes basic validation and returns appropriate HTTP exceptions (e.g., 404 for unknown job ID, 400 for bad requests).
- Frontend JavaScript (`apiClient.js`, `main.js`) includes `try...catch` blocks for API calls and displays error messages to the user (e.g., via `alert`).

## 4. Component Breakdown

### 4.1 `interfaces/cli/main.py` (CLI Entry Point & Setup/Teardown)

- **Responsibilities:** Parse CLI args (`argparse`). Load API key (`dotenv`). Configure logging. Create output directories. Prepare the `config` dictionary for the core pipeline. Call `transcriptor_core.pipeline.run_pipeline`. Print final summary based on pipeline results. Set exit code.
- **Interface:** Command-line execution.

### 4.2 `interfaces/web/main.py` (Web Backend API)

- **Responsibilities:** Define FastAPI app. Serve static files and HTML template. Define API endpoints (`/`, `/submit_job`, `/status/{job_id}`, `/result/{job_id}`, `/download/{job_id}/{filename}`). Handle request validation (Pydantic). Manage shared `jobs` dictionary (simple in-memory store). Initiate background tasks via `interfaces.web.processing.start_job`. Retrieve job status/results from the `jobs` dict. Serve file downloads.
- **Interface:** HTTP API endpoints.

### 4.3 `interfaces/web/processing.py` (Web Background Processing)

- **Responsibilities:** Define `start_job` to initialize job state and launch background thread. Define `run_transcription_job_in_background` (target for thread) which sets up environment (API key, directories), defines status callback, calls `transcriptor_core.pipeline.run_pipeline` with the callback, and updates the final job state in the shared `jobs` dictionary based on pipeline results or exceptions.
- **Interface:** `start_job(...)`, `run_transcription_job_in_background(...)`.

### 4.4 `interfaces/web/static/*.js` (Web Frontend Logic)

- **Responsibilities:**
  - `main.js`: Entry point, initializes other modules, handles main job submission logic.
  - `apiClient.js`: Encapsulates `fetch` calls to the backend API endpoints.
  - `jobManager.js`: Manages the list of active jobs in the UI, handles status polling (`setInterval`), updates job card display based on status, fetches final results.
  - `uiInteractions.js`: Handles general UI events (button clicks, checkbox changes, modals, form clearing) not directly related to job state polling.
- **Interface:** Browser DOM events, functions exported/imported between modules.

### 4.5 `core/pipeline.py` (Core Pipeline Logic)

### 4.5 `transcriptor-core` Library (External Package)

- **Responsibilities:** Encapsulates the core logic for downloading, transcribing, and formatting. Exposes functions like `run_pipeline`, `download_audio_python_api`, `transcribe_audio_lemonfox`, `generate_txt`, `generate_srt`. Handles internal error handling and logging.
- **Interface:** Python functions imported by `transcriptor-app`.

## 5. Technology Stack

- **Language:** Python (Version 3.9+ recommended)
- **Application Libraries (`transcriptor-app/requirements.txt`):**
  - `transcriptor-core`: The core logic library (installed locally via `-e`).
  - `python-dotenv`: For loading API keys from `.env`.
  - `fastapi`: Web framework for the backend API.
  - `uvicorn[standard]`: ASGI server to run FastAPI.
  - `python-multipart`: For form data handling in FastAPI.
  - `jinja2`: For HTML templating.
- **Core Library Dependencies (`transcriptor-core/requirements.txt`):**
  - `yt-dlp`: ==2025.03.31
  - `openai`: ==1.70.0 (for interacting with the Lemonfox API)
- **Standard Libraries:** `os`, `argparse`, `datetime`, `logging`, `json`, `threading`, `uuid`, `sys`, `importlib`.
- **External System Dependencies:**
  - `ffmpeg` / `ffprobe`: Latest stable version, must be installed system-wide and accessible in the `PATH`.

### 5.1 Dependencies Summary

- **Programming Language:**
  - Python (Version 3.9+ recommended)
- **Application Python Libraries (`transcriptor-app` via `pip`):**
  - `transcriptor-core` (local editable install)
  - `python-dotenv`
  - `fastapi`
  - `uvicorn[standard]`
  - `python-multipart`
  - `jinja2`
- **Core Library Python Libraries (`transcriptor-core` via `pip`):**
  - `yt-dlp`
  - `openai`
- **Standard Python Libraries (Built-in):**
  - `os`, `sys`, `argparse`, `datetime`, `logging`, `json`, `threading`, `uuid`, `importlib`
- **External System Dependencies (Manual Installation Required):**
  - `ffmpeg` / `ffprobe`: Latest stable version, accessible in system `PATH`.
- **Development/Setup Tools (from `requirements-dev.txt` in respective projects):**
  - `pip`
  - `pytest`
  - `pytest-cov`
  - `Git` (Optional)

## 6. Data Structures

- **Configuration:**
  - CLI: Arguments parsed by `argparse` in `interfaces/cli/main.py`.
  - Web UI: Options selected in the browser, sent as JSON to `/submit_job`.
  - Both: Configuration dictionary passed to `core.pipeline.run_pipeline`. Lemonfox API Key managed via `.env` file.
- **Job State (Web UI):** In-memory Python dictionary (`jobs`) in `interfaces/web/main.py`, shared with `interfaces/web/processing.py`. Contains status, config, results, errors, timestamps, etc., keyed by `job_id`.
- **Intermediate:** Audio file path (string). Lemonfox transcription result (dict): Structure depends on `response_format`. Example:
  ```json
  {
    "task": "transcribe",
    "language": "en",
    "duration": 13.169,
    "text": "...",
    "segments": [
      {
        "id": 0,
        "text": "...",
        "start": 0.1,
        "end": 6.42,
        "language": "en",
        "speaker": "SPEAKER_00",
        "words": [
          {
            "word": "Artificial",
            "start": 0.1,
            "end": 0.561,
            "speaker": "SPEAKER_00"
          }
          // ... more words
        ]
      }
      // ... more segments
    ]
  }
  ```
- **Output:** String content for `.txt` and `.srt` files.

## 7. Deployment and Setup

- **Prerequisites:** Python 3.9+, `pip`, `ffmpeg` & `ffprobe` in system `PATH`. `Git` (optional, for cloning).
- **Installation Steps:**
  1.  Obtain code for both `transcriptor-app` and `transcriptor-core` (e.g., clone both repositories into the same parent directory).
  2.  Navigate to the `transcriptor-app` project directory.
  3.  Create virtual environment: `python -m venv .venv`
  4.  Activate environment: `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows).
  5.  Install application dependencies and the core library: `pip install -r requirements.txt`. This uses the `-e ../transcriptor-core` line to install the local core library in editable mode.
  6.  Ensure Lemonfox API Key is available in a `.env` file in the `transcriptor-app` project root.
- **Running:**
  - **CLI:** (Run from `transcriptor-app` directory)
    ```bash
    python interfaces/cli/main.py <URL> --model whisper-1 --formats txt srt --output-dir ./transcripts
    ```
  - **Web UI:** (Run from `transcriptor-app` directory)
    ```bash
    uvicorn interfaces.web.main:app --reload --host 127.0.0.1 --port 8000
    ```
    Then access `http://127.0.0.1:8000` in a browser.

## 8. Potential Challenges and Risks

- **Platform API Changes:** `yt-dlp` breakage due to YouTube/TikTok/Instagram updates.
  - **Mitigation:** Frequent `yt-dlp` updates, use `--update-to nightly`.
- **Lemonfox API:** Changes to API endpoints, parameters, response formats, or pricing. Service availability issues. Rate limiting.
  - **Mitigation:** Monitor Lemonfox documentation, implement robust error handling and retries if applicable.
- **API Key Management:** Need for secure storage and retrieval of the Lemonfox API key.
  - **Mitigation:** Currently uses `.env` file loaded via `python-dotenv`. Ensure `.env` is in `.gitignore`.
- **Network Issues:** General connectivity problems affecting downloads or API calls.
  - **Mitigation:** Standard network error handling, retries (`yt-dlp` has built-in retries).
- **Transcription Quality/Features:** Potential differences in accuracy or supported features (e.g., language detection, timestamp granularity) compared to self-hosted Whisper.
  - **Mitigation:** Test thoroughly, document limitations, potentially allow fallback or alternative engines.
- **Dependency Hell:** Ensuring `ffmpeg`, Python, and library versions are compatible.
  - **Mitigation:** Clear setup instructions, virtual environments, `requirements.txt`, `requirements-dev.txt`.
- **Filename Generation:** Complex filenames from `yt-dlp` templates might cause issues.
  - **Mitigation:** `prepare_filename` helps. Sanitize filenames if necessary.
- **Error Reporting:** Providing clear messages for download, API, and processing errors in both CLI and Web UI.
- **Concurrency (Web UI):** Simple `threading` might not scale well under heavy load.
  - **Mitigation (Future):** Move to a proper task queue (Celery/RQ) as outlined in `developmentPlan.md`.

## 9. Future Enhancements

- **Web UI Improvements:** Implement cancel/retry buttons, transcript preview, better progress reporting (if feasible), persistent job history (DB/Redis).
- **Batching:** Process lists of URLs from a file or CLI arguments.
- **Persistence:** Use a database (`SQLite`, `PostgreSQL`) to store job status, metadata, and transcripts.
- **Async Operations:** Utilize `asyncio` for non-blocking downloads/uploads (especially for UI).
- **Advanced Features:** Translation (if supported by Lemonfox), speaker diarization (using `speaker_labels`), potentially alternative STT engines.
- **Output Formats:** Add `VTT` (supported by Lemonfox), `JSON`, potentially editor-specific formats.
- **Configuration:** Allow more `yt-dlp` and Lemonfox API options (e.g., `prompt`, `response_format`) via CLI or a config file.
- **Packaging:** Create distributable packages (`PyInstaller`, Docker).
- **Audio Pre-processing:** Add options for noise reduction or normalization.

## 10. Document History

- **v1.0 (2025-04-06):** Initial draft based on discussion. Updated to use Lemonfox API. Styled for readability.
- **v1.1 (2025-04-10):** Updated architecture, components, data flow, tech stack, setup, and risks to reflect implementation of local Web UI (FastAPI + JS).

## 11. Testing Strategy

A comprehensive testing strategy is outlined in `testPlan.md`. The approach includes:

- **Unit Testing:** Resides within the `transcriptor-core` project (`transcriptor-core/tests/unit/`). Uses `pytest` and `unittest.mock` to test individual functions of the core library in isolation.
- **Integration Testing:** Resides within the `transcriptor-core` project (`transcriptor-core/tests/integration/`). Uses `pytest` and mocking to verify the interaction and data flow within the `transcriptor_core.pipeline.run_pipeline` function, mocking external APIs and filesystem interactions.
- **End-to-End (E2E) Testing:** Resides within the `transcriptor-app` project (`transcriptor-app/tests/e2e/`). Uses `pytest` and `subprocess` to execute the CLI application (`python interfaces/cli/main.py ...`) and verify critical user workflows against real external services, using the installed `transcriptor-core` library. (Web UI E2E tests are not yet implemented).
- **Manual Functional Testing:** For exploratory testing, usability checks, and verifying scenarios not covered by automated tests (covers both CLI and Web UI).

Refer to `docs/testPlan.md` for full details and specific test cases. Unit/Integration tests are run within the `transcriptor-core` project, while E2E tests are run within the `transcriptor-app` project.
