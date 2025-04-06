import logging
import os
from typing import Dict, Any, List, Optional
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _format_timestamp(seconds: float, separator: str = ',') -> str:
    """Formats seconds into SRT timestamp format (HH:MM:SS,ms)."""
    delta = timedelta(seconds=seconds)
    hours, remainder = divmod(delta.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}{separator}{milliseconds:03}"

def generate_txt(transcript_result: Dict[str, Any], output_path: str) -> bool:
    """
    Generates a plain text (.txt) transcript file.

    Args:
        transcript_result: The dictionary result from the transcription API
                           (expected to have a 'text' key or 'segments').
        output_path: The full path to save the .txt file.

    Returns:
        True if the file was written successfully, False otherwise.
    """
    logger.info(f"Generating TXT transcript at: {output_path}")
    try:
        # Prefer the overall 'text' field if available
        full_text = transcript_result.get('text')

        # If 'text' isn't top-level, reconstruct from segments
        if full_text is None and 'segments' in transcript_result:
            segments: List[Dict[str, Any]] = transcript_result.get('segments', [])
            full_text = "\n".join(segment.get('text', '').strip() for segment in segments if segment.get('text'))
            logger.info("Reconstructed text from segments for TXT output.")

        if full_text is None:
             logger.error("Could not find 'text' or 'segments' in transcription result for TXT generation.")
             return False

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_text.strip() + '\n') # Ensure a trailing newline
        logger.info("TXT file generated successfully.")
        return True
    except IOError as e:
        logger.error(f"Failed to write TXT file to {output_path}: {e}")
        return False
    except Exception as e:
        logger.exception(f"An unexpected error occurred during TXT generation: {e}")
        return False

def generate_srt(transcript_result: Dict[str, Any], output_path: str) -> bool:
    """
    Generates a SubRip Subtitle (.srt) transcript file.

    Requires 'segments' with 'start', 'end', and 'text' in the transcript_result.
    Optionally uses 'speaker' if available within segments.

    Args:
        transcript_result: The dictionary result from the transcription API
                           (expected to have a 'segments' list).
        output_path: The full path to save the .srt file.

    Returns:
        True if the file was written successfully, False otherwise.
    """
    logger.info(f"Generating SRT transcript at: {output_path}")
    segments: Optional[List[Dict[str, Any]]] = transcript_result.get('segments')

    if not segments:
        logger.error("SRT generation requires 'segments' in the transcription result.")
        # Attempt fallback to 'text' if no segments exist? Maybe not ideal for SRT.
        # Check if response_format was 'srt' directly from API?
        api_text = transcript_result.get('text')
        if isinstance(api_text, str) and '-->' in api_text:
             logger.warning("Result seems to contain SRT data directly in 'text'. Writing as is.")
             try:
                 os.makedirs(os.path.dirname(output_path), exist_ok=True)
                 with open(output_path, 'w', encoding='utf-8') as f:
                     f.write(api_text)
                 logger.info("SRT file written directly from API response text.")
                 return True
             except Exception as e:
                 logger.exception(f"Failed to write direct SRT text: {e}")
                 return False
        else:
             logger.error("No 'segments' found and 'text' does not appear to be SRT format.")
             return False


    srt_content = []
    segment_count = 0
    for i, segment in enumerate(segments):
        start_time = segment.get('start')
        end_time = segment.get('end')
        text = segment.get('text', '').strip()
        speaker = segment.get('speaker') # Optional speaker label

        if start_time is None or end_time is None or not text:
            logger.warning(f"Skipping segment {i+1} due to missing start/end time or text.")
            continue

        segment_count += 1
        start_str = _format_timestamp(start_time)
        end_str = _format_timestamp(end_time)

        srt_content.append(str(segment_count))
        srt_content.append(f"{start_str} --> {end_str}")
        if speaker:
            srt_content.append(f"({speaker}) {text}")
        else:
            srt_content.append(text)
        srt_content.append("") # Blank line separator

    if not srt_content:
        logger.error("No valid segments found to generate SRT content.")
        return False

    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(srt_content))
        logger.info("SRT file generated successfully.")
        return True
    except IOError as e:
        logger.error(f"Failed to write SRT file to {output_path}: {e}")
        return False
    except Exception as e:
        logger.exception(f"An unexpected error occurred during SRT generation: {e}")
        return False

if __name__ == '__main__':
    # Example usage (using dummy data)
    print("Testing formatter module...")
    dummy_result_simple = {
        "text": "This is a simple transcript."
    }
    dummy_result_verbose = {
        "task": "transcribe",
        "language": "en",
        "duration": 10.5,
        "text": "Hello world. This is a test.",
        "segments": [
            {
                "id": 0, "seek": 0, "start": 0.0, "end": 2.5, "text": " Hello world.",
                "tokens": [1, 2], "temperature": 0.0, "avg_logprob": -0.5,
                "compression_ratio": 1.0, "no_speech_prob": 0.1, "speaker": "SPEAKER_00"
            },
            {
                "id": 1, "seek": 0, "start": 3.0, "end": 5.8, "text": " This is a test.",
                "tokens": [3, 4, 5], "temperature": 0.0, "avg_logprob": -0.6,
                "compression_ratio": 1.1, "no_speech_prob": 0.05 # Missing speaker intentionally
            },
            { # Segment with missing time
                "id": 2, "seek": 0, "start": None, "end": 7.0, "text": " Missing start time."
            },
             { # Segment with missing text
                "id": 3, "seek": 0, "start": 8.0, "end": 9.0, "text": ""
            }
        ]
    }
    dummy_result_srt_in_text = {
        "text": "1\n00:00:00,123 --> 00:00:02,456\nHello\n\n2\n00:00:03,000 --> 00:00:05,000\nWorld\n"
    }


    test_output_dir = "formatter_test_output"
    os.makedirs(test_output_dir, exist_ok=True)

    txt_path_simple = os.path.join(test_output_dir, "simple.txt")
    txt_path_verbose = os.path.join(test_output_dir, "verbose.txt")
    srt_path_verbose = os.path.join(test_output_dir, "verbose.srt")
    srt_path_simple_fail = os.path.join(test_output_dir, "simple_fail.srt")
    srt_path_from_text = os.path.join(test_output_dir, "from_text.srt")

    print("\nTesting generate_txt (simple):")
    success_txt_simple = generate_txt(dummy_result_simple, txt_path_simple)
    print(f"Result: {'Success' if success_txt_simple else 'Fail'}")
    if success_txt_simple: print(f"Content:\n---\n{open(txt_path_simple).read()}---")

    print("\nTesting generate_txt (verbose):")
    success_txt_verbose = generate_txt(dummy_result_verbose, txt_path_verbose)
    print(f"Result: {'Success' if success_txt_verbose else 'Fail'}")
    if success_txt_verbose: print(f"Content:\n---\n{open(txt_path_verbose).read()}---")

    print("\nTesting generate_srt (verbose):")
    success_srt_verbose = generate_srt(dummy_result_verbose, srt_path_verbose)
    print(f"Result: {'Success' if success_srt_verbose else 'Fail'}")
    if success_srt_verbose: print(f"Content:\n---\n{open(srt_path_verbose).read()}---")

    print("\nTesting generate_srt (simple - expected fail):")
    success_srt_simple = generate_srt(dummy_result_simple, srt_path_simple_fail)
    print(f"Result: {'Success' if success_srt_simple else 'Fail'}")

    print("\nTesting generate_srt (from text):")
    success_srt_from_text = generate_srt(dummy_result_srt_in_text, srt_path_from_text)
    print(f"Result: {'Success' if success_srt_from_text else 'Fail'}")
    if success_srt_from_text: print(f"Content:\n---\n{open(srt_path_from_text).read()}---")

    # Optional: Clean up
    # import shutil
    # shutil.rmtree(test_output_dir)
    print(f"\nTest files generated in: {test_output_dir}")
