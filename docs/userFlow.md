# User Flow Document: TranscriptorApp

**Version:** 1.0
**Date:** 2025-04-09

## 1. Introduction

This document describes the typical user journeys when interacting with `TranscriptorApp`, covering both the CLI and the Local Web UI.

## 2. CLI User Flow

1.  **Prerequisites:**
    - User has installed Python, pip, and `ffmpeg`/`ffprobe`.
    - User has cloned the repository or downloaded the source code.
    - User has created and activated a virtual environment (recommended).
    - User has installed dependencies (`pip install -r requirements.txt`).
    - User has configured their `LEMONFOX_API_KEY` in a `.env` file in the project root.
2.  **Execute Command:** User runs the CLI script from the terminal within the project directory and activated environment, providing URLs and options:
    ```bash
    python interfaces/cli/main.py <URL1> [URL2...] [options...]
    ```
3.  **Processing:**
    - The script parses arguments.
    - It processes each URL sequentially.
    - Logs for download, transcription, and formatting appear in the terminal.
4.  **Results:**
    - Transcript files (`.txt`, `.srt`, etc.) are saved to the specified output directory (default: `./transcripts/`).
    - A final summary of processed and failed URLs is printed to the terminal.
    - The script exits with code 0 on success or non-zero if any URLs failed.

## 3. Local Web UI User Flow

This flow describes using the graphical interface running locally via the built-in web server.

1.  **Prerequisites:**
    - User has installed Python, pip, and `ffmpeg`/`ffprobe`.
    - User has cloned the repository or downloaded the source code.
    - User has created and activated a virtual environment (recommended).
    - User has installed dependencies (`pip install -r requirements.txt`).
    - User has configured their `LEMONFOX_API_KEY` in a `.env` file in the project root.
2.  **Launch Server:** User runs the Uvicorn server from the terminal within the project directory and activated environment:
    ```bash
    uvicorn interfaces.web.main:app --host 127.0.0.1 --port 8000
    ```
3.  **Access UI:**
    - User opens their web browser and navigates to `http://127.0.0.1:8000`.
4.  **Interact with Web UI:**
    - User sees the main application interface in their browser.
    - User sees the main application interface.
    - User enters one or more video URLs into the input field(s), using the "Add another URL" button if needed.
    - User selects desired options (output formats, model, keep audio, etc.) using the form controls. Advanced options can be revealed.
    - User clicks the "Start Transcription" button.
5.  **Job Submission & Processing:**
    - The frontend JavaScript sends the URLs and options to the local `/submit_job` API endpoint.
    - The backend (`processing.py`) starts processing the job in a background thread.
    - A new job card appears at the top of the "Active Jobs" list in the UI, initially showing "Pending".
6.  **Monitor Progress:**
    - The frontend JavaScript polls the `/status/<job_id>` endpoint periodically (e.g., every second).
    - The job card updates dynamically to show the current status (Downloading, Transcribing, Formatting, Cancelling, Cancelled) and updates the progress bar accordingly.
    - **Cancel Action:** While the job is in a pending or processing state (Downloading, Transcribing, Formatting), the user can click the Cancel button (<i class="fas fa-times"></i>) on the job card. The UI updates to "Cancelling", and the backend attempts to stop the job at the next checkpoint. The final status will become "Cancelled".
7.  **View Results / Handle Failures:**
    - When polling indicates a job status is "Completed":
      - The job card updates to show "Completed" status and reveals download buttons/links for the generated files (e.g., TXT, SRT). Files are located in the `web_outputs/<job_id>/` directory.
      - A preview button might be available (functionality TBD).
    - If polling indicates a job status is "Failed":
      - The job card updates to show "Failed" status and displays an error message.
      - **Retry Action:** The user can click the Retry button (<i class="fas fa-redo"></i>) on the failed job card. This submits a _new_ job with the same parameters. The old card is marked as "Retried" (or similar), and a new job card appears for the retry attempt.
8.  **Stop Server:** User stops the local server by pressing `Ctrl+C` in the terminal where Uvicorn was launched.
