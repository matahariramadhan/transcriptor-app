# TranscriptorApp

A command-line application to download video/audio from various platforms (YouTube, TikTok, Instagram, etc.) and generate transcripts using the Lemonfox API (an OpenAI Whisper-compatible endpoint).

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

1.  **Clone the repository (or download the source code):**

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
      pip install -r requirements.txt
      ```
    - **For development (including tests):**
      ```bash
      pip install -r requirements.txt -r requirements-dev.txt
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
    - Monitor job progress in the "Active Jobs" list.
    - Once completed, download links for the transcript files will appear on the job card. Output files are saved locally in the `web_outputs/<job_id>/` directory within the project folder.

## Project Structure

The project is organized into the following main directories:

- `core/`: Contains the core transcription engine logic (downloading, transcribing, formatting).
- `interfaces/`: Contains different ways to interact with the `core` engine:
  - `cli/`: The command-line interface (`main.py`).
  - `web/`: The local web user interface.
    - `main.py`: FastAPI backend server.
    - `processing.py`: Background job processing logic.
    - `static/`: Contains CSS and JavaScript files (`main.js`, `apiClient.js`, etc.).
    - `templates/`: Contains the HTML template (`index.html`).
- `tests/`: Contains unit, integration, and end-to-end tests.
- `web_outputs/`: Default directory where output files from the web UI are saved (created automatically).

## Testing

This project uses `pytest` for unit and integration testing.

1.  **Install Development Dependencies:**
    Make sure you have activated your virtual environment (`source .venv/bin/activate`). Then install the necessary packages:

    ```bash
    pip install -r requirements.txt -r requirements-dev.txt
    ```

2.  **Run Tests:**
    Execute the following command from the project root directory to run all tests (unit and integration):

    ```bash
    pytest
    ```

    Or for more detailed output:

    ```bash
    pytest -v
    ```

    **Running Specific Test Types:**

    ```bash
    # Run only unit tests
    pytest tests/unit/
    # Run only integration tests
    pytest tests/integration/
    # Run only end-to-end tests (requires network and API key in .env)
    pytest tests/e2e/
    ```

    **Running Tests with Coverage:**

    To measure code coverage using `pytest-cov` (included in development dependencies), run:

    ```bash
    pytest --cov=core tests/
    ```

    This will run all tests (unit and integration by default, or specify paths) in the `tests/` directory and report coverage for the `core/` directory.

See `docs/testPlan.md` for a detailed overview of the testing strategy (unit, integration, E2E) and the structure of the tests (`tests/unit/`, `tests/integration/`, `tests/e2e/`).

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on reporting issues, suggesting features, and submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
