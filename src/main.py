import argparse
import os
import logging
import sys
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any # Added Dict, Any
import yt_dlp # Added yt_dlp import here

# Add src directory to Python path to allow sibling imports
# Not strictly necessary if run as a module, but good for direct execution
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from .downloader import download_audio_python_api
    from .transcriber import transcribe_audio_lemonfox
    from .formatter import generate_txt, generate_srt
    from .pipeline import run_pipeline # Import the new pipeline function
except ImportError:
    # Fallback for running the script directly
    from downloader import download_audio_python_api
    from transcriber import transcribe_audio_lemonfox
    from formatter import generate_txt, generate_srt
    from pipeline import run_pipeline # Import the new pipeline function


# Configure logging
# Use basicConfig with force=True to ensure it's configured even if imported elsewhere
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger("TranscriptorApp")

# --- Constants ---
DEFAULT_OUTPUT_DIR = "transcripts"
DEFAULT_MODEL = "whisper-1" # Check Lemonfox docs for best/latest default
DEFAULT_AUDIO_FORMAT = "mp3"
DEFAULT_OUTPUT_FORMATS = ["txt", "srt"]
DEFAULT_FILENAME_TEMPLATE = "%(title)s [%(id)s]" # For transcript files
AUDIO_SUBDIR = "_audio_files" # Subdirectory for intermediate audio

def main():
    """Main function to parse arguments and run the transcription pipeline."""
    # Load environment variables from .env file
    load_dotenv()
    api_key = os.getenv("LEMONFOX_API_KEY")

    if not api_key:
        logger.error("Error: LEMONFOX_API_KEY not found in environment variables or .env file.")
        logger.error("Please create a .env file in the project root or set the environment variable.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Transcribe audio from video URLs using Lemonfox API.")
    # Changed "url" to "urls" and added nargs='+'
    parser.add_argument("urls", nargs='+', help="One or more video URLs to transcribe (space-separated)")
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to save transcripts and intermediate audio (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Transcription model to use (e.g., whisper-1, whisper-large-v3) (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--formats",
        nargs='+',
        choices=['txt', 'srt'],
        default=DEFAULT_OUTPUT_FORMATS,
        help=f"Output transcript formats (space-separated) (default: {' '.join(DEFAULT_OUTPUT_FORMATS)})"
    )
    parser.add_argument(
        "--audio-format",
        default=DEFAULT_AUDIO_FORMAT,
        help=f"Intermediate audio format for extraction (e.g., mp3, wav, opus) (default: {DEFAULT_AUDIO_FORMAT})"
    )
    parser.add_argument(
        "--output-filename-template",
        default=DEFAULT_FILENAME_TEMPLATE,
        # Prevent argparse from trying to format the default template string during help generation
        help=f"Template for the output transcript filename (without extension). Uses yt-dlp field names. Default: \"{DEFAULT_FILENAME_TEMPLATE.replace('%', '%%')}\""
    )
    parser.add_argument(
        "--language",
        help="Language code (ISO 639-1) for transcription (optional)"
    )
    parser.add_argument(
        "--prompt",
        help="Prompt to guide the transcription model (optional)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature (0.0 to 1.0) (default: 0.0)"
    )
    parser.add_argument(
        "--speaker-labels",
        action='store_true',
        help="Request speaker labels (if supported by Lemonfox model)"
    )
    parser.add_argument(
        "--keep-audio",
        action='store_true',
        help="Keep the intermediate audio file after transcription"
    )
    parser.add_argument(
        "--verbose",
        action='store_true',
        help="Enable verbose logging for debugging"
    )
    # TODO: Add --batch-file argument later if needed

    args = parser.parse_args()

    if args.verbose:
        # Set root logger level
        logging.getLogger().setLevel(logging.DEBUG)
        # Also set our specific logger level if needed
        logger.setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled.")

    # --- Directory Setup ---
    try:
        # Main output directory for transcripts
        os.makedirs(args.output_dir, exist_ok=True)
        # Subdirectory for intermediate audio files
        audio_output_dir = os.path.join(args.output_dir, AUDIO_SUBDIR)
        os.makedirs(audio_output_dir, exist_ok=True)
        logger.info(f"Output directory set to: {args.output_dir}")
        logger.info(f"Intermediate audio will be stored in: {audio_output_dir}")
    except OSError as e:
        logger.error(f"Failed to create output directories: {e}")
        sys.exit(1) # Exit if we can't create directories

    # --- Run Pipeline ---
    urls_to_process: List[str] = args.urls
    # Optional: Add logic here to read from args.batch_file if provided
    # and extend urls_to_process

    logger.info(f"Starting processing for {len(urls_to_process)} URL(s).")

    pipeline_results = run_pipeline(
        urls_to_process=urls_to_process,
        api_key=api_key,
        args=args,
        audio_output_dir=audio_output_dir
    )

    # --- Final Summary ---
    processed_count = pipeline_results.get('processed_count', 0)
    failed_urls = pipeline_results.get('failed_urls', [])
    total_attempted = len(urls_to_process)

    logger.info("="*20 + " Batch Summary " + "="*20)
    logger.info(f"Total URLs attempted: {total_attempted}")
    logger.info(f"Successfully processed: {processed_count}")
    if failed_urls:
        # Ensure uniqueness in case a URL failed multiple times internally (though unlikely with current logic)
        unique_failed_urls = sorted(list(set(failed_urls)))
        logger.warning(f"Failed URLs ({len(unique_failed_urls)}):")
        for failed_url in unique_failed_urls:
            logger.warning(f"  - {failed_url}")
    else:
        logger.info("All URLs processed successfully!")
    logger.info("="*55)

    logger.info("TranscriptorApp finished.")
    # Exit with error code if any URLs failed
    if failed_urls: # Check the failed_urls list from pipeline_results
        sys.exit(1)


if __name__ == "__main__":
    main()
