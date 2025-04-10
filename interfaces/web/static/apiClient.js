/**
 * apiClient.js
 * Handles communication with the backend FastAPI server.
 */

const API_BASE = ""; // Relative path for API calls

/**
 * Submits a new transcription job to the backend.
 * @param {object} jobRequest - The job details { urls: string[], config: object }
 * @returns {Promise<object>} - The response data containing the job_id.
 * @throws {Error} - Throws an error if the submission fails.
 */
export async function submitJob(jobRequest) {
  const response = await fetch(`${API_BASE}/submit_job`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(jobRequest),
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch (e) {
      // Ignore if response body is not JSON
    }
    throw new Error(`Error ${response.status}: ${errorDetail}`);
  }

  return await response.json(); // { message: string, job_id: string }
}

/**
 * Fetches the status of a specific job.
 * @param {string} jobId - The ID of the job to check.
 * @returns {Promise<object>} - The status data { job_id: string, status: string, error?: string }.
 * @throws {Error} - Throws an error if the fetch fails.
 */
export async function getJobStatus(jobId) {
  const response = await fetch(`${API_BASE}/status/${jobId}`);

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch (e) {
      // Ignore if response body is not JSON
    }
    // Propagate specific status codes like 404
    const error = new Error(`Error ${response.status}: ${errorDetail}`);
    error.status = response.status;
    throw error;
  }
  return await response.json();
}

/**
 * Fetches the final result of a completed or failed job.
 * @param {string} jobId - The ID of the job.
 * @returns {Promise<object>} - The result data including status, files, errors etc.
 * @throws {Error} - Throws an error if the fetch fails or job not finished.
 */
export async function getJobResult(jobId) {
  const response = await fetch(`${API_BASE}/result/${jobId}`);

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch (e) {
      // Ignore if response body is not JSON
    }
    const error = new Error(`Error ${response.status}: ${errorDetail}`);
    error.status = response.status;
    throw error;
  }
  return await response.json();
}

// Potential future function:
// export async function cancelJobRequest(jobId) { ... }
