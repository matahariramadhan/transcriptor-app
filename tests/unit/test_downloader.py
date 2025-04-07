import pytest
import os
import logging # Import logging for patching
from unittest.mock import patch, MagicMock, ANY # ANY is useful for matching complex args like hooks
from src.downloader import download_audio_python_api, YtdlpLogger # Import YtdlpLogger
import yt_dlp # Import the real module to check for its exceptions

# Define constants for tests
TEST_URL = "http://example.com/video"
TEST_OUTPUT_DIR = "test_audio_output"
TEST_AUDIO_FORMAT = "opus"
TEST_OUTPUT_TEMPLATE = "%(id)s_test"
EXPECTED_AUDIO_PATH_TEMPLATE = os.path.join(TEST_OUTPUT_DIR, TEST_OUTPUT_TEMPLATE)
EXPECTED_FINAL_FILENAME = os.path.join(TEST_OUTPUT_DIR, "video_id_test.opus") # Example final name
MOCK_INFO_DICT = {'id': 'video_id', 'ext': 'webm'} # Sample info dict for fallback test

# --- Test Cases ---

@patch('src.downloader.yt_dlp.YoutubeDL') # Patch the YoutubeDL class where it's used
def test_download_success_hook_provides_filename(mock_youtube_dl, tmp_path):
    """Tests successful download where the progress hook provides the final filename."""
    output_dir = tmp_path / TEST_OUTPUT_DIR
    output_dir.mkdir()
    expected_final_path = output_dir / "final_hook_name.opus"

    # Configure the mock instance returned by YoutubeDL()
    mock_ydl_instance = MagicMock()
    mock_youtube_dl.return_value.__enter__.return_value = mock_ydl_instance # Handle context manager

    # Simulate progress hook setting the filename and download returning success (0)
    def side_effect_download(urls):
        # Find the progress_hooks list in ydl_opts used to initialize YoutubeDL
        # This is a bit indirect but necessary as the hook is passed during init
        call_args, call_kwargs = mock_youtube_dl.call_args
        ydl_opts = call_args[0] # Assuming opts is the first positional arg
        hooks = ydl_opts.get('progress_hooks', [])
        # Simulate the hook being called with 'finished' status
        for hook in hooks:
            hook({'status': 'finished', 'filename': str(expected_final_path)})
        return 0 # Success code
    
    mock_ydl_instance.download.side_effect = side_effect_download

    # Mock os.path.exists to simulate the file existing after "download"
    with patch('os.path.exists', return_value=True) as mock_exists:
        result_path = download_audio_python_api(
            url=TEST_URL,
            output_dir=str(output_dir),
            audio_format=TEST_AUDIO_FORMAT,
            output_template=TEST_OUTPUT_TEMPLATE
        )

        # Assertions
        mock_youtube_dl.assert_called_once() # Check YoutubeDL was initialized
        # Check relevant ydl_opts were passed (use ANY for hooks/logger)
        mock_youtube_dl.assert_called_with({
            'format': 'bestaudio/best',
            'outtmpl': str(output_dir / TEST_OUTPUT_TEMPLATE),
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': TEST_AUDIO_FORMAT}],
            'logger': ANY,
            'progress_hooks': ANY,
            'noprogress': True,
            'quiet': True,
            'ignoreerrors': False,
            'paths': {'home': str(output_dir)}
        })
        mock_ydl_instance.download.assert_called_once_with([TEST_URL])
        mock_exists.assert_called_with(str(expected_final_path))
        assert result_path == str(expected_final_path)


@patch('src.downloader.yt_dlp.YoutubeDL')
def test_download_success_fallback_filename(mock_youtube_dl, tmp_path):
    """Tests successful download using fallback filename logic when hook doesn't provide it."""
    output_dir = tmp_path / TEST_OUTPUT_DIR
    output_dir.mkdir()
    expected_prepared_path_no_ext = output_dir / f"{MOCK_INFO_DICT['id']}_test"
    expected_final_path = output_dir / f"{MOCK_INFO_DICT['id']}_test.{TEST_AUDIO_FORMAT}"

    mock_ydl_instance = MagicMock()
    mock_youtube_dl.return_value.__enter__.return_value = mock_ydl_instance

    # Simulate download success (0) but hook doesn't set filename
    mock_ydl_instance.download.return_value = 0
    # Mock extract_info and prepare_filename for fallback
    mock_ydl_instance.extract_info.return_value = MOCK_INFO_DICT
    mock_ydl_instance.prepare_filename.return_value = str(expected_prepared_path_no_ext)

    # Mock os.path.exists to return True for the expected fallback path
    with patch('os.path.exists', return_value=True) as mock_exists:
        result_path = download_audio_python_api(
            url=TEST_URL,
            output_dir=str(output_dir),
            audio_format=TEST_AUDIO_FORMAT,
            output_template=TEST_OUTPUT_TEMPLATE
        )

        mock_ydl_instance.download.assert_called_once_with([TEST_URL])
        mock_ydl_instance.extract_info.assert_called_once_with(TEST_URL, download=False)
        mock_ydl_instance.prepare_filename.assert_called_once_with(MOCK_INFO_DICT, outtmpl=str(output_dir / TEST_OUTPUT_TEMPLATE))
        mock_exists.assert_called_with(str(expected_final_path))
        assert result_path == str(expected_final_path)


@patch('src.downloader.yt_dlp.YoutubeDL')
def test_download_failure_code(mock_youtube_dl, tmp_path):
    """Tests download failure when yt-dlp returns a non-zero exit code."""
    output_dir = tmp_path / TEST_OUTPUT_DIR
    output_dir.mkdir()

    mock_ydl_instance = MagicMock()
    mock_youtube_dl.return_value.__enter__.return_value = mock_ydl_instance
    # Simulate download failure (non-zero code)
    mock_ydl_instance.download.return_value = 1

    result_path = download_audio_python_api(
        url=TEST_URL,
        output_dir=str(output_dir),
        audio_format=TEST_AUDIO_FORMAT,
        output_template=TEST_OUTPUT_TEMPLATE
    )

    mock_ydl_instance.download.assert_called_once_with([TEST_URL])
    assert result_path is None


# --- Tests for YtdlpLogger ---

@patch('src.downloader.logger') # Patch the logger instance used by YtdlpLogger
def test_ytdlp_logger_info(mock_logger):
    """Tests YtdlpLogger.info method."""
    ytdlp_logger = YtdlpLogger()
    test_msg = "Info message"
    ytdlp_logger.info(test_msg)
    mock_logger.info.assert_called_once_with(f"yt-dlp: {test_msg}")

@patch('src.downloader.logger')
def test_ytdlp_logger_warning(mock_logger):
    """Tests YtdlpLogger.warning method."""
    ytdlp_logger = YtdlpLogger()
    test_msg = "Warning message"
    ytdlp_logger.warning(test_msg)
    mock_logger.warning.assert_called_once_with(f"yt-dlp: {test_msg}")

@patch('src.downloader.logger')
def test_ytdlp_logger_error(mock_logger):
    """Tests YtdlpLogger.error method."""
    ytdlp_logger = YtdlpLogger()
    test_msg = "Error message"
    ytdlp_logger.error(test_msg)
    mock_logger.error.assert_called_once_with(f"yt-dlp: {test_msg}")

@patch('src.downloader.logger')
def test_ytdlp_logger_debug_passes_info(mock_logger):
    """Tests YtdlpLogger.debug passes non-debug messages to info."""
    ytdlp_logger = YtdlpLogger()
    test_msg = "Not a real debug message"
    ytdlp_logger.debug(test_msg)
    mock_logger.info.assert_called_once_with(f"yt-dlp: {test_msg}")
    mock_logger.debug.assert_not_called()

@patch('src.downloader.logger')
def test_ytdlp_logger_debug_ignores_debug(mock_logger):
    """Tests YtdlpLogger.debug ignores messages starting with '[debug]'."""
    ytdlp_logger = YtdlpLogger()
    test_msg = "[debug] Detailed yt-dlp debug info"
    ytdlp_logger.debug(test_msg)
    mock_logger.info.assert_not_called()
    mock_logger.debug.assert_not_called()


@patch('src.downloader.yt_dlp.YoutubeDL')
def test_download_exception(mock_youtube_dl, tmp_path):
    """Tests download failure when yt-dlp raises a DownloadError."""
    output_dir = tmp_path / TEST_OUTPUT_DIR
    output_dir.mkdir()

    mock_ydl_instance = MagicMock()
    mock_youtube_dl.return_value.__enter__.return_value = mock_ydl_instance
    # Simulate download raising an exception
    mock_ydl_instance.download.side_effect = yt_dlp.utils.DownloadError("Test download error")

    result_path = download_audio_python_api(
        url=TEST_URL,
        output_dir=str(output_dir),
        audio_format=TEST_AUDIO_FORMAT,
        output_template=TEST_OUTPUT_TEMPLATE
    )

    mock_ydl_instance.download.assert_called_once_with([TEST_URL])
    assert result_path is None

@patch('src.downloader.yt_dlp.YoutubeDL')
def test_download_fallback_file_not_found(mock_youtube_dl, tmp_path):
    """Tests failure when fallback filename logic can't find the file."""
    output_dir = tmp_path / TEST_OUTPUT_DIR
    output_dir.mkdir()
    expected_prepared_path_no_ext = output_dir / f"{MOCK_INFO_DICT['id']}_test"
    expected_final_path = output_dir / f"{MOCK_INFO_DICT['id']}_test.{TEST_AUDIO_FORMAT}"

    mock_ydl_instance = MagicMock()
    mock_youtube_dl.return_value.__enter__.return_value = mock_ydl_instance

    mock_ydl_instance.download.return_value = 0 # Download succeeds
    mock_ydl_instance.extract_info.return_value = MOCK_INFO_DICT
    mock_ydl_instance.prepare_filename.return_value = str(expected_prepared_path_no_ext)

    # Mock os.path.exists to return False
    with patch('os.path.exists', return_value=False) as mock_exists:
        result_path = download_audio_python_api(
            url=TEST_URL,
            output_dir=str(output_dir),
            audio_format=TEST_AUDIO_FORMAT,
            output_template=TEST_OUTPUT_TEMPLATE
        )

        # Check if alternative extension was checked (if applicable)
        # The primary path check happens implicitly before the alternative path check in the code
        mock_exists.assert_any_call(str(expected_final_path)) # Ensure primary path was checked
        if TEST_AUDIO_FORMAT in ['opus', 'vorbis']:
             alt_ext = {'opus': 'webm', 'vorbis': 'ogg'}[TEST_AUDIO_FORMAT]
             alt_path = output_dir / f"{MOCK_INFO_DICT['id']}_test.{alt_ext}"
             mock_exists.assert_any_call(str(alt_path))

        assert result_path is None
