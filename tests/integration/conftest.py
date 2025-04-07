import pytest
import argparse

# --- Shared Test Data ---

MOCK_URL_1 = "http://example.com/video1"
MOCK_URL_2 = "http://example.com/video2"
MOCK_API_KEY = "test-api-key"

# Sample transcription result to be returned by the mocked transcriber
MOCK_TRANSCRIPT_RESULT = {
    "text": "This is the full transcript text.",
    "segments": [
        {"start": 0.5, "end": 2.8, "text": "This is the full transcript text.", "speaker": "SPEAKER_00"}
    ]
}

# Sample info dict returned by mocked yt-dlp for filename extraction
MOCK_INFO_DICT = {'id': 'video1_id', 'title': 'Video Title 1', 'ext': 'mp4'}

# --- Shared Helper Function ---

# Make it a fixture so it's easily available to tests
@pytest.fixture
def create_mock_args_fixture():
    """Fixture factory to create mock argparse.Namespace objects."""
    def _create_mock_args(**kwargs):
        """Creates a mock argparse.Namespace object with default values."""
        defaults = {
            "urls": [MOCK_URL_1],
            "output_dir": "output", # Will be replaced by tmp_path in tests
            "model": "whisper-1",
            "formats": ["txt", "srt"],
            "audio_format": "mp3",
            "output_filename_template": "%(title)s [%(id)s]",
            "language": None,
            "prompt": None,
            "temperature": 0.0,
            "speaker_labels": False,
            "keep_audio": False,
            "verbose": False,
        }
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)
    return _create_mock_args
