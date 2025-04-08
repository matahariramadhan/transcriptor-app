# TranscriptorApp

A command-line application to download video/audio from various platforms (YouTube, TikTok, Instagram, etc.) and generate transcripts using the Lemonfox API (an OpenAI Whisper-compatible endpoint).

Based on the technical design outlined in `technical_design.md`.

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

Run the application from your terminal within the activated virtual environment.

**Basic Example (Single URL):**

```bash
python src/main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

This will:

- Download the audio from the YouTube URL.
- Transcribe it using the default model (`whisper-1`).
- Save `transcript.txt` and `transcript.srt` (using default filename template) into the `./transcripts/` directory.
- Save the intermediate audio file in `./transcripts/_audio_files/`.
- Delete the intermediate audio file upon completion.

**Example with Multiple URLs and Options:**

```bash
python src/main.py "URL_1" "URL_2" "URL_3" \
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
python src/main.py --help
```

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
    pytest --cov=src tests/
    ```

    This will run all tests (unit and integration by default, or specify paths) in the `tests/` directory and report coverage for the `src/` directory.

See `testPlan.md` for a detailed overview of the testing strategy (unit, integration, E2E) and the structure of the tests (`tests/unit/`, `tests/integration/`, `tests/e2e/`).

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on reporting issues, suggesting features, and submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
