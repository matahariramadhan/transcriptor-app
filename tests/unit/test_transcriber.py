import pytest
import os
from unittest.mock import patch, MagicMock, mock_open, ANY
from core.transcriber import transcribe_audio_lemonfox
# Import specific exceptions from the openai library to test handling
from openai import APIError, APIConnectionError, RateLimitError, AuthenticationError

# Define constants for tests
TEST_AUDIO_PATH = "fake/audio/path.mp3"
TEST_MODEL = "whisper-1"
TEST_API_KEY = "sk-testkey123"
MOCK_TRANSCRIPTION_RESULT = {"text": "This is a mock transcription."}

# --- Test Cases ---

# Use patch for the OpenAI client within the transcriber module
@patch('core.transcriber.OpenAI')
@patch('core.transcriber.os.path.exists', return_value=True) # Assume file exists for most tests
def test_transcribe_success(mock_exists, mock_openai_client, tmp_path):
    """Tests successful transcription path."""
    # Configure the mock client and its methods
    mock_client_instance = MagicMock()
    mock_openai_client.return_value = mock_client_instance
    mock_transcription_object = MagicMock()
    # Simulate Pydantic-like model_dump or direct dict return
    mock_transcription_object.model_dump.return_value = MOCK_TRANSCRIPTION_RESULT 
    mock_client_instance.audio.transcriptions.create.return_value = mock_transcription_object

    # Use a real temporary file path for the test
    audio_file_path = tmp_path / "test.mp3"
    audio_file_path.touch() # Create the dummy file

    result = transcribe_audio_lemonfox(
        audio_path=str(audio_file_path),
        model_name=TEST_MODEL,
        api_key=TEST_API_KEY,
        language="en",
        prompt="Test prompt",
        speaker_labels=True
    )

    # Assertions
    mock_exists.assert_called_once_with(str(audio_file_path))
    mock_openai_client.assert_called_once_with(
        api_key=TEST_API_KEY,
        base_url="https://api.lemonfox.ai/v1"
    )
    # Check that create was called with expected args (file handle is tricky, use ANY)
    mock_client_instance.audio.transcriptions.create.assert_called_once()
    call_args, call_kwargs = mock_client_instance.audio.transcriptions.create.call_args
    assert call_kwargs.get("model") == TEST_MODEL
    assert call_kwargs.get("language") == "en"
    assert call_kwargs.get("prompt") == "Test prompt"
    assert call_kwargs.get("speaker_labels") is True
    assert call_kwargs.get("response_format") == 'json' # Expect default 'json' as it wasn't overridden
    # Check file handle was passed (cannot compare directly)
    assert 'file' in call_kwargs 
    
    assert result == MOCK_TRANSCRIPTION_RESULT


@patch('core.transcriber.OpenAI')
@patch('core.transcriber.os.path.exists', return_value=True)
def test_transcribe_success_string_response(mock_exists, mock_openai_client, tmp_path):
    """Tests successful transcription when API returns a plain string."""
    mock_client_instance = MagicMock()
    mock_openai_client.return_value = mock_client_instance
    mock_api_response_string = "This is a plain string response."
    mock_client_instance.audio.transcriptions.create.return_value = mock_api_response_string

    audio_file_path = tmp_path / "test.mp3"
    audio_file_path.touch()

    result = transcribe_audio_lemonfox(
        audio_path=str(audio_file_path),
        model_name=TEST_MODEL,
        api_key=TEST_API_KEY,
        response_format='text' # Explicitly set format that might return string
    )

    # Assertions
    mock_exists.assert_called_once_with(str(audio_file_path))
    mock_openai_client.assert_called_once_with(
        api_key=TEST_API_KEY,
        base_url="https://api.lemonfox.ai/v1"
    )
    mock_client_instance.audio.transcriptions.create.assert_called_once()
    call_args, call_kwargs = mock_client_instance.audio.transcriptions.create.call_args
    assert call_kwargs.get("response_format") == 'text'
    
    # Check that the string result is wrapped in a dictionary
    assert result == {"text": mock_api_response_string}


@patch('core.transcriber.os.path.exists', return_value=False)
def test_transcribe_file_not_found(mock_exists):
    """Tests failure when the audio file does not exist."""
    result = transcribe_audio_lemonfox(
        audio_path=TEST_AUDIO_PATH,
        model_name=TEST_MODEL,
        api_key=TEST_API_KEY
    )
    mock_exists.assert_called_once_with(TEST_AUDIO_PATH)
    assert result is None

@patch('core.transcriber.OpenAI')
@patch('core.transcriber.os.path.exists', return_value=True)
def test_transcribe_no_api_key(mock_exists, mock_openai_client):
    """Tests failure when API key is missing."""
    result = transcribe_audio_lemonfox(
        audio_path=TEST_AUDIO_PATH,
        model_name=TEST_MODEL,
        api_key=None # Simulate missing key
    )
    mock_openai_client.assert_not_called() # Client initialization shouldn't happen
    assert result is None

@patch('core.transcriber.OpenAI', side_effect=Exception("Client init failed"))
@patch('core.transcriber.os.path.exists', return_value=True)
def test_transcribe_client_init_fails(mock_exists, mock_openai_client):
    """Tests failure during OpenAI client initialization."""
    result = transcribe_audio_lemonfox(
        audio_path=TEST_AUDIO_PATH,
        model_name=TEST_MODEL,
        api_key=TEST_API_KEY
    )
    mock_openai_client.assert_called_once()
    assert result is None

# --- Test API Error Handling ---

@pytest.mark.parametrize("error_type", [
    AuthenticationError(message="Auth error", response=MagicMock(), body=None),
    RateLimitError(message="Rate limit", response=MagicMock(), body=None),
    # Add a mock request object for APIConnectionError
    APIConnectionError(message="Connection error", request=MagicMock()), 
    APIError(message="Generic API error", request=MagicMock(), body=None),
    Exception("Unexpected error during API call") # Generic catch-all
])
@patch('core.transcriber.OpenAI')
@patch('core.transcriber.os.path.exists', return_value=True)
def test_transcribe_api_errors(mock_exists, mock_openai_client, error_type, tmp_path):
    """Tests handling of various API errors during transcription create call."""
    mock_client_instance = MagicMock()
    mock_openai_client.return_value = mock_client_instance
    # Simulate the create call raising the specified error
    mock_client_instance.audio.transcriptions.create.side_effect = error_type

    audio_file_path = tmp_path / "test.mp3"
    audio_file_path.touch()

    result = transcribe_audio_lemonfox(
        audio_path=str(audio_file_path),
        model_name=TEST_MODEL,
        api_key=TEST_API_KEY
    )

    mock_client_instance.audio.transcriptions.create.assert_called_once()
    assert result is None
