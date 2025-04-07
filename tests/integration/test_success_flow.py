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
@patch('src.pipeline.yt_dlp.YoutubeDL') # Mock the yt-dlp instance used for filename extraction
@patch('src.pipeline.os.remove') # Mock os.remove to check cleanup
@patch('src.pipeline.os.rmdir') # Mock os.rmdir to check cleanup
def test_integration_single_url_success(
    mock_rmdir, mock_remove, mock_youtube_dl, mock_transcriber, mock_downloader,
    tmp_path, create_mock_args_fixture # Use fixture
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

    # --- Prepare Args ---
    args = create_mock_args_fixture(output_dir=str(tmp_path)) # Use fixture

    # --- Run Pipeline ---
    results = run_pipeline(
        urls_to_process=[MOCK_URL_1],
        api_key=MOCK_API_KEY,
        args=args,
        audio_output_dir=str(mock_audio_path.parent) # Pass the audio subdir path
    )

    # --- Assertions ---
    # Check pipeline results
    assert results['processed_count'] == 1
    assert results['failed_urls'] == []

    # Check mock calls
    mock_downloader.assert_called_once_with(
        url=MOCK_URL_1,
        output_dir=str(mock_audio_path.parent),
        audio_format=args.audio_format,
        output_template="%(id)s" # Default template used for audio
    )
    # Check call, filtering out None/False args as done in pipeline.py
    mock_transcriber.assert_called_once_with(
        audio_path=str(mock_audio_path),
        model_name=args.model,
        api_key=MOCK_API_KEY,
        temperature=args.temperature, # 0.0 is passed
        response_format='verbose_json'
        # language=None, prompt=None, speaker_labels=False are filtered out
    )
    mock_youtube_dl.assert_called_once() # Check filename extractor was initialized
    mock_ydl_extractor_instance.extract_info.assert_called_once_with(MOCK_URL_1, download=False)
    mock_ydl_extractor_instance.prepare_filename.assert_called_once_with(MOCK_INFO_DICT, outtmpl=args.output_filename_template)

    # Check output files
    expected_base_output = tmp_path / f"{MOCK_INFO_DICT['title']} [{MOCK_INFO_DICT['id']}]"
    txt_output_path = expected_base_output.with_suffix('.txt')
    srt_output_path = expected_base_output.with_suffix('.srt')

    assert txt_output_path.exists()
    assert srt_output_path.exists()

    # Check file content (basic check)
    expected_txt_content = MOCK_TRANSCRIPT_RESULT['text'] + "\n"
    expected_srt_content = "1\n00:00:00,500 --> 00:00:02,800\n(SPEAKER_00) This is the full transcript text.\n"
    assert txt_output_path.read_text(encoding='utf-8') == expected_txt_content
    assert srt_output_path.read_text(encoding='utf-8') == expected_srt_content

    # Check cleanup (default is to remove audio)
    mock_remove.assert_called_once_with(str(mock_audio_path))
    # Check if rmdir was attempted on the audio subdir
    mock_rmdir.assert_called_once_with(str(mock_audio_path.parent))
