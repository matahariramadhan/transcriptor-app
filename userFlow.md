# User Flow Document: TranscriptorApp

**Version:** 1.0
**Date:** 2025-04-09

## 1. Introduction

This document describes the typical user journey when interacting with the planned Phase 1 Local Desktop Application of `TranscriptorApp`.

## 2. Phase 1: Local Desktop Application (Web UI via Local Server) - Planned

This flow describes using the planned graphical interface running locally.

1.  **Prerequisites:**
    - User has installed the packaged application (e.g., via an installer or by running the executable created by PyInstaller).
    - User has ensured `ffmpeg`/`ffprobe` are installed system-wide.
    - User has configured their `LEMONFOX_API_KEY` (either via a `.env` file placed alongside the executable or potentially through a first-run UI setup).
2.  **Launch Application:** User double-clicks the application executable or runs it from the terminal.
3.  **Application Starts:**
    - A local FastAPI server starts in the background (likely hidden from the user).
    - The user's default web browser automatically opens to `http://127.0.0.1:<port>` (e.g., `http://127.0.0.1:8000`).
4.  **Interact with Web UI:**
    - User sees the main application interface in their browser.
    - User enters one or more video URLs into an input field.
    - User selects desired options (output formats, model, keep audio, etc.) using UI elements (checkboxes, dropdowns, text fields).
    - User clicks a "Submit" or "Start Transcription" button.
5.  **Job Submission & Processing:**
    - The frontend JavaScript sends the URLs and options to the local `/submit_job` API endpoint.
    - The backend starts processing the job(s) in background threads.
    - The UI updates to show the job(s) as "Pending" or "Processing" (e.g., in a list). The UI might poll the `/status/<job_id>` endpoint periodically.
6.  **Monitor Progress:**
    - User can see the status of each submitted job in the UI (e.g., Downloading, Transcribing, Formatting, Completed, Failed).
    - Progress indicators might be shown.
7.  **View Results:**
    - When a job status changes to "Completed", the UI provides access to the results:
      - Displaying the transcript text directly in the UI.
      - Providing download links for the generated `.txt` and/or `.srt` files (which were saved locally by the backend).
    - If a job status changes to "Failed", the UI displays an error message indicating the reason for failure (obtained from `/result/<job_id>` or `/status/<job_id>`).
8.  **Close Application:** User closes the browser tab/window. User stops the local server (e.g., by closing the terminal window it was launched from, or via a "Quit" option if the packaged app provides one).
