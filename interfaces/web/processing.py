import os
import sys
import threading
import logging
import time
import uuid
from typing import Dict, Any, List

# Add project root to Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from core.pipeline import run_pipeline
from dotenv import load_dotenv

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
        if job_id in jobs_dict:
            logger.info(f"Job {job_id}: Status changing to '{new_status}'")
            jobs_dict[job_id]["status"] = new_status
            logger.debug(f"Job {job_id}: jobs_dict updated. Current status: {jobs_dict[job_id].get('status')}") # Added debug log
        else:
            logger.warning(f"Job {job_id}: Tried to update status to '{new_status}', but job not found in dict.")

    # Load API key within the thread (or ensure it's passed securely)
    load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))
    api_key = os.getenv("LEMONFOX_API_KEY")

    if not api_key:
        logger.error(f"Job {job_id}: LEMONFOX_API_KEY not found for background thread.")
        jobs_dict[job_id] = {"status": "failed", "error": "API key not configured."}
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

        # --- Run the Core Pipeline ---
        # Pass the status update callback
        # Note: The core pipeline logs progress internally
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
        update_status("failed") # Use callback to set status
        jobs_dict[job_id]["error"] = f"An unexpected error occurred: {str(e)}"
    else:
        # --- Update Final Job Status Based on Results (if pipeline didn't crash) ---
        if not pipeline_results.get('failed_urls'):
            update_status("completed") # Use callback
            jobs_dict[job_id]["processed_count"] = pipeline_results.get('processed_count', len(urls))
            # Store paths to generated files
            try:
                jobs_dict[job_id]["files"] = [f for f in os.listdir(job_output_dir) if os.path.isfile(os.path.join(job_output_dir, f)) and not f.startswith('.')]
            except FileNotFoundError:
                 logger.warning(f"Job {job_id}: Output directory {job_output_dir} not found when listing files.")
                 jobs_dict[job_id]["files"] = []
            logger.info(f"Job {job_id}: Completed successfully.")
        else:
            update_status("failed") # Use callback, even for partial failures for simplicity
            jobs_dict[job_id]["error"] = f"Processing failed for URLs: {pipeline_results['failed_urls']}"
            jobs_dict[job_id]["processed_count"] = pipeline_results.get('processed_count', 0)
            jobs_dict[job_id]["failed_urls"] = pipeline_results.get('failed_urls', [])
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
        "status": "pending",
        "submitted_at": time.time(),
        "urls": urls,
        "config": config,
        "output_dir": None, # Will be set when job runs
        "files": [],
        "error": None
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
