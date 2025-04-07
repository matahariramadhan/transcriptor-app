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
except ImportError:
    # Fallback for running the script directly
    from downloader import download_audio_python_api
    from transcriber import transcribe_audio_lemonfox
    from formatter import generate_txt, generate_srt


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

    # --- Batch Processing Loop ---
    processed_urls_count = 0
    failed_urls_list: List[str] = []
    urls_to_process: List[str] = args.urls

    # Optional: Add logic here to read from args.batch_file if provided
    # and extend urls_to_process

    total_urls = len(urls_to_process)
    logger.info(f"Starting batch processing for {total_urls} URL(s).")

    # Use a single yt-dlp instance for filename extraction if possible
    # Initialize outside the loop to avoid repeated setup
    ydl_filename_extractor = yt_dlp.YoutubeDL({
        'quiet': True,
        'logger': logging.getLogger('yt_dlp_filename'),
        'extract_flat': 'in_playlist', # Faster extraction for playlists if only filename needed
        'skip_download': True
    })


    for index, current_url in enumerate(urls_to_process):
        logger.info(f"--- Processing URL {index + 1}/{total_urls}: {current_url} ---")
        audio_path: Optional[str] = None
        transcript_result: Optional[Dict[str, Any]] = None
        url_success = False # Flag to track success for this specific URL

        try:
            # --- Download Audio ---
            # Use a simple ID-based template for the intermediate audio file
            audio_filename_template = "%(id)s"
            logger.info("Step 1: Downloading and extracting audio...")
            audio_path = download_audio_python_api(
                url=current_url, # Use current_url from loop
                output_dir=audio_output_dir,
                audio_format=args.audio_format,
                output_template=audio_filename_template
            )
            if not audio_path:
                logger.error(f"Audio download/extraction failed for {current_url}. Skipping.")
                failed_urls_list.append(current_url)
                continue # Move to the next URL

            logger.info(f"Audio successfully saved to: {audio_path}")

            # --- Transcribe Audio ---
            logger.info("Step 2: Transcribing audio...")
            # Prepare transcription arguments
            transcribe_args = {
                "language": args.language,
                "prompt": args.prompt,
                "temperature": args.temperature,
                "speaker_labels": args.speaker_labels,
                "response_format": 'verbose_json' # Needed for SRT
            }
            transcribe_args = {k: v for k, v in transcribe_args.items() if v is not None}

            transcript_result = transcribe_audio_lemonfox(
                audio_path=audio_path,
                model_name=args.model,
                api_key=api_key,
                **transcribe_args
            )
            if not transcript_result:
                logger.error(f"Audio transcription failed for {current_url}. Skipping.")
                failed_urls_list.append(current_url)
                continue # Move to the next URL

            logger.info("Transcription completed.")

            # --- Format and Save Transcripts ---
            logger.info("Step 3: Formatting and saving transcripts...")
            # Determine the base filename using the user's template for the current URL
            base_filename = "transcript" # Fallback filename
            try:
                 # Use the pre-initialized extractor
                 info_dict = ydl_filename_extractor.extract_info(current_url, download=False)
                 # Handle potential playlist entries if extract_flat was used
                 if 'entries' in info_dict and info_dict['entries']:
                     # Use info from the first entry if it's a playlist URL itself
                     entry_info = info_dict['entries'][0]
                     # Check if the entry itself is a playlist (less common)
                     if 'entries' in entry_info and entry_info['entries']:
                         logger.warning("Nested playlist detected for filename extraction, using first video.")
                         entry_info = entry_info['entries'][0]
                     # Merge top-level playlist info with entry info for template
                     merged_info = {**info_dict, **entry_info}
                     # Remove 'entries' to avoid issues with prepare_filename if it expects a single video dict
                     merged_info.pop('entries', None)
                     info_dict = merged_info
                 elif 'entries' in info_dict: # Playlist URL but no entries extracted (maybe empty or error)
                     logger.warning(f"Could not extract video entry info from playlist URL {current_url} for filename template.")
                     # Use playlist info directly if available
                     pass # info_dict already contains playlist info

                 base_filename = ydl_filename_extractor.prepare_filename(info_dict, outtmpl=args.output_filename_template)
                 base_filename, _ = os.path.splitext(base_filename)
                 logger.info(f"Using base filename for transcripts: {base_filename}")
            except Exception as e:
                logger.warning(f"Could not extract info for filename template for {current_url}, using fallback '{base_filename}': {e}")

            output_base_path = os.path.join(args.output_dir, base_filename)
            format_success_count = 0
            total_formats = len(args.formats)

            for fmt in args.formats:
                output_file_path = f"{output_base_path}.{fmt}"
                logger.info(f"Generating {fmt.upper()} format...")
                success = False
                try:
                    if fmt == 'txt':
                        success = generate_txt(transcript_result, output_file_path)
                    elif fmt == 'srt':
                        success = generate_srt(transcript_result, output_file_path)

                    if success:
                        logger.info(f"{fmt.upper()} file saved to: {output_file_path}")
                        format_success_count += 1
                    else:
                        logger.error(f"Failed to generate {fmt.upper()} file for {current_url}.")
                except Exception as e:
                     logger.exception(f"An unexpected error occurred during {fmt} formatting for {current_url}: {e}")

            if format_success_count == total_formats:
                 logger.info(f"All requested transcript formats generated successfully for {current_url}.")
                 url_success = True # Mark this URL as fully successful
            elif format_success_count > 0:
                 logger.warning(f"Generated {format_success_count}/{total_formats} requested transcript formats for {current_url}.")
                 url_success = True # Mark as partially successful counts as processed
            else:
                 logger.error(f"Failed to generate any transcript formats for {current_url}.")
                 failed_urls_list.append(current_url) # Add to failed list if no formats generated

            if url_success:
                processed_urls_count += 1

        except Exception as e:
            logger.exception(f"An critical unexpected error occurred processing {current_url}: {e}. Skipping.")
            if current_url not in failed_urls_list: # Avoid double listing
                 failed_urls_list.append(current_url)
        finally:
            # --- Cleanup (runs even if errors occurred mid-process for a URL) ---
            if audio_path and os.path.exists(audio_path) and not args.keep_audio:
                try:
                    logger.info(f"Cleaning up intermediate audio file: {audio_path}")
                    os.remove(audio_path)
                    # Attempt to remove the audio subdir if empty (might fail if other files exist)
                    try:
                        os.rmdir(audio_output_dir)
                        logger.debug(f"Removed empty audio directory: {audio_output_dir}")
                    except OSError:
                        logger.debug(f"Audio directory not empty or error removing, skipping: {audio_output_dir}")
                except OSError as e:
                    logger.warning(f"Could not remove intermediate audio file {audio_path}: {e}")
            elif audio_path and args.keep_audio:
                 logger.info(f"Intermediate audio file kept at: {audio_path}")

            logger.info(f"--- Finished processing URL: {current_url} ---")


    # --- Final Summary ---
    logger.info("="*20 + " Batch Summary " + "="*20)
    logger.info(f"Total URLs attempted: {total_urls}")
    logger.info(f"Successfully processed: {processed_urls_count}")
    if failed_urls_list:
        # Remove duplicates from failed list before printing
        unique_failed_urls = sorted(list(set(failed_urls_list)))
        logger.warning(f"Failed URLs ({len(unique_failed_urls)}):")
        for failed_url in unique_failed_urls:
            logger.warning(f"  - {failed_url}")
    else:
        logger.info("All URLs processed successfully!")
    logger.info("="*55)

    logger.info("TranscriptorApp finished.")
    # Exit with error code if any URLs failed
    if failed_urls_list:
        sys.exit(1)


if __name__ == "__main__":
    main()
