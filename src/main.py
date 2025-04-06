import argparse
import os
import logging
import sys
from dotenv import load_dotenv
from typing import List, Optional

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
    parser.add_argument("url", help="URL of the video to transcribe (YouTube, TikTok, Instagram, etc.)")
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

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
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
        sys.exit(1)

    # --- Download Audio ---
    # Use a simple ID-based template for the intermediate audio file
    audio_filename_template = "%(id)s"
    audio_path: Optional[str] = None
    try:
        logger.info("Step 1: Downloading and extracting audio...")
        audio_path = download_audio_python_api(
            url=args.url,
            output_dir=audio_output_dir,
            audio_format=args.audio_format,
            output_template=audio_filename_template # Use simple template for audio
        )
        if not audio_path:
            logger.error("Audio download/extraction failed. Exiting.")
            sys.exit(1)
        logger.info(f"Audio successfully saved to: {audio_path}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred during audio download: {e}")
        sys.exit(1)


    # --- Transcribe Audio ---
    transcript_result: Optional[dict] = None
    if audio_path:
        try:
            logger.info("Step 2: Transcribing audio...")
            # Prepare transcription arguments
            transcribe_args = {
                "language": args.language,
                "prompt": args.prompt,
                "temperature": args.temperature,
                "speaker_labels": args.speaker_labels,
                # Pass 'verbose_json' to get segments needed for SRT formatting
                "response_format": 'verbose_json'
            }
            # Filter out None values for cleaner API call
            transcribe_args = {k: v for k, v in transcribe_args.items() if v is not None}

            transcript_result = transcribe_audio_lemonfox(
                audio_path=audio_path,
                model_name=args.model,
                api_key=api_key,
                **transcribe_args
            )
            if not transcript_result:
                logger.error("Audio transcription failed. Exiting.")
                sys.exit(1)
            logger.info("Transcription completed.")
            # logger.debug(f"Transcription result: {transcript_result}") # Can be very verbose
        except Exception as e:
            logger.exception(f"An unexpected error occurred during transcription: {e}")
            sys.exit(1)


    # --- Format and Save Transcripts ---
    if transcript_result:
        logger.info("Step 3: Formatting and saving transcripts...")
        # Determine the base filename using the user's template
        # We need info from the download step for this. Let's re-extract minimal info.
        base_filename = "transcript" # Fallback filename
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'logger': logging.getLogger('yt_dlp_filename')}) as ydl:
                 info_dict = ydl.extract_info(args.url, download=False)
                 # Use the user-provided template for the final transcript filename
                 base_filename = ydl.prepare_filename(info_dict, outtmpl=args.output_filename_template)
                 # Remove any potential extension added by prepare_filename if template didn't include it
                 base_filename, _ = os.path.splitext(base_filename)
                 logger.info(f"Using base filename for transcripts: {base_filename}")
        except Exception as e:
            logger.warning(f"Could not extract info for filename template, using fallback '{base_filename}': {e}")


        output_base_path = os.path.join(args.output_dir, base_filename)

        success_count = 0
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
                    success_count += 1
                else:
                    logger.error(f"Failed to generate {fmt.upper()} file.")
            except Exception as e:
                 logger.exception(f"An unexpected error occurred during {fmt} formatting: {e}")


        if success_count == total_formats:
             logger.info("All requested transcript formats generated successfully.")
        elif success_count > 0:
             logger.warning(f"Generated {success_count}/{total_formats} requested transcript formats.")
        else:
             logger.error("Failed to generate any transcript formats.")


    # --- Cleanup ---
    if audio_path and os.path.exists(audio_path) and not args.keep_audio:
        try:
            logger.info(f"Cleaning up intermediate audio file: {audio_path}")
            os.remove(audio_path)
            # Attempt to remove the audio subdir if empty
            try:
                os.rmdir(audio_output_dir)
                logger.info(f"Removed empty audio directory: {audio_output_dir}")
            except OSError:
                logger.debug(f"Audio directory not empty, not removing: {audio_output_dir}")
        except OSError as e:
            logger.warning(f"Could not remove intermediate audio file {audio_path}: {e}")
    elif args.keep_audio:
         logger.info(f"Intermediate audio file kept at: {audio_path}")


    logger.info("TranscriptorApp finished.")


if __name__ == "__main__":
    main()
