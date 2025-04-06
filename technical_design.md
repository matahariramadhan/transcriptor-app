# Technical Design Document: TranscriptorApp

**Version:** 1.0
**Date:** 2025-04-06

## 1. Introduction / Overview

### 1.1 Purpose

This document outlines the technical design for `TranscriptorApp`, a command-line application designed to generate transcripts from video URLs.

### 1.2 Application Description

`TranscriptorApp` accepts URLs from popular video platforms (YouTube, TikTok, Instagram), downloads the associated video content, extracts the audio, transcribes the audio to text using the Lemonfox API (an OpenAI-compatible Whisper endpoint), and outputs the transcript in various formats (`TXT`, `SRT`).

### 1.3 Goals

- Provide a simple command-line interface for users.
- Reliably download content from specified platforms.
- Accurately transcribe audio content.
- Offer common transcript output formats.
- Maintain a modular and extensible codebase using open-source libraries.

### 1.4 Target Audience

Developers involved in the implementation, testing, and future maintenance of `TranscriptorApp`.

## 2. Goals and Scope

### 2.1 In Scope (Version 1.0)

- **Input:** Accept single video URLs via command-line arguments. Supported platforms: YouTube, TikTok, Instagram (leveraging `yt-dlp`'s capabilities).
- **Downloading:** Utilize `yt-dlp`'s Python API to download and extract audio.
- **Audio Format:** Extract audio into common formats like `MP3` or `Opus` (configurable).
- **Transcription:** Use the standard `openai` Python library, configured to point to the Lemonfox API endpoint, to perform transcription. Allow selection of Whisper model size (e.g., `tiny`, `base`, `small`, `medium`, `large` - assuming Lemonfox supports these via the `model` parameter) via CLI argument. Optionally support Lemonfox features like `speaker_labels`.
- **Output Formats:** Generate transcripts in plain text (`.txt`) and SubRip Subtitle (`.srt`) formats. Allow selection of desired formats via CLI argument.
- **Output Location:** Save output files to a user-specified directory or a default location.
- **Modularity:** Structure the code into distinct Python modules for downloading, transcription, and formatting.
- **Technology:** Rely on Python and specified open-source libraries.
- **Interface:** Command-Line Interface (CLI).

### 2.2 Out of Scope (Version 1.0)

- Graphical User Interface (GUI) or Web User Interface (Web UI).
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

The application follows a pipeline architecture initiated from a command-line interface.

- **CLI Layer:** Parses user input (URL, options).
- **Orchestration Layer:** Coordinates the workflow, calling modules sequentially.
- **Downloader Module:** Interacts with `yt-dlp` to fetch and extract audio.
- **Transcriber Module:** Interacts with the Lemonfox API via the configured `openai` library client.
- **Formatter Module:** Processes transcription output into desired file formats.
- **Filesystem:** Reads/writes audio and transcript files.

### 3.2 Modularity

The application will be divided into the following Python modules:

- `main.py`: Handles CLI parsing (`argparse`), orchestrates the process flow, manages overall status reporting.
- `downloader.py`: Contains the `download_audio_python_api` function using `yt_dlp.YoutubeDL` and its associated helper classes/functions (like loggers/hooks). Responsible for fetching the URL and outputting an audio file path.
- `transcriber.py`: Contains the `transcribe_audio_lemonfox` function using the `openai` library configured for Lemonfox. Takes an audio path, returns a structured transcription result.
- `formatter.py`: Contains `generate_txt`, `generate_srt`, and potentially other format-generating functions. Takes the transcription result, outputs formatted files.
- `utils.py` (Optional): For shared helper functions or constants.

### 3.3 Data Flow

1.  User executes `python main.py <URL> [options]`.
2.  `main.py` parses arguments.
3.  `main.py` calls `downloader.download_audio_python_api(url, output_options)`.
4.  `downloader.py` uses `yt-dlp` API to download/extract audio, saves file (e.g., `audio_files_api/youtube_VIDEOID.mp3`).
5.  `downloader.py` returns the audio file path (string) to `main.py`.
6.  `main.py` calls `transcriber.transcribe_audio_lemonfox(audio_path, model_name, api_key, **kwargs)`. _(Note: API key management needs secure handling)_.
7.  `transcriber.py` initializes the `openai` client with the Lemonfox base URL (`https://api.lemonfox.ai/v1`) and API key.
8.  `transcriber.py` calls `client.audio.transcriptions.create()` with the audio file, model, and other optional parameters (like `language`, `speaker_labels`).
9.  `transcriber.py` returns the transcription result (dictionary, potentially including speaker labels if requested) to `main.py`.
10. `main.py` iterates through desired output formats.
11. `main.py` calls `formatter.generate_srt(transcript_result, output_path_srt)`.
12. `formatter.py` formats data and writes `.srt` file.
13. `main.py` calls `formatter.generate_txt(transcript_result, output_path_txt)`.
14. `formatter.py` formats data and writes `.txt` file.
15. `main.py` reports completion status.
16. (Optional) `main.py` or modules can clean up intermediate audio files if desired.

### 3.4 Error Handling Strategy

- Each module function (`download_audio_python_api`, `transcribe_audio_lemonfox`, etc.) will use `try...except` blocks to catch relevant exceptions (e.g., `yt_dlp.utils.DownloadError`, `openai.APIError`, `FileNotFoundError`, general `Exception`).
- Errors will be logged using Python's `logging` module.
- Functions will return `None` or raise a custom application exception upon failure to signal the orchestrator (`main.py`) to halt the process for that URL.
- `main.py` will catch errors from module calls and report failure to the user with informative messages, including relevant error details where possible.

## 4. Component Breakdown

### 4.1 `main.py` (CLI & Orchestrator)

- **Responsibilities:** Parse CLI args (`url`, `--output-dir`, `--model`, `--formats`, `--audio-format`). Validate inputs. Call downloader, transcriber, formatter in sequence. Handle errors returned from modules. Print status messages.
- **Interface:** Uses `argparse`.

### 4.2 `downloader.py` (Downloader Module)

- **Responsibilities:** Implement `download_audio_python_api` using `yt_dlp.YoutubeDL`. Configure `ydl_opts` based on input parameters (output path/template, audio format). Use `FFmpegExtractAudio` postprocessor. Determine and return the final audio file path reliably (using `prepare_filename`). Handle `yt-dlp` specific errors.
- **Interface:** `download_audio_python_api(url: str, output_dir: str, audio_format: str, output_template: str) -> Optional[str]`

### 4.3 `transcriber.py` (Transcriber Module)

- **Responsibilities:** Implement `transcribe_audio_lemonfox`. Initialize the `openai` client with the Lemonfox base URL (`https://api.lemonfox.ai/v1`) and the user's Lemonfox API key (passed securely, e.g., via environment variable or config). Call `client.audio.transcriptions.create()` passing the audio file, model name, and any other desired parameters (e.g., `language`, `response_format`, `speaker_labels`). Return the result dictionary received from the API. Handle API-related exceptions (e.g., authentication errors, rate limits, network issues).
- **Interface:** `transcribe_audio_lemonfox(audio_path: str, model_name: str, api_key: str, **kwargs) -> Optional[dict]` (Example signature, actual implementation might vary based on how API key is managed).

### 4.4 `formatter.py` (Formatter Module)

- **Responsibilities:** Implement `generate_txt` and `generate_srt`. Take the structured result from the transcriber. Format timestamps correctly for SRT. Write output to specified file paths.
- **Interface:** `generate_txt(transcript_result: dict, output_path: str)`, `generate_srt(transcript_result: dict, output_path: str)`

## 5. Technology Stack

- **Language:** Python (Version 3.9+ recommended)
- **Core Libraries:**
  - `yt-dlp`: ==2025.03.31
  - `openai`: ==1.70.0 (for interacting with the Lemonfox API)
- **Standard Libraries:** `os`, `argparse`, `datetime`, `logging`, `json` (optional)
- **External Dependencies:**
  - `ffmpeg` / `ffprobe`: Latest stable version, must be installed system-wide and accessible in the `PATH`. (Custom `yt-dlp/FFmpeg-Builds` recommended if encountering issues).

### 5.1 Dependencies Summary

- **Programming Language:**
  - Python (Version 3.9+ recommended)
- **Core Python Libraries (via `pip` / `requirements.txt`):**
  - `yt-dlp`: ==2025.03.31
  - `openai`: ==1.70.0
- **Standard Python Libraries (Built-in):**
  - `os`
  - `argparse`
  - `datetime`
  - `logging`
  - `json` (optional)
- **External System Dependencies (Manual Installation Required):**
  - `ffmpeg` / `ffprobe`: Latest stable version, accessible in system `PATH`.
- **Development/Setup Tools:**
  - `pip`
  - `Git` (Optional)

## 6. Data Structures

- **Configuration:** `argparse.Namespace` object holding CLI arguments. `ydl_opts` dictionary for `yt-dlp`. Lemonfox API Key (managed securely, e.g., env var `LEMONFOX_API_KEY`).
- **Intermediate:** Audio file path (string). Lemonfox transcription result (dict): Structure depends on `response_format` and `speaker_labels`. Example (with `speaker_labels=true`):
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
  1.  Obtain code (e.g., `git clone ...`).
  2.  Navigate to project directory.
  3.  Create virtual environment: `python -m venv .venv`
  4.  Activate environment: `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows).
  5.  Install Python dependencies: `pip install -r requirements.txt` (A `requirements.txt` file should list `yt-dlp`, `openai`).
  6.  Ensure Lemonfox API Key is available (e.g., set as an environment variable `LEMONFOX_API_KEY`).
- **Running:**
  ```bash
  python main.py <URL> --model whisper-1 --formats txt srt --output-dir ./transcripts
  ```

## 8. Potential Challenges and Risks

- **Platform API Changes:** `yt-dlp` breakage due to YouTube/TikTok/Instagram updates.
  - **Mitigation:** Frequent `yt-dlp` updates, use `--update-to nightly`.
- **Lemonfox API:** Changes to API endpoints, parameters, response formats, or pricing. Service availability issues. Rate limiting.
  - **Mitigation:** Monitor Lemonfox documentation, implement robust error handling and retries if applicable.
- **API Key Management:** Need for secure storage and retrieval of the Lemonfox API key.
  - **Mitigation:** Use environment variables, configuration files with appropriate permissions, or dedicated secrets management.
- **Network Issues:** General connectivity problems affecting downloads or API calls.
  - **Mitigation:** Standard network error handling, retries (`yt-dlp` has built-in retries).
- **Transcription Quality/Features:** Potential differences in accuracy or supported features (e.g., language detection, timestamp granularity) compared to self-hosted Whisper.
  - **Mitigation:** Test thoroughly, document limitations, potentially allow fallback or alternative engines.
- **Dependency Hell:** Ensuring `ffmpeg`, Python, and library versions are compatible.
  - **Mitigation:** Clear setup instructions, virtual environments, `requirements.txt`.
- **Filename Generation:** Complex filenames from `yt-dlp` templates might cause issues.
  - **Mitigation:** `prepare_filename` helps. Use simpler templates if needed.
- **Error Reporting:** Providing clear messages for both download and API errors.

## 9. Future Enhancements

- **UI:** Develop a Web UI (`Flask`/`Streamlit`) or Desktop GUI (`PyQt`/`Tkinter`).
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
