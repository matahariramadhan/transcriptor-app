# Development Plan: TranscriptorApp Evolutionary Journey

**Version:** 4.0 (Local MVP -> Commercial Web App -> Mobile Clients)
**Date:** 2025-04-08

## 1. Goal

Outline the phased development journey for `transcriptor-app`, starting with an open-source, local desktop application (MVP), evolving into a scalable, commercial cloud-hosted web application, and finally extending reach with mobile clients (iOS/Android) utilizing the commercial backend.

## 2. Overall Strategy

This plan follows an iterative approach with a clear distinction between the initial open-source offering and the later commercial service:

1.  **Phase 1: Local Desktop Application (Open Source MVP):** Create an easy-to-use graphical application that runs entirely on the user's local machine, leveraging the existing core logic. License: MIT.
2.  **Phase 2: Commercial Scaled Web Application:** Build the cloud infrastructure, backend API, task processing system, and a sophisticated web frontend for a commercial service offering.
3.  **Phase 3: Commercial Mobile App Integration:** Develop native or cross-platform mobile apps that act as clients to the commercial backend API built in Phase 2.

## 3. Phase 1: Local Desktop Application (Open Source MVP)

- **Status:** Core implementation complete. Minor refinements (e.g., cancel/retry buttons, preview) and packaging remain.
- **Goal:** Provide a user-friendly graphical interface for the existing transcription functionality that runs locally on the user's computer. Build an initial user base and gather feedback. Release under MIT license.
- **Chosen Architecture:** **Local Web Server + Web UI**
  - A **FastAPI** server (`interfaces/web/main.py`) runs locally (bound to `127.0.0.1`), serving an HTML template (`interfaces/web/templates/index.html`) with static CSS/JS (`interfaces/web/static/`).
  - The user interacts with the application via their web browser pointing to `localhost`.
  - Background processing (`interfaces/web/processing.py`) is handled using Python's `threading` module to keep the UI responsive, calling the `core` logic.
- **Key Characteristics:**
  - Runs entirely on the user's machine.
  - Requires local installation of Python, `ffmpeg`, and dependencies (`requirements.txt` + FastAPI, Uvicorn).
  - Uses the user's local `LEMONFOX_API_KEY` (configured via `.env` initially, potentially UI later).
  - Processing (download, transcription) happens locally in background threads.
  - Output files saved to the user's local filesystem.
  - No cloud deployment or hosting required.
  - Codebase licensed under MIT.
- **Key Tasks:**
  1.  Set up FastAPI application structure within a `local_ui` directory.
  2.  Design and implement HTML templates and static files (CSS, JS) for the UI (URL input, options, status, results).
  3.  Develop FastAPI endpoints:
      - `/` (GET): Serve main HTML page.
      - `/submit_job` (POST): Accept URL/options, start processing in a background thread, return `job_id`.
      - `/status/<job_id>` (GET): Return job status (e.g., Pending, Processing, Completed, Failed).
      - `/result/<job_id>` (GET): Return results (text content or file paths) or error details.
  4.  Implement simple in-memory storage (`jobs` dictionary in `interfaces/web/main.py`) for tracking job status and results.
  5.  Adapt `core/pipeline.py` logic (via `interfaces/web/processing.py`) to run within a background thread, updating the shared status/result storage using callbacks.
  6.  Implement frontend JavaScript (`interfaces/web/static/*.js`) to call API endpoints, poll for status, and display results/errors dynamically.
  7.  Add FastAPI, Uvicorn, Jinja2 etc. to `requirements.txt`.
  8.  (Remaining) Package the application using **PyInstaller** (or similar) to create a distributable executable (documenting any separate `ffmpeg` installation needed).
  9.  Create clear installation and usage instructions for the packaged application.
  10. Publish code to a public repository (e.g., GitHub) with the MIT license.
- **Outcome:** A distributable, open-source desktop application (run via executable, accessed via localhost in browser) allowing users to transcribe videos locally using their own API key, with a non-blocking UI.

## 4. Phase 2: Commercial Scaled Web Application

- **Goal:** Build a robust, scalable, cloud-hosted web application for a commercial transcription service. This forms the core of the commercial offering.
- **Architecture:**
  - **Backend API:** Cloud-hosted API (Flask/FastAPI). Handles user requests, authentication, and job management.
  - **Task Queue System:** Decouple processing using a Message Broker (Redis/RabbitMQ) and Task Queue Library (Celery/RQ).
  - **Worker Processes:** Cloud-hosted workers execute the transcription pipeline (reusing logic from Phase 1 where applicable).
  - **Result Storage:** Cloud Storage (S3/GCS) for transcript files, Database (PostgreSQL/MongoDB) or Redis for job status/metadata.
  - **Frontend:** Sophisticated web UI built with a modern JavaScript framework (React, Vue, Svelte).
  - **Authentication:** Implement user accounts and secure authentication.
  - **(Optional) Billing:** Integrate a payment/subscription system.
- **Key Tasks:**
  1.  Design cloud infrastructure (compute, storage, database, broker).
  2.  Develop and deploy the Backend API with user authentication and job submission/status/result endpoints.
  3.  Set up and configure the Message Broker and Task Queue system.
  4.  Develop and deploy Worker processes, ensuring they have necessary dependencies (`ffmpeg`, `yt-dlp`) likely via containerization (Docker). Adapt Phase 1 processing logic for the worker context.
  5.  Implement robust result storage using Cloud Storage and/or a database.
  6.  Develop the sophisticated web frontend using React/Vue/Svelte.
  7.  Implement user authentication flows on both frontend and backend.
  8.  (Optional) Integrate billing/subscription management.
  9.  Set up monitoring, logging, and alerting for the cloud infrastructure.
- **Outcome:** A scalable, reliable, commercial web application offering transcription as a service, ready for user sign-ups and potential monetization.

## 5. Phase 3: Commercial Mobile App Integration

- **Goal:** Extend the commercial service reach by providing native or cross-platform mobile apps.
- **Architecture:**
  - **Backend:** Utilize the _existing_ commercial backend API developed in Phase 2.
  - **Mobile App:** Develop iOS/Android apps (Native or Cross-Platform) that act as clients to the backend API.
- **Key Tasks:**
  1.  Choose mobile development approach (Native vs. Cross-Platform).
  2.  Design mobile UI/UX consistent with the web application branding.
  3.  Develop mobile app screens (Login/Signup, URL Input, Job List/Status, Result Display/Download).
  4.  Implement API client logic within the mobile app to interact securely with the commercial backend API (handling authentication tokens).
  5.  Handle local state/storage for job tracking and potentially offline access if needed.
  6.  Implement platform-specific features (e.g., push notifications for job completion).
  7.  Test thoroughly across different devices and OS versions.
  8.  Deploy to App Store Connect / Google Play Console following platform guidelines.
- **Outcome:** Mobile applications providing users convenient, on-the-go access to the commercial transcription service.

## 6. Key Considerations (Across Phases)

- **Code Reusability:** Maximize reuse of the core Python transcription logic. (Note: As of v1.3.0, the core logic has been refactored into a separate `transcriptor-core` library to facilitate reuse between the Phase 1 local app and future Phase 2 backend workers).
- **Licensing:** Maintain a clear separation between the MIT-licensed Phase 1 codebase (and potentially the `transcriptor-core` library, depending on chosen license) and the proprietary/commercial codebase for Phase 2 and 3.
- **Infrastructure Costs:** Carefully plan and monitor cloud infrastructure costs, especially for Phase 2 and 3.
- **API Design:** Design the Phase 2 API thoughtfully, as it will serve both the web frontend and future mobile clients. Consider versioning early.
- **Security:** Implement robust security measures at all stages, particularly for the commercial phases involving user data and payments.
- **User Experience:** Ensure a smooth and intuitive user experience across desktop, web, and mobile platforms.

This evolutionary plan provides a structured path from an open-source local tool to a comprehensive commercial service with web and mobile interfaces.
