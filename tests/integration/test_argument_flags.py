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
@patch('core.pipeline.yt_dlp.YoutubeDL')
@patch('core.pipeline.os.remove') # Mock os.remove to check cleanup
@patch('core.pipeline.os.rmdir') # Mock os.rmdir to check cleanup
@patch('core.pipeline.generate_txt', return_value=True) # Mock formatters too
@patch('core.pipeline.generate_srt', return_value=True)
def test_integration_keep_audio_flag(
    mock_generate_srt, mock_generate_txt, # Add formatter mocks
    mock_rmdir, mock_remove, mock_youtube_dl, mock_transcriber, mock_downloader,
    tmp_path, create_mock_config_fixture # Use updated fixture
):
    """
    Integration test verifying the keep_audio config flag prevents audio file deletion.
    """
    # --- Setup Mocks (similar to single URL success) ---
    mock_audio_filename = "video1_id.mp3"
    mock_audio_path = tmp_path / "_audio_files" / mock_audio_filename
    mock_audio_path.parent.mkdir()
    mock_audio_path.touch()

    mock_downloader.return_value = str(mock_audio_path)
    mock_transcriber.return_value = MOCK_TRANSCRIPT_RESULT

    mock_ydl_extractor_instance = MagicMock()
    mock_youtube_dl.return_value = mock_ydl_extractor_instance
    mock_ydl_extractor_instance.extract_info.return_value = MOCK_INFO_DICT
    expected_base_filename_path = tmp_path / f"{MOCK_INFO_DICT['title']} [{MOCK_INFO_DICT['id']}]"
    mock_ydl_extractor_instance.prepare_filename.return_value = str(expected_base_filename_path)

    # --- Prepare Config (set keep_audio=True) ---
    config = create_mock_config_fixture(keep_audio=True) # Use updated fixture
    output_dir = str(tmp_path)
    audio_output_dir = str(mock_audio_path.parent)

    # --- Run Pipeline ---
    results = run_pipeline(
        urls_to_process=[MOCK_URL_1],
        api_key=MOCK_API_KEY,
        config=config, # Pass config dict
        audio_output_dir=audio_output_dir,
        output_dir=output_dir # Pass output_dir explicitly
    )

    # --- Assertions ---
    # Check pipeline results (should still succeed)
    assert results['processed_count'] == 1
    assert results['failed_urls'] == []

    # Check formatters were called (to ensure pipeline ran fully)
    expected_base_output_path = os.path.join(output_dir, f"{MOCK_INFO_DICT['title']} [{MOCK_INFO_DICT['id']}]")
    mock_generate_txt.assert_called_once_with(MOCK_TRANSCRIPT_RESULT, f"{expected_base_output_path}.txt")
    mock_generate_srt.assert_called_once_with(MOCK_TRANSCRIPT_RESULT, f"{expected_base_output_path}.srt")

    # Check cleanup (audio file should NOT be removed)
    mock_remove.assert_not_called()
    mock_rmdir.assert_not_called() # Directory shouldn't be removed if file is kept


@patch('core.pipeline.download_audio_python_api')
@patch('core.pipeline.transcribe_audio_lemonfox')
@patch('core.pipeline.yt_dlp.YoutubeDL')
@patch('core.pipeline.os.remove')
@patch('core.pipeline.os.rmdir')
@patch('core.pipeline.generate_txt', return_value=True) # Mock formatters too
@patch('core.pipeline.generate_srt', return_value=True)
def test_integration_speaker_labels_flag(
    mock_generate_srt, mock_generate_txt, # Add formatter mocks
    mock_rmdir, mock_remove, mock_youtube_dl, mock_transcriber, mock_downloader,
    tmp_path, create_mock_config_fixture # Use updated fixture
):
    """
    Integration test verifying the speaker_labels config flag is passed correctly.
    """
    # --- Setup Mocks (similar to single URL success) ---
    mock_audio_filename = "video1_id.mp3"
    mock_audio_path = tmp_path / "_audio_files" / mock_audio_filename
    mock_audio_path.parent.mkdir()
    mock_audio_path.touch()

    mock_downloader.return_value = str(mock_audio_path)
    mock_transcriber.return_value = MOCK_TRANSCRIPT_RESULT # Content doesn't matter here

    # Mock filename extractor
    mock_ydl_extractor_instance = MagicMock()
    mock_youtube_dl.return_value = mock_ydl_extractor_instance
    mock_ydl_extractor_instance.extract_info.return_value = MOCK_INFO_DICT
    expected_base_filename_path = tmp_path / f"{MOCK_INFO_DICT['title']} [{MOCK_INFO_DICT['id']}]"
    mock_ydl_extractor_instance.prepare_filename.return_value = str(expected_base_filename_path)

    # --- Prepare Config (set speaker_labels=True) ---
    config = create_mock_config_fixture(speaker_labels=True) # Use updated fixture
    output_dir = str(tmp_path)
    audio_output_dir = str(mock_audio_path.parent)

    # --- Run Pipeline ---
    results = run_pipeline(
        urls_to_process=[MOCK_URL_1],
        api_key=MOCK_API_KEY,
        config=config, # Pass config dict
        audio_output_dir=audio_output_dir,
        output_dir=output_dir # Pass output_dir explicitly
    )

    # --- Assertions ---
    # Check pipeline results (should succeed)
    assert results['processed_count'] == 1
    assert results['failed_urls'] == []

    # Check transcriber call includes speaker_labels=True
    mock_transcriber.assert_called_once_with(
        audio_path=str(mock_audio_path),
        model_name=config['model'],
        api_key=MOCK_API_KEY,
        temperature=config['temperature'],
        speaker_labels=True, # Verify this was passed
        response_format='verbose_json'
    )

    # Check formatters were called (to ensure pipeline ran fully)
    expected_base_output_path = os.path.join(output_dir, f"{MOCK_INFO_DICT['title']} [{MOCK_INFO_DICT['id']}]")
    mock_generate_txt.assert_called_once_with(MOCK_TRANSCRIPT_RESULT, f"{expected_base_output_path}.txt")
    mock_generate_srt.assert_called_once_with(MOCK_TRANSCRIPT_RESULT, f"{expected_base_output_path}.srt")

    # Check cleanup
    mock_remove.assert_called_once_with(str(mock_audio_path))
    mock_rmdir.assert_called_once_with(audio_output_dir)
