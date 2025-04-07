import argparse
import os
import logging
from typing import List, Optional, Dict, Any
import yt_dlp

# Assuming these are imported correctly relative to the src directory
try:
    from .downloader import download_audio_python_api
    from .transcriber import transcribe_audio_lemonfox
    from .formatter import generate_txt, generate_srt
except ImportError:
    # Fallback for potential execution context issues (less likely if run via main)
    from downloader import download_audio_python_api
    from transcriber import transcribe_audio_lemonfox
    from formatter import generate_txt, generate_srt

logger = logging.getLogger("TranscriptorApp.Pipeline") # Use a child logger

def run_pipeline(
    urls_to_process: List[str],
    api_key: str,
    args: argparse.Namespace,
    audio_output_dir: str
) -> Dict[str, Any]:
    """
    Runs the core transcription pipeline for a list of URLs.

    Args:
        urls_to_process: List of URLs to process.
        api_key: The Lemonfox API key.
        args: The parsed command-line arguments namespace.
        audio_output_dir: The directory to store intermediate audio files.

    Returns:
        A dictionary containing processing results, e.g.,
        {'processed_count': int, 'failed_urls': List[str]}
    """
    processed_urls_count = 0
    failed_urls_list: List[str] = []
    total_urls = len(urls_to_process)

    logger.info(f"Pipeline started for {total_urls} URL(s).")

    # Initialize yt-dlp instance for filename extraction here
    # (Moved from main.py)
    ydl_filename_extractor = yt_dlp.YoutubeDL({
        'quiet': True,
        'logger': logging.getLogger('yt_dlp_filename'), # Can use a specific logger
        'extract_flat': 'in_playlist',
        'skip_download': True
    })

    # --- Batch Processing Loop ---
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
            # Filter out None values before passing to API
            transcribe_args = {k: v for k, v in transcribe_args.items() if v is not None and v is not False} # Also filter False for speaker_labels if not set

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
                     # Prioritize entry info over playlist info in case of conflicts (e.g., title)
                     merged_info = {**info_dict, **entry_info}
                     # Remove 'entries' to avoid issues with prepare_filename if it expects a single video dict
                     merged_info.pop('entries', None)
                     info_dict = merged_info
                 elif 'entries' in info_dict: # Playlist URL but no entries extracted (maybe empty or error)
                     logger.warning(f"Could not extract video entry info from playlist URL {current_url} for filename template.")
                     # Use playlist info directly if available
                     pass # info_dict already contains playlist info

                 base_filename = ydl_filename_extractor.prepare_filename(info_dict, outtmpl=args.output_filename_template)
                 # Remove extension that prepare_filename might add if template doesn't have one
                 base_filename, _ = os.path.splitext(base_filename)
                 logger.info(f"Using base filename for transcripts: {base_filename}")
            except Exception as e:
                logger.warning(f"Could not extract info for filename template for {current_url}, using fallback '{base_filename}': {e}")

            # Use the main output dir from args for the final transcript files
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
                 if current_url not in failed_urls_list: # Avoid double listing if download/transcribe failed
                    failed_urls_list.append(current_url)

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
                    # Check if dir exists before trying to remove
                    if os.path.exists(audio_output_dir):
                        try:
                            os.rmdir(audio_output_dir)
                            logger.debug(f"Removed empty audio directory: {audio_output_dir}")
                        except OSError:
                            # Directory not empty or other error, fine to ignore
                            logger.debug(f"Audio directory not empty or error removing, skipping: {audio_output_dir}")
                except OSError as e:
                    logger.warning(f"Could not remove intermediate audio file {audio_path}: {e}")
            elif audio_path and args.keep_audio:
                 logger.info(f"Intermediate audio file kept at: {audio_path}")

            logger.info(f"--- Finished processing URL: {current_url} ---")

    logger.info(f"Pipeline finished. Processed: {processed_urls_count}, Failed: {len(failed_urls_list)}")

    return {
        'processed_count': processed_urls_count,
        'failed_urls': failed_urls_list
    }
