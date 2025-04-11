import os
import sys
import threading
import logging
import time
import uuid
from typing import Dict, Any, List
from pathlib import Path # Add this import

# Add project root to Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Import from the installed transcriptor_core package
from transcriptor_core.pipeline import run_pipeline
from dotenv import load_dotenv

# Import or define status constants (ensure consistency with main.py)
# If importing directly causes issues (e.g., circular imports), redefine them here.
STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_DOWNLOADING = "downloading"
STATUS_TRANSCRIBING = "transcribing"
STATUS_FORMATTING = "formatting"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_CANCELLING = "cancelling"
STATUS_CANCELLED = "cancelled"

# Configure logging for the processing module
logger = logging.getLogger("TranscriptorApp.WebProcessing")
# Ensure handlers are configured (could inherit from main app's logger setup)
if not logger.hasHandlers():
     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# --- Job Management (using the shared 'jobs' dict from web/main.py) ---
# This is a simplified approach. In a real app, use a proper task queue (Celery, RQ)
# and a more robust storage mechanism (Redis, DB).
# We'll pass the 'jobs' dictionary from main.py to functions here.

def run_transcription_job_in_background(
    job_id: str,
    urls: List[str],
    config: Dict[str, Any],
    jobs_dict: Dict[str, Any], # Pass the shared jobs dictionary
):
    """
    Runs the transcription pipeline in a separate thread and updates job status via callback.
    """
    logger.info(f"Starting background job {job_id} for URLs: {urls}")

    # --- Define Status Update Callback ---
    def update_status(new_status: str):
        # Check for cancellation *before* updating status, except when setting to CANCELLED
        if new_status != STATUS_CANCELLED and jobs_dict.get(job_id, {}).get('cancelled', False):
            logger.info(f"Job {job_id}: Cancellation detected during status update to '{new_status}'. Setting to CANCELLED instead.")
            if job_id in jobs_dict:
                jobs_dict[job_id]["status"] = STATUS_CANCELLED
            return # Don't proceed with the original status update

        if job_id in jobs_dict:
            # Avoid overwriting a final state like CANCELLED with an intermediate one
            current_status = jobs_dict[job_id].get("status")
            if current_status == STATUS_CANCELLED and new_status != STATUS_CANCELLED:
                 logger.warning(f"Job {job_id}: Attempted to update status from CANCELLED to {new_status}. Ignoring.")
                 return

            logger.info(f"Job {job_id}: Status changing to '{new_status}'")
            jobs_dict[job_id]["status"] = new_status
            logger.debug(f"Job {job_id}: jobs_dict updated. Current status: {jobs_dict[job_id].get('status')}")
        else:
            logger.warning(f"Job {job_id}: Tried to update status to '{new_status}', but job not found in dict.")

    # --- Check for Cancellation Before Starting ---
    if jobs_dict.get(job_id, {}).get('cancelled', False):
        logger.info(f"Job {job_id}: Detected cancellation request before starting processing.")
        update_status(STATUS_CANCELLED)
        return # Exit thread <-- Corrected indentation

    # --- Load API Key ---
    # Determine the correct path to .env file, considering packaged state
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        # .env file was added to the bundle root in the .spec file
        bundle_dir = Path(sys._MEIPASS)
        dotenv_path = bundle_dir / '.env'
        logger.info(f"Job {job_id}: Running frozen, attempting to load .env from {dotenv_path}")
    else:
        # Running as a normal script
        # Assume .env is in the project root relative to this script's original location
        script_dir = Path(__file__).parent.parent.parent # Navigate up to transcriptor-app
        dotenv_path = script_dir / '.env'
        logger.info(f"Job {job_id}: Running as script, attempting to load .env from {dotenv_path}")

    loaded = load_dotenv(dotenv_path=dotenv_path, verbose=True)
    if not loaded:
         logger.warning(f"Job {job_id}: .env file not found or failed to load from {dotenv_path}")

    api_key = os.getenv("LEMONFOX_API_KEY")

    if not api_key:
        logger.error(f"Job {job_id}: LEMONFOX_API_KEY not found for background thread.")
        update_status(STATUS_FAILED) # Use callback
        jobs_dict[job_id]["error"] = "API key not configured."
        return

    # Define output directories relative to project root or a configurable path
    # For simplicity, let's create job-specific output dirs within a main 'web_outputs' dir
    base_output_dir = os.path.join(PROJECT_ROOT, "web_outputs")
    job_output_dir = os.path.join(base_output_dir, job_id)
    job_audio_output_dir = os.path.join(job_output_dir, "_audio_files")

    try:
        os.makedirs(job_output_dir, exist_ok=True)
        os.makedirs(job_audio_output_dir, exist_ok=True)
        logger.info(f"Job {job_id}: Output will be saved to {job_output_dir}")

        # jobs_dict[job_id]["status"] = "processing" # Removed: Status updated via callback now
        jobs_dict[job_id]["output_dir"] = job_output_dir # Store output path

        # --- Check for Cancellation Before Running Pipeline ---
        if jobs_dict.get(job_id, {}).get('cancelled', False):
            logger.info(f"Job {job_id}: Detected cancellation request before running core pipeline.")
            update_status(STATUS_CANCELLED)
            return # Exit thread

        # --- Run the Core Pipeline ---
        # Pass the status update callback
        # Note: The core pipeline logs progress internally
        # TODO: Consider adding cancellation checks *within* run_pipeline if possible,
        #       or make run_pipeline accept a check function. For now, we only check before it starts.
        pipeline_results = run_pipeline(
            urls_to_process=urls,
            api_key=api_key,
            config=config,
            audio_output_dir=job_audio_output_dir,
            output_dir=job_output_dir, # Pass job-specific output dir
            status_update_callback=update_status # Pass the callback
        )
    except Exception as e:
        # --- Handle critical errors during pipeline execution ---
        logger.exception(f"Job {job_id}: Critical error during background processing: {e}")
        update_status(STATUS_FAILED) # Use callback to set status
        jobs_dict[job_id]["error"] = f"An unexpected error occurred: {str(e)}"
    else:
        # --- Check for Cancellation After Pipeline Finishes (before setting final status) ---
        if jobs_dict.get(job_id, {}).get('cancelled', False):
             logger.info(f"Job {job_id}: Detected cancellation request after pipeline finished. Setting status to CANCELLED.")
             update_status(STATUS_CANCELLED)
             # Optionally list files created before cancellation detected
             try:
                 jobs_dict[job_id]["files"] = [f for f in os.listdir(job_output_dir) if os.path.isfile(os.path.join(job_output_dir, f)) and not f.startswith('.')]
             except FileNotFoundError:
                 jobs_dict[job_id]["files"] = []
             return # Exit thread

        # --- Update Final Job Status Based on Results (if pipeline didn't crash and wasn't cancelled) ---
        if not pipeline_results.get('failed_urls'):
            update_status(STATUS_COMPLETED) # Use callback
            jobs_dict[job_id]["processed_count"] = pipeline_results.get('processed_count', len(urls))
            # Store paths to generated files
            try:
                jobs_dict[job_id]["files"] = [f for f in os.listdir(job_output_dir) if os.path.isfile(os.path.join(job_output_dir, f)) and not f.startswith('.')]
            except FileNotFoundError:
                 logger.warning(f"Job {job_id}: Output directory {job_output_dir} not found when listing files.")
                 jobs_dict[job_id]["files"] = []
            logger.info(f"Job {job_id}: Completed successfully.")
        else:
            update_status(STATUS_FAILED) # Use callback, even for partial failures for simplicity
            jobs_dict[job_id]["error"] = f"Processing failed for URLs: {list(pipeline_results.get('failed_urls', {}).keys())}" # Store only URLs
            jobs_dict[job_id]["processed_count"] = pipeline_results.get('processed_count', 0)
            jobs_dict[job_id]["failed_urls"] = pipeline_results.get('failed_urls', {}) # Store full failure details if needed elsewhere
            # List any files that might have been created before failure
            try:
                jobs_dict[job_id]["files"] = [f for f in os.listdir(job_output_dir) if os.path.isfile(os.path.join(job_output_dir, f)) and not f.startswith('.')]
            except FileNotFoundError:
                 jobs_dict[job_id]["files"] = []
            logger.warning(f"Job {job_id}: Finished with failures: {pipeline_results['failed_urls']}")


def start_job(
    urls: List[str],
    config: Dict[str, Any],
    jobs_dict: Dict[str, Any] # Pass the shared jobs dictionary
) -> str:
    """
    Creates a job ID, initializes status, and starts the background thread.
    """
    job_id = str(uuid.uuid4())
    jobs_dict[job_id] = {
        "status": STATUS_PENDING,
        "submitted_at": time.time(),
        "original_urls": urls, # Store original URLs for retry
        "original_config": config, # Store original config for retry
        "output_dir": None, # Will be set when job runs
        "files": [],
        "error": None,
        "cancelled": False # Initialize cancellation flag
    }
    logger.info(f"Job {job_id} created and added to queue.")

    # Create and start the background thread
    thread = threading.Thread(
        target=run_transcription_job_in_background,
        args=(job_id, urls, config, jobs_dict),
        daemon=True # Allows main thread to exit even if background threads are running
    )
    thread.start()
    logger.info(f"Job {job_id}: Background thread started.")

    return job_id
