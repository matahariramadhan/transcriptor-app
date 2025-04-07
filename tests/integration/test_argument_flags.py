import pytest
import os
from unittest.mock import patch, MagicMock

# Import the function we want to test
from src.pipeline import run_pipeline

# Import constants from conftest
from .conftest import MOCK_URL_1, MOCK_API_KEY, MOCK_TRANSCRIPT_RESULT, MOCK_INFO_DICT

# --- Test Cases ---

@patch('src.pipeline.download_audio_python_api')
@patch('src.pipeline.transcribe_audio_lemonfox')
@patch('src.pipeline.yt_dlp.YoutubeDL')
@patch('src.pipeline.os.remove') # Mock os.remove to check cleanup
@patch('src.pipeline.os.rmdir') # Mock os.rmdir to check cleanup
def test_integration_keep_audio_flag(
    mock_rmdir, mock_remove, mock_youtube_dl, mock_transcriber, mock_downloader,
    tmp_path, create_mock_args_fixture # Use fixture
):
    """
    Integration test verifying the --keep-audio flag prevents audio file deletion.
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

    # --- Prepare Args (set keep_audio=True) ---
    args = create_mock_args_fixture(output_dir=str(tmp_path), keep_audio=True) # Use fixture

    # --- Run Pipeline ---
    results = run_pipeline(
        urls_to_process=[MOCK_URL_1],
        api_key=MOCK_API_KEY,
        args=args,
        audio_output_dir=str(mock_audio_path.parent)
    )

    # --- Assertions ---
    # Check pipeline results (should still succeed)
    assert results['processed_count'] == 1
    assert results['failed_urls'] == []

    # Check output files exist
    expected_base_output = tmp_path / f"{MOCK_INFO_DICT['title']} [{MOCK_INFO_DICT['id']}]"
    txt_output_path = expected_base_output.with_suffix('.txt')
    srt_output_path = expected_base_output.with_suffix('.srt')
    assert txt_output_path.exists()
    assert srt_output_path.exists()

    # Check cleanup (audio file should NOT be removed)
    mock_remove.assert_not_called()
    mock_rmdir.assert_not_called() # Directory shouldn't be removed if file is kept


@patch('src.pipeline.download_audio_python_api')
@patch('src.pipeline.transcribe_audio_lemonfox')
@patch('src.pipeline.yt_dlp.YoutubeDL')
@patch('src.pipeline.os.remove')
@patch('src.pipeline.os.rmdir')
def test_integration_speaker_labels_flag(
    mock_rmdir, mock_remove, mock_youtube_dl, mock_transcriber, mock_downloader,
    tmp_path, create_mock_args_fixture # Use fixture
):
    """
    Integration test verifying the --speaker-labels flag is passed correctly.
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

    # --- Prepare Args (set speaker_labels=True) ---
    args = create_mock_args_fixture(output_dir=str(tmp_path), speaker_labels=True) # Use fixture

    # --- Run Pipeline ---
    results = run_pipeline(
        urls_to_process=[MOCK_URL_1],
        api_key=MOCK_API_KEY,
        args=args,
        audio_output_dir=str(mock_audio_path.parent)
    )

    # --- Assertions ---
    # Check pipeline results (should succeed)
    assert results['processed_count'] == 1
    assert results['failed_urls'] == []

    # Check transcriber call includes speaker_labels=True
    mock_transcriber.assert_called_once_with(
        audio_path=str(mock_audio_path),
        model_name=args.model,
        api_key=MOCK_API_KEY,
        temperature=args.temperature,
        speaker_labels=True, # Verify this was passed
        response_format='verbose_json'
    )

    # Check output files exist (basic check)
    expected_base_output = tmp_path / f"{MOCK_INFO_DICT['title']} [{MOCK_INFO_DICT['id']}]"
    txt_output_path = expected_base_output.with_suffix('.txt')
    srt_output_path = expected_base_output.with_suffix('.srt')
    assert txt_output_path.exists()
    assert srt_output_path.exists()

    # Check cleanup
    mock_remove.assert_called_once_with(str(mock_audio_path))
    mock_rmdir.assert_called_once_with(str(mock_audio_path.parent))
