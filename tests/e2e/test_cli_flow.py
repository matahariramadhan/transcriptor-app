import subprocess
import os
import sys
import pytest
import shutil
from pathlib import Path

# Define paths relative to the project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
VENV_PYTHON_PATH = PROJECT_ROOT / ".venv" / "bin" / "python" # Assumes Linux/macOS structure
MAIN_SCRIPT_PATH = PROJECT_ROOT / "src" / "main.py"

# --- Test URLs (Replace with actual stable URLs) ---
# Using a known short, public domain video if possible
# Example: YouTube video ID for "Big Buck Bunny" (check copyright/terms)
# Or a specific test video you upload.
# Provided URLs:
TEST_URL_YOUTUBE_SHORT = "https://youtube.com/shorts/qx09DLXxVug?si=AaJm9rVgO1O8j6Ln"
TEST_URL_TIKTOK = "https://vt.tiktok.com/ZSrDK18C7/"
INVALID_TEST_URL = "https://example.com/invalid-video-url" # Keep for failure tests

# --- Helper Function ---

def run_transcriptor_cli(
    args: list[str],
    output_dir: Path,
    # api_key: str | None = "DUMMY_API_KEY_FOR_NOW", # Removed - rely on .env loading
    timeout: int = 120 # Generous timeout for download/transcription
) -> subprocess.CompletedProcess:
    """
    Runs the main.py script as a subprocess.
    Assumes LEMONFOX_API_KEY is loaded from .env by the script itself.
    """
    # Ensure the venv python exists
    if not VENV_PYTHON_PATH.exists():
        pytest.fail(f"Virtual environment Python not found at: {VENV_PYTHON_PATH}")

    command = [
        str(VENV_PYTHON_PATH), # Use the virtual environment's Python
        str(MAIN_SCRIPT_PATH),
        *args,
        "--output-dir", str(output_dir) # Ensure output goes to temp dir
    ]

    # The subprocess should inherit the environment, including vars loaded by pytest
    # or the shell environment, which allows the script's dotenv loading to work.
    # We don't need to manipulate the API key here anymore.
    env = os.environ.copy()

    print(f"\nRunning command: {' '.join(command)}") # For debugging
    print(f"Output directory: {output_dir}")
    # print(f"API Key Provided: {'Yes' if api_key else 'No'}") # Removed

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env=env, # Pass the current environment
        cwd=PROJECT_ROOT, # Run from project root
        timeout=timeout
    )

    # Print output for easier debugging during test runs
    print(f"Exit Code: {result.returncode}")
    if result.stdout:
        print(f"stdout:\n---\n{result.stdout}\n---")
    if result.stderr:
        print(f"stderr:\n---\n{result.stderr}\n---")

    return result

# --- Test Fixtures ---

@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Creates a temporary directory for test outputs."""
    output_dir = tmp_path / "e2e_output"
    output_dir.mkdir()
    print(f"Created temp output dir: {output_dir}")
    # No need to yield and clean, tmp_path handles it
    return output_dir

# --- Test Cases ---

# @pytest.mark.e2e # Optional: Mark tests as E2E
def test_smoke_single_url_default_options(temp_output_dir: Path):
    """
    Basic smoke test: Run with one URL and default settings.
    Verifies successful execution and creation of default output files for a YouTube Short.
    """
    # Check if the main API key is loaded from .env
    api_key = os.getenv("LEMONFOX_API_KEY")
    if not api_key:
        pytest.skip("Skipping E2E test: LEMONFOX_API_KEY environment variable not found (expected in .env).")

    args = [TEST_URL_YOUTUBE_SHORT]
    # Don't pass api_key explicitly to the helper anymore
    result = run_transcriptor_cli(args, temp_output_dir)

    assert result.returncode == 0, f"CLI command failed with exit code {result.returncode}"

    # Check for default output files (using the default template)
    # We need to know the video ID or title to predict the exact filename
    # For now, let's check if *any* .txt and .srt file exist
    # A more robust check would parse the expected filename from the URL/ID
    output_files = list(temp_output_dir.glob('*'))
    txt_files = [f for f in output_files if f.suffix == '.txt']
    srt_files = [f for f in output_files if f.suffix == '.srt']

    assert len(txt_files) >= 1, "Expected at least one .txt file to be created"
    assert len(srt_files) >= 1, "Expected at least one .srt file to be created"

    # Check content basics (optional but good)
    if txt_files:
        txt_content = txt_files[0].read_text()
        assert len(txt_content) > 10, f"TXT file {txt_files[0].name} seems too short or empty"
    if srt_files:
        srt_content = srt_files[0].read_text()
        assert "-->" in srt_content, f"SRT file {srt_files[0].name} does not contain '-->'"

    # Check if audio subdirectory was created and then removed (default behavior)
    audio_subdir = temp_output_dir / "_audio_files"
    assert not audio_subdir.exists(), "Intermediate audio directory '_audio_files' should have been removed by default"


# @pytest.mark.e2e
def test_smoke_single_url_tiktok(temp_output_dir: Path):
    """
    Basic smoke test for a TikTok URL.
    """
    api_key = os.getenv("LEMONFOX_API_KEY")
    if not api_key:
        pytest.skip("Skipping E2E test: LEMONFOX_API_KEY environment variable not found.")

    args = [TEST_URL_TIKTOK]
    result = run_transcriptor_cli(args, temp_output_dir)

    assert result.returncode == 0, f"CLI command failed with exit code {result.returncode}"

    output_files = list(temp_output_dir.glob('*'))
    txt_files = [f for f in output_files if f.suffix == '.txt']
    srt_files = [f for f in output_files if f.suffix == '.srt']

    assert len(txt_files) >= 1, "Expected at least one .txt file for TikTok URL"
    assert len(srt_files) >= 1, "Expected at least one .srt file for TikTok URL"

    audio_subdir = temp_output_dir / "_audio_files"
    assert not audio_subdir.exists(), "Intermediate audio directory '_audio_files' should have been removed"


# @pytest.mark.e2e
def test_multiple_urls_success(temp_output_dir: Path):
    """
    Test processing multiple valid URLs successfully.
    """
    api_key = os.getenv("LEMONFOX_API_KEY")
    if not api_key:
        pytest.skip("Skipping E2E test: LEMONFOX_API_KEY environment variable not found.")

    args = [TEST_URL_YOUTUBE_SHORT, TEST_URL_TIKTOK]
    result = run_transcriptor_cli(args, temp_output_dir)

    assert result.returncode == 0, f"CLI command failed processing multiple URLs"

    # Expect output files for both URLs (at least 2 txt, 2 srt)
    output_files = list(temp_output_dir.glob('*'))
    txt_files = [f for f in output_files if f.suffix == '.txt']
    srt_files = [f for f in output_files if f.suffix == '.srt']

    # Check based on the default filename template: "%(title)s [%(id)s]"
    # We'd need to know the actual titles/ids to be precise.
    # For now, just check counts.
    assert len(txt_files) >= 2, "Expected at least two .txt files for two URLs"
    assert len(srt_files) >= 2, "Expected at least two .srt files for two URLs"

    # Check summary log output (optional but good)
    assert "Batch Summary" in result.stdout
    assert "Total URLs attempted: 2" in result.stdout
    assert "Successfully processed: 2" in result.stdout
    # Check summary log output (now expected on stdout)
    assert "Batch Summary" in result.stdout
    assert "Total URLs attempted: 2" in result.stdout
    assert "Successfully processed: 2" in result.stdout
    # Check that the failure message is NOT in stdout or stderr
    assert "Failed URLs" not in result.stdout
    assert "Failed URLs" not in result.stderr


    audio_subdir = temp_output_dir / "_audio_files"
    assert not audio_subdir.exists(), "Intermediate audio directory should be removed after processing multiple URLs"


# @pytest.mark.e2e
def test_options_format_srt_only(temp_output_dir: Path):
    """Test using --formats srt option."""
    api_key = os.getenv("LEMONFOX_API_KEY")
    if not api_key:
        pytest.skip("Skipping E2E test: LEMONFOX_API_KEY environment variable not found.")

    args = [TEST_URL_YOUTUBE_SHORT, "--formats", "srt"]
    result = run_transcriptor_cli(args, temp_output_dir)

    assert result.returncode == 0

    output_files = list(temp_output_dir.glob('*'))
    txt_files = [f for f in output_files if f.suffix == '.txt']
    srt_files = [f for f in output_files if f.suffix == '.srt']

    assert len(txt_files) == 0, "Expected no .txt file when format is only srt"
    assert len(srt_files) >= 1, "Expected at least one .srt file"


# @pytest.mark.e2e
def test_options_keep_audio(temp_output_dir: Path):
    """Test using --keep-audio option."""
    api_key = os.getenv("LEMONFOX_API_KEY")
    if not api_key:
        pytest.skip("Skipping E2E test: LEMONFOX_API_KEY environment variable not found.")

    args = [TEST_URL_YOUTUBE_SHORT, "--keep-audio"]
    result = run_transcriptor_cli(args, temp_output_dir)

    assert result.returncode == 0

    # Check that the audio subdirectory *and* at least one audio file exist
    audio_subdir = temp_output_dir / "_audio_files"
    assert audio_subdir.exists(), "Intermediate audio directory '_audio_files' should exist"
    audio_files = list(audio_subdir.glob('*'))
    # Check for common audio extensions used by the app/yt-dlp
    expected_audio_files = [f for f in audio_files if f.suffix in ('.mp3', '.opus', '.wav', '.m4a', '.webm')]
    assert len(expected_audio_files) >= 1, "Expected at least one audio file in the audio subdir"


# @pytest.mark.e2e
def test_multiple_urls_partial_failure(temp_output_dir: Path):
    """Test processing one valid and one invalid URL."""
    api_key = os.getenv("LEMONFOX_API_KEY")
    if not api_key:
        pytest.skip("Skipping E2E test: LEMONFOX_API_KEY environment variable not found.")

    args = [TEST_URL_YOUTUBE_SHORT, INVALID_TEST_URL]
    result = run_transcriptor_cli(args, temp_output_dir)

    # Expect non-zero exit code because one URL failed
    assert result.returncode != 0, "Expected non-zero exit code for partial failure"

    # Check that output files for the *valid* URL were still created
    output_files = list(temp_output_dir.glob('*'))
    # Use a pattern that likely matches the valid URL's output
    # Default template: "%(title)s [%(id)s]" -> ID is qx09DLXxVug
    valid_url_outputs = [f for f in output_files if "qx09DLXxVug" in f.name]
    assert len(valid_url_outputs) >= 2, "Expected output files (.txt, .srt) for the valid URL"

    # Check summary log output indicates failure (stdout for summary, stderr for warnings)
    assert "Batch Summary" in result.stdout
    assert "Total URLs attempted: 2" in result.stdout
    assert "Successfully processed: 1" in result.stdout # Only one succeeded
    # Warnings about failed URLs should now go to stderr
    assert "Failed URLs (1):" in result.stderr
    assert f"- {INVALID_TEST_URL}" in result.stderr


# @pytest.mark.e2e
def test_api_key_loaded_from_dotenv(temp_output_dir: Path):
    """
    Verify the script runs successfully when the API key is loaded from .env,
    and does NOT print the 'not found' error.
    This test assumes the key *is* present in the .env file.
    """
    api_key = os.getenv("LEMONFOX_API_KEY")
    if not api_key:
        pytest.skip("Skipping test: LEMONFOX_API_KEY not found in environment/.env, cannot verify loading.")

    # No need to manipulate os.environ here, just run the script normally
    args = [TEST_URL_YOUTUBE_SHORT]
    result = run_transcriptor_cli(args, temp_output_dir)

    # Expect successful execution because the key is loaded from .env
    assert result.returncode == 0, "Expected successful execution when key is loaded from .env"

    # Verify the "API key not found" error message is NOT printed to stderr
    # (The initial check in main.py logs errors to stderr now)
    assert "LEMONFOX_API_KEY not found" not in result.stderr
    # Also check stdout just in case, though it shouldn't be there
    assert "LEMONFOX_API_KEY not found" not in result.stdout


# @pytest.mark.e2e
def test_invalid_url_format(temp_output_dir: Path):
    """Test running with a syntactically invalid URL (not a real video)."""
    api_key = os.getenv("LEMONFOX_API_KEY")
    if not api_key:
        pytest.skip("Skipping E2E test: LEMONFOX_API_KEY environment variable not found.")

    # Using the INVALID_TEST_URL defined earlier
    args = [INVALID_TEST_URL]
    result = run_transcriptor_cli(args, temp_output_dir)

    # Expect non-zero exit code because download should fail
    assert result.returncode != 0, "Expected non-zero exit code for invalid URL"

    # Check logs for download error indication
    # Check logs for download error indication (now expected on stderr)
    assert "yt-dlp download error" in result.stderr or \
           "Audio download/extraction failed" in result.stderr # Pipeline errors also go to stderr

    # Check summary log output indicates failure (summary on stdout, warning on stderr)
    assert "Batch Summary" in result.stdout
    assert "Total URLs attempted: 1" in result.stdout
    assert "Successfully processed: 0" in result.stdout
    assert "Failed URLs (1):" in result.stderr
    assert f"- {INVALID_TEST_URL}" in result.stderr
