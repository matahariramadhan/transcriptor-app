import logging
import os
from typing import Optional, Dict, Any
from openai import OpenAI, APIError, APIConnectionError, RateLimitError, AuthenticationError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Lemonfox API endpoint
LEMONFOX_API_BASE_URL = "https://api.lemonfox.ai/v1"

def transcribe_audio_lemonfox(
    audio_path: str,
    model_name: str,
    api_key: str,
    language: Optional[str] = None,
    prompt: Optional[str] = None,
    response_format: str = 'json', # 'json', 'text', 'srt', 'verbose_json', or 'vtt'
    temperature: float = 0.0,
    speaker_labels: bool = False,
    **kwargs: Any # To catch any other potential API parameters
) -> Optional[Dict[str, Any]]:
    """
    Transcribes an audio file using the Lemonfox API (OpenAI-compatible).

    Args:
        audio_path: Path to the audio file to transcribe.
        model_name: The name of the Whisper model to use (e.g., 'whisper-1', 'whisper-large-v3').
                    Check Lemonfox documentation for supported models.
        api_key: Your Lemonfox API key.
        language: Optional language code (ISO 639-1 format) for transcription.
        prompt: Optional text to guide the model's style or continue previous audio.
        response_format: The desired format of the transcript.
        temperature: Sampling temperature (0-1). Higher values make output more random.
        speaker_labels: Whether to request speaker labels (if supported by Lemonfox).
        **kwargs: Additional parameters to pass to the API.

    Returns:
        A dictionary containing the transcription result, or None if transcription fails.
        The structure depends on the 'response_format'. For 'json' or 'verbose_json',
        it's a dictionary. For 'text', 'srt', 'vtt', it might be a string within a dict.
    """
    if not api_key:
        logger.error("Lemonfox API key is missing.")
        return None

    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found at path: {audio_path}")
        return None

    logger.info(f"Initializing Lemonfox client for model: {model_name}")
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=LEMONFOX_API_BASE_URL,
        )
    except Exception as e:
        logger.exception(f"Failed to initialize OpenAI client: {e}")
        return None

    logger.info(f"Starting transcription for: {audio_path}")
    logger.info(f"Using model: {model_name}, Response format: {response_format}, Speaker Labels: {speaker_labels}")
    if language:
        logger.info(f"Language specified: {language}")
    if prompt:
        logger.info("Prompt provided.")

    try:
        with open(audio_path, "rb") as audio_file:
            # Prepare API parameters
            api_params = {
                "model": model_name,
                "file": audio_file,
                "response_format": response_format,
                "temperature": temperature,
                **kwargs # Include any extra parameters passed
            }
            if language:
                api_params["language"] = language
            if prompt:
                api_params["prompt"] = prompt
            if speaker_labels:
                # Note: Parameter name might differ for Lemonfox, check their docs
                # Assuming it's 'speaker_labels' based on the design doc
                api_params["speaker_labels"] = True

            logger.debug(f"Calling Lemonfox API with params: { {k: v for k, v in api_params.items() if k != 'file'} }") # Don't log file object

            transcription = client.audio.transcriptions.create(**api_params)

            logger.info("Transcription successful.")

            # The result type depends on response_format.
            # For 'json' or 'verbose_json', it's usually an object with attributes.
            # For others, it might be a simple string. We'll return the raw object.
            # If it has a model_dump method (like Pydantic models), use it for better dict representation.
            if hasattr(transcription, 'model_dump'):
                 result_dict = transcription.model_dump()
                 logger.debug(f"Transcription result (dict): {result_dict}")
                 return result_dict
            elif isinstance(transcription, dict):
                 logger.debug(f"Transcription result (dict): {transcription}")
                 return transcription
            elif isinstance(transcription, str):
                 # Wrap string results in a dictionary for consistency
                 logger.debug(f"Transcription result (text): {transcription[:100]}...") # Log snippet
                 return {"text": transcription}
            else:
                 logger.warning(f"Unexpected transcription result type: {type(transcription)}. Returning as is.")
                 return transcription # Return raw object if unsure

    except AuthenticationError as e:
        logger.error(f"Lemonfox authentication error: {e}. Check your API key.")
        return None
    except RateLimitError as e:
        logger.error(f"Lemonfox rate limit exceeded: {e}")
        return None
    except APIConnectionError as e:
        logger.error(f"Could not connect to Lemonfox API: {e}")
        return None
    except APIError as e:
        logger.error(f"Lemonfox API error: Status={e.status_code}, Message={e.message}")
        return None
    except FileNotFoundError:
        logger.error(f"Audio file not found during transcription attempt: {audio_path}")
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred during transcription: {e}")
        return None

if __name__ == '__main__':
    # Example usage (requires a valid API key in env and an audio file)
    print("Testing transcriber module...")
    api_key_from_env = os.getenv("LEMONFOX_API_KEY")
    test_audio_file = "downloaded_audio_test/dQw4w9WgXcQ.mp3" # Assumes downloader test ran

    if not api_key_from_env:
        print("Error: LEMONFOX_API_KEY environment variable not set.")
    elif not os.path.exists(test_audio_file):
        print(f"Error: Test audio file not found at {test_audio_file}. Run downloader test first.")
    else:
        print(f"Found API key and test audio file: {test_audio_file}")
        print("Attempting transcription (using whisper-1)...")

        # Load dotenv specifically for testing if run directly
        from dotenv import load_dotenv
        load_dotenv()
        api_key_from_env = os.getenv("LEMONFOX_API_KEY") # Reload after load_dotenv

        if not api_key_from_env:
             print("Error: LEMONFOX_API_KEY still not found after trying to load .env.")
        else:
            transcript_result = transcribe_audio_lemonfox(
                audio_path=test_audio_file,
                model_name="whisper-1", # Use a standard model name
                api_key=api_key_from_env,
                response_format='verbose_json', # Get detailed output
                speaker_labels=True # Example: request speaker labels
            )

            if transcript_result:
                print("\nTest transcription successful!")
                # Print structure or specific fields
                if isinstance(transcript_result, dict):
                    print(f"  Duration: {transcript_result.get('duration')}")
                    print(f"  Language: {transcript_result.get('language')}")
                    print(f"  Text snippet: {transcript_result.get('text', '')[:100]}...")
                    if 'segments' in transcript_result:
                        print(f"  Number of segments: {len(transcript_result['segments'])}")
                        if transcript_result['segments']:
                             first_segment = transcript_result['segments'][0]
                             print(f"  First segment speaker: {first_segment.get('speaker', 'N/A')}")
                else:
                    print(f"  Result: {transcript_result}")

            else:
                print("\nTest transcription failed.")
