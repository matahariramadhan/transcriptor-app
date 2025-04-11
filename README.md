# TranscriptorApp

An application with command-line and local web interfaces to download video/audio from various platforms (YouTube, TikTok, Instagram, etc.) and generate transcripts using the Lemonfox API (an OpenAI Whisper-compatible endpoint).

Based on the technical design outlined in `docs/technical_design.md`.

## Features

- Downloads audio from one or more video URLs provided as arguments using `yt-dlp`.
- Processes multiple URLs sequentially, continuing even if one URL fails.
- Transcribes audio using the Lemonfox API (via the `openai` library).
- Supports selecting different Whisper models available on Lemonfox.
- Optionally requests speaker labels (if supported by the Lemonfox model).
- Outputs transcripts in `.txt` and `.srt` formats.
- Configurable output directory and filename template.
- Handles API keys securely via a `.env` file.

## Prerequisites

- **Python:** Version 3.9+ recommended.
- **pip:** Python package installer (usually comes with Python).
- **ffmpeg & ffprobe:** Required by `yt-dlp` for audio extraction and processing. Must be installed system-wide and accessible in your system's `PATH`. You can download builds from [ffmpeg.org](https://ffmpeg.org/download.html) or use a package manager (e.g., `apt install ffmpeg`, `brew install ffmpeg`).

## Installation

1.  **Clone the repository (or download the source code) for both `transcriptor-app` and `transcriptor-core`:**
    Make sure both project directories (`transcriptor-app` and `transcriptor-core`) are placed alongside each other (e.g., in the same parent directory).

    ```bash
    # If you have git installed
    # git clone <repository_url>
    # cd transcriptor-app
    ```

    _(Assuming you already have the code in the current directory)_

2.  **Create and activate a virtual environment (recommended):**

    ```bash
    # Create the environment
    python -m venv .venv

    # Activate it:
    # Linux/macOS
    source .venv/bin/activate
    # Windows (Command Prompt/PowerShell)
    # .venv\Scripts\activate
    ```

3.  **Install dependencies:**

    - **For running the application:**

    ```bash
    # Installs app dependencies and the local transcriptor-core in editable mode
    pip install -r requirements.txt
    ```

    - **For development (running tests):**
      You also need to install development dependencies for _both_ projects:
      ```bash
      # In transcriptor-app directory:
      pip install -r requirements-dev.txt
      # In transcriptor-core directory:
      cd ../transcriptor-core
      pip install -r requirements-dev.txt
      cd ../transcriptor-app
      ```

## Configuration

1.  **Copy the example environment file:**

    ```bash
    cp .env.example .env
    ```

    _(On Windows, use `copy .env.example .env`)_

2.  **Edit the `.env` file:**
    Open the newly created `.env` file in a text editor.
    Replace `YOUR_LEMONFOX_API_KEY_HERE` with your actual API key obtained from [Lemonfox AI](https://lemonfox.ai/).
    ```dotenv
    LEMONFOX_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    ```
    Save the file. The `.gitignore` file is already configured to prevent accidentally committing your `.env` file.

## Usage

This application provides two interfaces: a Command-Line Interface (CLI) and a local Web User Interface (Web UI). Run either from your terminal within the activated virtual environment.

### Command-Line Interface (CLI)

**Basic Example (Single URL):**

```bash
python interfaces/cli/main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

This will:

- Download the audio from the YouTube URL.
- Transcribe it using the default model (`whisper-1`).
- Save `transcript.txt` and `transcript.srt` (using default filename template) into the `./transcripts/` directory.
- Save the intermediate audio file in `./transcripts/_audio_files/`.
- Delete the intermediate audio file upon completion.

**Example with Multiple URLs and Options:**

```bash
python interfaces/cli/main.py "URL_1" "URL_2" "URL_3" \
    --output-dir ./my_output \
    --model whisper-large-v3 \
    --formats srt \
    --audio-format opus \
    --output-filename-template "%(channel)s - %(title)s" \
    --language en \
    --speaker-labels \
    --keep-audio \
    --verbose
```

This command:

- Processes `URL_1`, `URL_2`, and `URL_3` sequentially.
- Saves output for each URL to the `./my_output` directory.
- Uses the `whisper-large-v3` model for each transcription.
- Only generates an `.srt` file for each URL.
- Extracts intermediate audio as `.opus`.
- Names the output file like `Channel Name - Video Title.srt`.
- Hints the language is English.
- Requests speaker labels.
- Keeps the intermediate `.opus` file.
- Enables verbose logging.

## Options

Run the following command to see all available command-line options:

```bash
python interfaces/cli/main.py --help
```

### Web User Interface (Web UI)

This provides a graphical interface accessible via your web browser.

1.  **Start the Server:**
    Run the following command from the project root directory:

    ```bash
    uvicorn interfaces.web.main:app --reload --host 127.0.0.1 --port 8000
    ```

    _(The `--reload` flag automatically restarts the server when code changes are detected, useful for development.)_

2.  **Access the UI:**
    Open your web browser and navigate to: `http://127.0.0.1:8000`

3.  **Using the UI:**
    - Enter one or more video/audio URLs in the input fields. Use the "+ Add another URL" button for multiple URLs.
    - Configure transcription settings like the Whisper model and desired output formats (TXT, SRT).
    - Use "Advanced Options" to set language hints, request speaker labels, or choose to keep intermediate audio files.
    - Click "Start Transcription".
    - Monitor job progress in the "Active Jobs" list. Use the Cancel button (<i class="fas fa-times"></i>) to stop a pending or processing job, or the Retry button (<i class="fas fa-redo"></i>) to resubmit a failed job.
    - Once completed, download links for the transcript files will appear on the job card. Output files are saved locally in the `web_outputs/<job_id>/` directory within the project folder.

### Running the Packaged Application (Experimental)

For easier distribution without requiring users to install Python or dependencies (except `ffmpeg`), you can build a standalone executable using PyInstaller.

1.  **Prerequisites for Building:**
    - Ensure you have completed the standard installation steps above, including installing development dependencies (`pip install -r requirements-dev.txt`).
    - Make sure `pyinstaller` is installed in your virtual environment.
2.  **Build the Executable:**
    - Navigate to the `transcriptor-app` directory in your terminal (with the virtual environment activated).
    - Run the PyInstaller build command using the provided spec file:
      ```bash
      pyinstaller run_web_ui.spec
      ```
    - This will create `build` and `dist` directories. The packaged application will be inside `dist/run_web_ui`.
3.  **Running the Packaged App:**
    - **Important:** Ensure `ffmpeg` and `ffprobe` are installed system-wide and accessible in your system's `PATH`. This is still required by the packaged application.
    - Copy the `.env` file (containing your `LEMONFOX_API_KEY`) into the `dist/run_web_ui` directory alongside the executable.
    - Navigate to the `dist/run_web_ui` directory in your terminal.
    - Run the executable:
      ```bash
      # On Linux/macOS
      ./run_web_ui
      # On Windows
      # .\run_web_ui.exe
      ```
    - Access the UI in your browser at `http://127.0.0.1:8000` as usual. Output files will be created within the `dist/run_web_ui/_internal/web_outputs/` directory.

**Note:** Packaging complex applications with web servers and background threads can sometimes have platform-specific issues. Test thoroughly on your target operating system.

## Project Structure

The project is organized into the following main directories:

- `interfaces/`: Contains different ways to interact with the core engine:
  - `cli/`: The command-line interface (`main.py`).
  - `web/`: The local web user interface (FastAPI backend, JS frontend).
- `tests/`: Contains end-to-end tests (`e2e/`) for the application. Unit and integration tests reside within the `transcriptor-core` library project.
- `web_outputs/`: Default directory where output files from the web UI are saved (created automatically).
- `transcriptor-core/` (Separate Project): Contains the core transcription engine logic (downloading, transcribing, formatting) as an installable library. Includes its own unit and integration tests.

## Testing

This project uses `pytest`.

1.  **Install Development Dependencies:**
    Make sure you have activated your virtual environment and installed development dependencies for _both_ `transcriptor-app` and `transcriptor-core` as described in the Installation section.

2.  **Run Tests:**

    - **Core Unit & Integration Tests:** Navigate to the `transcriptor-core` directory and run its tests:
      ```bash
      cd ../transcriptor-core
      python -m pytest
      cd ../transcriptor-app
      ```
    - **Application End-to-End (E2E) Tests:** Run from the `transcriptor-app` root directory:

      ```bash
      # Requires network and API key in .env
      python -m pytest tests/e2e/
      ```

See `docs/testPlan.md` for a detailed overview of the testing strategy. Unit and integration tests for the core logic reside within the `transcriptor-core` project. E2E tests for the application reside here in `transcriptor-app/tests/e2e/`.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on reporting issues, suggesting features, and submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
