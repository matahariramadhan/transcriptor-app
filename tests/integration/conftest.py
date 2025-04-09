import pytest

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
def create_mock_config_fixture():
    """Fixture factory to create mock configuration dictionaries."""
    def _create_mock_config(**kwargs):
        """Creates a mock config dictionary with default values."""
        defaults = {
            # Note: 'urls' are passed directly to run_pipeline, not part of config dict
            # Note: 'output_dir' is passed directly to run_pipeline, not part of config dict
            "model": "whisper-1",
            "formats": ["txt", "srt"],
            "audio_format": "mp3",
            "output_filename_template": "%(title)s [%(id)s]",
            "language": None,
            "prompt": None,
            "temperature": 0.0,
            "speaker_labels": False,
            "keep_audio": False,
            # Note: 'verbose' is handled by logger setup, not needed in core config
        }
        defaults.update(kwargs)
        return defaults
    return _create_mock_config
