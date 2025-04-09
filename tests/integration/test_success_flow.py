import pytest
import os
from unittest.mock import patch, MagicMock

# Import the function we want to test
from core.pipeline import run_pipeline

# Import constants from conftest
from .conftest import MOCK_URL_1, MOCK_API_KEY, MOCK_TRANSCRIPT_RESULT, MOCK_INFO_DICT

# --- Test Cases ---

@patch('core.pipeline.download_audio_python_api')
@patch('core.pipeline.transcribe_audio_lemonfox')
@patch('core.pipeline.yt_dlp.YoutubeDL') # Mock the yt-dlp instance used for filename extraction
@patch('core.pipeline.os.remove') # Mock os.remove to check cleanup
@patch('core.pipeline.os.rmdir') # Mock os.rmdir to check cleanup
@patch('core.pipeline.generate_txt', return_value=True) # Mock formatters too
@patch('core.pipeline.generate_srt', return_value=True)
def test_integration_single_url_success(
    mock_generate_srt, mock_generate_txt, # Add formatter mocks
    mock_rmdir, mock_remove, mock_youtube_dl, mock_transcriber, mock_downloader,
    tmp_path, create_mock_config_fixture # Use updated fixture
):
    """
    Integration test for successfully processing a single URL.
    Mocks downloader, transcriber, and filename extractor.
    Verifies pipeline return value and output file creation/content.
    """
    # --- Setup Mocks ---
    mock_audio_filename = "video1_id.mp3"
    mock_audio_path = tmp_path / "_audio_files" / mock_audio_filename
    mock_audio_path.parent.mkdir() # Create the audio subdir
    mock_audio_path.touch() # Create dummy audio file for os.path.exists checks

    mock_downloader.return_value = str(mock_audio_path)
    mock_transcriber.return_value = MOCK_TRANSCRIPT_RESULT

    # Configure the mock yt-dlp filename extractor
    mock_ydl_extractor_instance = MagicMock()
    mock_youtube_dl.return_value = mock_ydl_extractor_instance
    mock_ydl_extractor_instance.extract_info.return_value = MOCK_INFO_DICT
    # Simulate prepare_filename removing extension if template doesn't have one
    expected_base_filename_path = tmp_path / f"{MOCK_INFO_DICT['title']} [{MOCK_INFO_DICT['id']}]"
    mock_ydl_extractor_instance.prepare_filename.return_value = str(expected_base_filename_path)

    # --- Prepare Config ---
    # Use the updated fixture to create a config dictionary
    config = create_mock_config_fixture()
    output_dir = str(tmp_path) # Define output_dir for clarity
    audio_output_dir = str(mock_audio_path.parent) # Define audio_output_dir

    # --- Run Pipeline ---
    results = run_pipeline(
        urls_to_process=[MOCK_URL_1],
        api_key=MOCK_API_KEY,
        config=config, # Pass the config dictionary
        audio_output_dir=audio_output_dir,
        output_dir=output_dir # Pass output_dir explicitly
    )

    # --- Assertions ---
    # Check pipeline results
    assert results['processed_count'] == 1
    assert results['failed_urls'] == []

    # Check mock calls
    mock_downloader.assert_called_once_with(
        url=MOCK_URL_1,
        output_dir=audio_output_dir,
        audio_format=config['audio_format'],
        output_template="%(id)s" # Default template used for audio
    )
    # Check call, filtering out None/False args as done in pipeline.py
    mock_transcriber.assert_called_once_with(
        audio_path=str(mock_audio_path),
        model_name=config['model'],
            api_key=MOCK_API_KEY,
            temperature=config['temperature'], # 0.0 is passed
            speaker_labels=False, # Add expected default
            response_format='verbose_json'
            # language=None, prompt=None, speaker_labels=False are filtered out
        )
    mock_youtube_dl.assert_called_once() # Check filename extractor was initialized
    mock_ydl_extractor_instance.extract_info.assert_called_once_with(MOCK_URL_1, download=False)
    mock_ydl_extractor_instance.prepare_filename.assert_called_once_with(MOCK_INFO_DICT, outtmpl=config['output_filename_template'])

    # Check that formatters were called
    expected_base_output_path = os.path.join(output_dir, f"{MOCK_INFO_DICT['title']} [{MOCK_INFO_DICT['id']}]")
    mock_generate_txt.assert_called_once_with(MOCK_TRANSCRIPT_RESULT, f"{expected_base_output_path}.txt")
    mock_generate_srt.assert_called_once_with(MOCK_TRANSCRIPT_RESULT, f"{expected_base_output_path}.srt")

    # Check cleanup (default is keep_audio=False in fixture)
    mock_remove.assert_called_once_with(str(mock_audio_path))
    # Check if rmdir was attempted on the audio subdir
    mock_rmdir.assert_called_once_with(str(mock_audio_path.parent))
