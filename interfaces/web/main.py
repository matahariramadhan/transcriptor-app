import os
import sys
import uuid
import logging
from fastapi import FastAPI, Request, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn

# Add project root to Python path to allow imports like `from core import ...`
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# Ensure project root is in path *before* importing from core or interfaces
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Import background processing function
from interfaces.web.processing import start_job

# --- Logging Setup ---
# Configure logging for the web interface
# Could potentially share config with CLI if desired
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TranscriptorApp.WebUI")


# --- FastAPI App Setup ---
app = FastAPI(title="TranscriptorApp Web UI")

# Mount static files directory
# Ensure the path is relative to this script's location
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Configure Jinja2 templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# --- In-memory Job Storage (Simple Placeholder) ---
# In a real app, this would be more robust (e.g., Redis, DB)
# Stores job status, config, results etc. Keyed by job_id.
jobs: Dict[str, Dict[str, Any]] = {}

# --- Job Status Constants ---
# Define constants for job statuses to avoid typos
STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing" # Generic processing, might be refined by callback
STATUS_DOWNLOADING = "downloading"
STATUS_TRANSCRIBING = "transcribing"
STATUS_FORMATTING = "formatting"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_CANCELLING = "cancelling"
STATUS_CANCELLED = "cancelled"


# --- Pydantic Models ---
class JobConfigRequest(BaseModel):
    model: str = "whisper-1"
    formats: List[str] = ["txt", "srt"]
    audio_format: str = "mp3"
    language: Optional[str] = None
    prompt: Optional[str] = None
    temperature: float = 0.0
    speaker_labels: bool = False
    keep_audio: bool = False
    # output_filename_template is not directly set by user in this simple UI,
    # but could be added as an advanced option. We'll use a default or derive it.

class JobSubmitRequest(BaseModel):
    urls: List[str]
    config: JobConfigRequest


# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/submit_job", status_code=202) # 202 Accepted for background tasks
async def submit_job_endpoint(
    job_request: JobSubmitRequest,
    background_tasks: BackgroundTasks # Inject background tasks handler
):
    """
    Accepts job submission, starts background processing, returns job ID.
    """
    if not job_request.urls:
        raise HTTPException(status_code=400, detail="No URLs provided.")

    logger.info(f"Received job submission for URLs: {job_request.urls}")
    logger.info(f"Job config: {job_request.config.model_dump()}")

    # Prepare config dictionary for the core pipeline
    pipeline_config = job_request.config.model_dump()
    # Add default filename template if not provided (or derive if needed)
    pipeline_config.setdefault("output_filename_template", "%(title)s [%(id)s]")

    # Start the job using the processing module function
    # Pass the shared 'jobs' dictionary
    job_id = start_job(
        urls=job_request.urls,
        config=pipeline_config,
        jobs_dict=jobs
    )

    logger.info(f"Job {job_id} submitted successfully.")
    return {"message": "Job submitted successfully", "job_id": job_id}


@app.get("/status/{job_id}")
async def get_job_status_endpoint(job_id: str):
    """Returns the current status and basic info of a job."""
    logger.debug(f"Status requested for job: {job_id}")
    job_info = jobs.get(job_id)
    if not job_info:
        logger.warning(f"Status request failed: Job {job_id} not found.")
        raise HTTPException(status_code=404, detail="Job not found")

    # Return essential status info needed for UI updates
    # Add progress later if implemented in processing.py
    response_data = {
        "job_id": job_id,
        "status": job_info.get("status", "unknown"),
        "error": job_info.get("error"), # Include error message if status is 'failed'
        # Add any other fields needed by updateJobCardUI that change frequently
    }
    logger.debug(f"Returning status for job {job_id}: {response_data}")
    return response_data


@app.get("/result/{job_id}")
async def get_job_result_endpoint(job_id: str):
    """Returns the final results (files, errors) of a completed or failed job."""
    logger.debug(f"Result requested for job: {job_id}")
    job_info = jobs.get(job_id)
    if not job_info:
         logger.warning(f"Result request failed: Job {job_id} not found.")
         raise HTTPException(status_code=404, detail="Job not found")

    status = job_info.get("status")
    if status not in ["completed", "failed"]:
        logger.warning(f"Result requested for job {job_id} which is not finished (status: {status}).")
        # Depending on desired behavior, could return current status or raise an error
        # Raising error might be clearer for the frontend logic fetching results
        raise HTTPException(status_code=400, detail=f"Job is still in progress (status: {status}).")

    # Return detailed results needed for download links and summary
    response_data = {
        "job_id": job_id,
        "status": status,
        "error": job_info.get("error"),
        "output_dir": job_info.get("output_dir"), # Needed for constructing download paths? Maybe not directly by frontend.
        "files": job_info.get("files", []), # List of generated filenames
        "processed_count": job_info.get("processed_count"),
        "failed_urls": job_info.get("failed_urls", []),
        # Add transcript preview text here if implementing preview
    }
    logger.debug(f"Returning result for job {job_id}: {response_data}")
    return response_data


@app.get("/download/{job_id}/{filename}")
async def download_file_endpoint(job_id: str, filename: str):
    """Allows downloading of generated transcript files."""
    job_info = jobs.get(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")

    output_dir = job_info.get("output_dir")
    if not output_dir:
         raise HTTPException(status_code=404, detail="Job output directory not found.")

    # Basic security check: prevent path traversal
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    file_path = os.path.join(output_dir, filename)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found.")

    # Check if filename is in the list of expected files for the job (optional but good)
    if filename not in job_info.get("files", []):
         logger.warning(f"Attempt to download file '{filename}' not listed in job {job_id} files.")
         # Decide whether to allow or deny - denying is safer.
         # raise HTTPException(status_code=403, detail="Access denied to this file.")

    logger.info(f"Serving file download: {file_path}")
    return FileResponse(path=file_path, filename=filename, media_type='application/octet-stream')


@app.post("/cancel/{job_id}", status_code=200)
async def cancel_job_endpoint(job_id: str):
    """Attempts to cancel a running job."""
    logger.info(f"Cancel requested for job: {job_id}")
    job_info = jobs.get(job_id)
    if not job_info:
        logger.warning(f"Cancel request failed: Job {job_id} not found.")
        raise HTTPException(status_code=404, detail="Job not found")

    current_status = job_info.get("status")
    # Define cancellable states
    cancellable_statuses = [
        STATUS_PENDING,
        STATUS_PROCESSING,
        STATUS_DOWNLOADING,
        STATUS_TRANSCRIBING,
        STATUS_FORMATTING,
    ]

    if current_status in cancellable_statuses:
        job_info["cancelled"] = True # Set the flag for the background task to check
        job_info["status"] = STATUS_CANCELLING # Update status immediately
        logger.info(f"Job {job_id} marked for cancellation.")
        return {"message": "Job cancellation requested."}
    elif current_status == STATUS_CANCELLING or current_status == STATUS_CANCELLED:
        logger.info(f"Job {job_id} is already cancelling or cancelled.")
        return {"message": "Job already cancelling or cancelled."}
    else:
        logger.warning(f"Job {job_id} cannot be cancelled in its current state: {current_status}")
        raise HTTPException(status_code=400, detail=f"Job cannot be cancelled in state: {current_status}")


@app.post("/retry/{job_id}", status_code=202)
async def retry_job_endpoint(job_id: str):
    """Retries a failed job by creating and submitting a new job with the original parameters."""
    logger.info(f"Retry requested for job: {job_id}")
    original_job_info = jobs.get(job_id)
    if not original_job_info:
        logger.warning(f"Retry request failed: Job {job_id} not found.")
        raise HTTPException(status_code=404, detail="Original job not found")

    if original_job_info.get("status") != STATUS_FAILED:
        logger.warning(f"Retry requested for job {job_id} which did not fail (status: {original_job_info.get('status')}).")
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried.")

    # Retrieve original parameters needed to start a new job
    original_urls = original_job_info.get("original_urls")
    original_config = original_job_info.get("original_config")

    if not original_urls or not original_config:
         logger.error(f"Cannot retry job {job_id}: Missing original URLs or config in stored job info.")
         raise HTTPException(status_code=500, detail="Cannot retry job: Internal data missing.")

    logger.info(f"Retrying job {job_id} with URLs: {original_urls}")
    logger.info(f"Retry config: {original_config}")

    # Start a *new* job using the processing module function
    # Pass the shared 'jobs' dictionary
    new_job_id = start_job(
        urls=original_urls,
        config=original_config,
        jobs_dict=jobs
    )

    logger.info(f"Retry of job {job_id} submitted as new job {new_job_id}.")
    # Return the ID of the *new* job
    return {"message": "Retry submitted as a new job.", "new_job_id": new_job_id}


# --- Run Server (for local development) ---
if __name__ == "__main__":
    # Get port from environment variable or default to 8000
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting TranscriptorApp Web UI on http://127.0.0.1:{port}")
    # Use uvicorn to run the app
    # host="0.0.0.0" makes it accessible on the network, use "127.0.0.1" for local only
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
