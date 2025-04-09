import logging
import os
from typing import Optional, Dict, Any
import yt_dlp

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YtdlpLogger:
    """Custom logger for yt-dlp to integrate with standard logging."""
    def debug(self, msg):
        # yt-dlp passes info messages to debug
        if msg.startswith('[debug] '):
            pass # Ignore verbose debug messages from yt-dlp
        else:
            self.info(msg)
    def info(self, msg):
        logger.info(f"yt-dlp: {msg}")
    def warning(self, msg):
        logger.warning(f"yt-dlp: {msg}")
    def error(self, msg):
        logger.error(f"yt-dlp: {msg}")

def download_audio_python_api(
    url: str,
    output_dir: str,
    audio_format: str = 'mp3',
    output_template: str = '%(id)s.%(ext)s'
) -> Optional[str]:
    """
    Downloads audio from a given URL using yt-dlp's Python API.

    Args:
        url: The URL of the video to download.
        output_dir: The directory to save the downloaded audio file.
        audio_format: The desired audio format (e.g., 'mp3', 'wav', 'opus').
        output_template: The filename template for the output file (without extension).

    Returns:
        The full path to the downloaded audio file, or None if download fails.
    """
    output_path_template = os.path.join(output_dir, output_template)
    final_filename = None # Variable to store the final filename

    def progress_hook(d: Dict[str, Any]):
        nonlocal final_filename
        if d['status'] == 'finished':
            # Store the final filename when download completes
            # yt-dlp might change the extension based on the postprocessor
            final_filename = d.get('filename')
            logger.info(f"Download finished. File saved (potentially temporarily) as: {d.get('filename')}")
        elif d['status'] == 'error':
            logger.error("Error during download hook.")
        # You can add more detailed progress reporting here if needed
        # elif d['status'] == 'downloading':
        #     p = d['_percent_str']
        #     s = d['_speed_str']
        #     e = d['_eta_str']
        #     logger.info(f"{p} of {d['total_bytes_str']} at {s}, ETA {e}")

    ydl_opts: Dict[str, Any] = {
        'format': 'bestaudio/best', # Select best audio-only format, fallback to best combined
        'outtmpl': output_path_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_format,
            # 'preferredquality': '192', # Optional: set audio quality
        }],
        'logger': YtdlpLogger(),
        'progress_hooks': [progress_hook],
        'noprogress': True, # Disable default progress bar, use hook instead
        'quiet': True, # Suppress yt-dlp console output, rely on logger
        # 'verbose': True, # Uncomment for detailed yt-dlp debugging
        'ignoreerrors': False, # Stop on download errors
        'paths': {'home': output_dir} # Ensure final file is in output_dir
    }

    logger.info(f"Starting audio download for URL: {url}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Requested audio format: {audio_format}")
    logger.info(f"Output template: {output_path_template}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            error_code = ydl.download([url])
            if error_code != 0:
                logger.error(f"yt-dlp download failed with error code: {error_code}")
                return None

            # After download, determine the exact output filename
            # The hook should have captured it, but we can try to reconstruct if needed
            if final_filename and os.path.exists(final_filename):
                 logger.info(f"Successfully downloaded and extracted audio to: {final_filename}")
                 return final_filename
            else:
                # Fallback: Try to find the file based on the template and expected extension
                # This is less reliable as yt-dlp might adjust the filename slightly
                logger.warning("Could not reliably determine final filename from hook. Attempting fallback.")
                # Use prepare_filename to get the expected path *before* download
                # This might not reflect the final extension after postprocessing
                info_dict = ydl.extract_info(url, download=False)
                expected_path_no_ext = ydl.prepare_filename(info_dict, outtmpl=output_path_template)
                expected_path = f"{expected_path_no_ext}.{audio_format}"

                if os.path.exists(expected_path):
                    logger.info(f"Successfully downloaded and extracted audio (fallback check): {expected_path}")
                    return expected_path
                else:
                    # Check common alternatives if the exact format wasn't used
                    alt_formats = {'opus': 'webm', 'vorbis': 'ogg'}
                    if audio_format in alt_formats:
                        alt_ext = alt_formats[audio_format]
                        alt_path = f"{expected_path_no_ext}.{alt_ext}"
                        if os.path.exists(alt_path):
                             logger.info(f"Successfully downloaded and extracted audio (fallback check with alt ext): {alt_path}")
                             return alt_path

                    logger.error(f"Download seemed successful, but could not find the final audio file. Expected path pattern: {expected_path} or similar.")
                    return None

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"yt-dlp download error: {e}")
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred during download: {e}")
        return None

if __name__ == '__main__':
    # Example usage (for testing the module directly)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Example YouTube URL
    test_output_dir = "downloaded_audio_test"
    os.makedirs(test_output_dir, exist_ok=True)

    print(f"Testing downloader with URL: {test_url}")
    audio_file = download_audio_python_api(test_url, test_output_dir, audio_format='mp3')

    if audio_file:
        print(f"\nTest successful! Audio downloaded to: {audio_file}")
        # Optional: Clean up test file
        # os.remove(audio_file)
        # os.rmdir(test_output_dir)
    else:
        print("\nTest failed. Audio download was unsuccessful.")
