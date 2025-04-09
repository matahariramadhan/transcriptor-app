import pytest
import os
from unittest.mock import patch, MagicMock

# Import the function we want to test
from core.pipeline import run_pipeline

# Import constants from conftest
from .conftest import MOCK_URL_1, MOCK_URL_2, MOCK_API_KEY, MOCK_TRANSCRIPT_RESULT, MOCK_INFO_DICT

# --- Test Cases ---

@patch('core.pipeline.download_audio_python_api')
@patch('core.pipeline.transcribe_audio_lemonfox')
@patch('core.pipeline.yt_dlp.YoutubeDL')
@patch('core.pipeline.os.remove')
@patch('core.pipeline.os.rmdir')
@patch('core.pipeline.generate_txt', return_value=True) # Mock formatters too
@patch('core.pipeline.generate_srt', return_value=True)
def test_integration_multiple_urls_one_download_fails(
    mock_generate_srt, mock_generate_txt, # Add formatter mocks
    mock_rmdir, mock_remove, mock_youtube_dl, mock_transcriber, mock_downloader,
    tmp_path, create_mock_config_fixture # Use updated fixture
):
    """
    Integration test for processing multiple URLs where the second URL fails download.
    Verifies that the first URL is processed successfully and the second is marked as failed.
    """
    # --- Setup Mocks ---
    # Mock successful download for URL 1
    mock_audio_filename_1 = "video1_id.mp3"
    mock_audio_path_1 = tmp_path / "_audio_files" / mock_audio_filename_1
    mock_audio_path_1.parent.mkdir(exist_ok=True) # Ensure audio subdir exists
    mock_audio_path_1.touch()

    # Mock failed download for URL 2 (downloader returns None)
    mock_downloader.side_effect = [str(mock_audio_path_1), None] # Return path for first, None for second

    # Mock successful transcription for URL 1
    mock_transcriber.return_value = MOCK_TRANSCRIPT_RESULT

    # Mock filename extraction (only needed for URL 1)
    mock_ydl_extractor_instance = MagicMock()
    mock_youtube_dl.return_value = mock_ydl_extractor_instance
    mock_ydl_extractor_instance.extract_info.return_value = MOCK_INFO_DICT
    expected_base_filename_path = tmp_path / f"{MOCK_INFO_DICT['title']} [{MOCK_INFO_DICT['id']}]"
    mock_ydl_extractor_instance.prepare_filename.return_value = str(expected_base_filename_path)

    # --- Prepare Config ---
    config = create_mock_config_fixture() # Use updated fixture
    output_dir = str(tmp_path)
    audio_output_dir = str(mock_audio_path_1.parent)
    urls_to_process = [MOCK_URL_1, MOCK_URL_2]

    # --- Run Pipeline ---
    results = run_pipeline(
        urls_to_process=urls_to_process,
        api_key=MOCK_API_KEY,
        config=config, # Pass config dict
        audio_output_dir=audio_output_dir,
        output_dir=output_dir # Pass output_dir explicitly
    )

    # --- Assertions ---
    # Check pipeline results
    assert results['processed_count'] == 1 # Only URL 1 succeeded
    assert results['failed_urls'] == [MOCK_URL_2] # URL 2 failed

    # Check mock calls (downloader called twice, transcriber once, etc.)
    assert mock_downloader.call_count == 2
    mock_downloader.assert_any_call(url=MOCK_URL_1, output_dir=audio_output_dir, audio_format=config['audio_format'], output_template="%(id)s")
    mock_downloader.assert_any_call(url=MOCK_URL_2, output_dir=audio_output_dir, audio_format=config['audio_format'], output_template="%(id)s")

    mock_transcriber.assert_called_once() # Only called for URL 1
    # Check call, including default temperature
    mock_transcriber.assert_called_with(
            audio_path=str(mock_audio_path_1),
            model_name=config['model'],
            api_key=MOCK_API_KEY,
            temperature=config['temperature'], # Should be 0.0
            speaker_labels=False, # Add expected default
            response_format='verbose_json'
        )

    mock_ydl_extractor_instance.extract_info.assert_called_once_with(MOCK_URL_1, download=False) # Only for URL 1

    # Check formatters called only for URL 1
    expected_base_output_path = os.path.join(output_dir, f"{MOCK_INFO_DICT['title']} [{MOCK_INFO_DICT['id']}]")
    mock_generate_txt.assert_called_once_with(MOCK_TRANSCRIPT_RESULT, f"{expected_base_output_path}.txt")
    mock_generate_srt.assert_called_once_with(MOCK_TRANSCRIPT_RESULT, f"{expected_base_output_path}.srt")

    # Check cleanup (only for URL 1's audio)
    mock_remove.assert_called_once_with(str(mock_audio_path_1))
    # rmdir might be called multiple times if cleanup logic runs per URL,
    # or just once if it only tries at the very end. Let's check it was called for the correct dir.
    # Depending on exact cleanup logic, assert_called_once_with or assert_any_call might be better.
    # Given the current loop structure, it likely tries after each URL's finally block.
    # Let's assume it might be called twice but we only care it was called for the right dir.
    mock_rmdir.assert_any_call(audio_output_dir)


@patch('core.pipeline.download_audio_python_api')
@patch('core.pipeline.transcribe_audio_lemonfox')
@patch('core.pipeline.yt_dlp.YoutubeDL') # Mock filename extractor
@patch('core.pipeline.os.remove')
@patch('core.pipeline.os.rmdir')
@patch('core.pipeline.generate_txt') # Mock formatters too
@patch('core.pipeline.generate_srt')
def test_integration_transcription_fails(
    mock_generate_srt, mock_generate_txt, # Add formatter mocks
    mock_rmdir, mock_remove, mock_youtube_dl, mock_transcriber, mock_downloader,
    tmp_path, create_mock_config_fixture # Use updated fixture
):
    """
    Integration test where transcription step fails.
    """
    # --- Setup Mocks ---
    mock_audio_filename = "video1_id.mp3"
    mock_audio_path = tmp_path / "_audio_files" / mock_audio_filename
    mock_audio_path.parent.mkdir()
    mock_audio_path.touch()

    mock_downloader.return_value = str(mock_audio_path)
    # Simulate transcription failure
    mock_transcriber.return_value = None

    # Mock filename extractor - it shouldn't be called if transcription fails before formatting
    mock_ydl_extractor_instance = MagicMock()
    mock_youtube_dl.return_value = mock_ydl_extractor_instance

    # --- Prepare Config ---
    config = create_mock_config_fixture() # Use updated fixture
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
    # Check pipeline results
    assert results['processed_count'] == 0 # Failed
    assert results['failed_urls'] == [MOCK_URL_1]

    # Check mocks
    mock_downloader.assert_called_once()
    mock_transcriber.assert_called_once() # Transcriber was called but returned None
    # YoutubeDL IS called once at the start of the pipeline to initialize the extractor
    mock_youtube_dl.assert_called_once()
    # But its methods for filename generation should NOT be called
    mock_ydl_extractor_instance.extract_info.assert_not_called()
    mock_ydl_extractor_instance.prepare_filename.assert_not_called()

    # Check formatters not called
    mock_generate_txt.assert_not_called()
    mock_generate_srt.assert_not_called()

    # Check cleanup still happens
    mock_remove.assert_called_once_with(str(mock_audio_path))
    mock_rmdir.assert_called_once_with(audio_output_dir)


@patch('core.pipeline.download_audio_python_api')
@patch('core.pipeline.transcribe_audio_lemonfox')
@patch('core.pipeline.yt_dlp.YoutubeDL')
@patch('core.pipeline.generate_txt') # Mock the formatter functions
@patch('core.pipeline.generate_srt') # Mock the formatter functions
@patch('core.pipeline.os.remove')
@patch('core.pipeline.os.rmdir')
def test_integration_formatting_fails(
    mock_rmdir, mock_remove, mock_generate_srt, mock_generate_txt,
    mock_youtube_dl, mock_transcriber, mock_downloader,
    tmp_path, create_mock_config_fixture # Use updated fixture
):
    """
    Integration test where SRT formatting fails, but TXT succeeds.
    """
    # --- Setup Mocks ---
    mock_audio_filename = "video1_id.mp3"
    mock_audio_path = tmp_path / "_audio_files" / mock_audio_filename
    mock_audio_path.parent.mkdir()
    mock_audio_path.touch()

    mock_downloader.return_value = str(mock_audio_path)
    mock_transcriber.return_value = MOCK_TRANSCRIPT_RESULT

    # Mock filename extractor
    mock_ydl_extractor_instance = MagicMock()
    mock_youtube_dl.return_value = mock_ydl_extractor_instance
    mock_ydl_extractor_instance.extract_info.return_value = MOCK_INFO_DICT
    expected_base_filename_path = tmp_path / f"{MOCK_INFO_DICT['title']} [{MOCK_INFO_DICT['id']}]"
    mock_ydl_extractor_instance.prepare_filename.return_value = str(expected_base_filename_path)

    # Simulate formatting results (TXT succeeds, SRT fails)
    mock_generate_txt.return_value = True
    mock_generate_srt.return_value = False

    # --- Prepare Config ---
    config = create_mock_config_fixture(formats=['txt', 'srt']) # Use updated fixture
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
    # Check pipeline results
    # The current logic counts a URL as processed if at least one format succeeds.
    # It only adds to failed_urls if download/transcription fails OR *zero* formats succeed.
    assert results['processed_count'] == 1 # TXT succeeded, so it's counted.
    assert results['failed_urls'] == [] # Not added to failed list because one format worked.

    # Check mocks
    mock_downloader.assert_called_once()
    mock_transcriber.assert_called_once()
    mock_youtube_dl.assert_called_once() # Filename extraction should happen

    # Check formatter calls
    expected_base_output_path = os.path.join(output_dir, f"{MOCK_INFO_DICT['title']} [{MOCK_INFO_DICT['id']}]")
    mock_generate_txt.assert_called_once_with(MOCK_TRANSCRIPT_RESULT, f"{expected_base_output_path}.txt")
    mock_generate_srt.assert_called_once_with(MOCK_TRANSCRIPT_RESULT, f"{expected_base_output_path}.srt")

    # Check cleanup still happens
    mock_remove.assert_called_once_with(str(mock_audio_path))
    mock_rmdir.assert_called_once_with(audio_output_dir)
