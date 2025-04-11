/**
 * jobManager.js
 * Handles adding jobs to the UI, polling status, and updating job cards.
 */

import {
  getJobStatus,
  getJobResult,
  cancelJob,
  retryJob,
} from "./apiClient.js"; // Import new functions
// Potentially import UI update functions if we further modularize updateJobCardUI
// import { showModal } from './uiInteractions.js'; // If needed for error display

// --- State and DOM References ---
const activeJobs = {}; // Store job data and interval IDs: { job_id: { intervalId: null, status: 'pending', element: null } }
const jobsListContainer = document.querySelector(".space-y-5"); // Container for job cards

// --- Constants for Statuses (align with backend) ---
const STATUS_PENDING = "pending";
const STATUS_PROCESSING = "processing"; // Generic processing, might be refined by callback
const STATUS_DOWNLOADING = "downloading";
const STATUS_TRANSCRIBING = "transcribing";
const STATUS_FORMATTING = "formatting";
const STATUS_COMPLETED = "completed";
const STATUS_FAILED = "failed";
const STATUS_CANCELLING = "cancelling";
const STATUS_CANCELLED = "cancelled";
const STATUS_ERROR = "error"; // Frontend specific error status

// --- Exported Functions ---

export function addJobToUI(jobId, url) {
  if (!jobsListContainer) {
    console.error("Jobs list container not found!");
    return;
  }
  const jobCardHTML = createJobCardHTML(jobId, url);
  // Insert at the top of the list
  jobsListContainer.insertAdjacentHTML("afterbegin", jobCardHTML);
  const jobElement = jobsListContainer.querySelector(
    `[data-job-id="${jobId}"]`
  );
  activeJobs[jobId] = {
    intervalId: null,
    status: "pending",
    element: jobElement,
  };

  // Event listeners are now handled by delegation (see setupEventListeners below)
}

export function startPollingJobStatus(jobId) {
  if (activeJobs[jobId] && activeJobs[jobId].intervalId === null) {
    console.log(`Starting polling for job ${jobId}`);
    activeJobs[jobId].intervalId = setInterval(() => {
      updateJobStatus(jobId);
    }, 1000); // Poll every 1 second
    // Initial immediate check
    updateJobStatus(jobId);
  }
}

// --- Internal Helper Functions ---

function createJobCardHTML(jobId, url) {
  // Basic initial card structure. Will be updated by polling.
  const truncatedUrl = url.length > 60 ? url.substring(0, 57) + "..." : url;
  let title = `Job ${jobId.substring(0, 6)}`;
  try {
    const urlObj = new URL(url);
    if (
      urlObj.hostname.includes("youtube.com") &&
      urlObj.searchParams.has("v")
    ) {
      title = `YouTube Video (${urlObj.searchParams.get("v")})`;
    } else if (urlObj.hostname.includes("tiktok.com")) {
      const pathParts = urlObj.pathname.split("/");
      const videoId =
        pathParts[pathParts.length - 1] || pathParts[pathParts.length - 2];
      if (videoId) title = `TikTok Video (${videoId})`;
    }
  } catch (e) {
    console.warn("Could not parse URL for title:", url);
  }

  return `
    <div class="card bg-white rounded-xl shadow-sm p-6 border-l-4 border-gray-400" data-job-id="${jobId}">
      <div class="flex justify-between items-start mb-4">
        <div>
          <div class="flex items-center mb-1">
            <span class="status-indicator bg-gray-400"></span>
            <h3 class="font-medium text-gray-800 job-title">${title}</h3>
          </div>
          <p class="text-sm text-gray-500 truncate max-w-2xl job-url">${truncatedUrl}</p>
        </div>
        <div class="flex space-x-2 job-actions">
          <button class="text-red-500 hover:text-red-700 p-1 transition job-cancel-button hidden" title="Cancel" data-job-id="${jobId}">
            <i class="fas fa-times"></i>
          </button>
           <button class="text-blue-500 hover:text-blue-700 p-1 transition job-retry-button hidden" title="Retry" data-job-id="${jobId}">
            <i class="fas fa-redo"></i>
          </button>
        </div>
      </div>
      <div class="mb-3 job-status-section">
        <div class="flex justify-between mb-2">
          <span class="text-sm font-medium text-gray-700 job-status-text">Pending...</span>
          <span class="text-sm text-gray-500 job-progress-percentage"></span>
        </div>
        <div class="w-full bg-gray-100 rounded-full h-2.5 job-progress-bar-bg">
          <div class="progress-bar bg-gray-400 h-2.5 rounded-full job-progress-bar" style="width: 0%"></div>
        </div>
      </div>
      <div class="flex items-center text-xs text-gray-500 bg-gray-50 p-2 rounded job-details-section hidden">
        <i class="fas fa-info-circle mr-2"></i>
        <span class="job-details-text"></span>
      </div>
       <div class="text-xs text-red-500 bg-red-50 p-3 rounded job-error-section hidden">
          Error: <span class="job-error-text"></span>
       </div>
       <div class="flex justify-end items-center mb-3 job-results-section hidden">
           <!-- Buttons for completed jobs -->
           <div class="flex space-x-3">
                <button class="text-sm px-4 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center space-x-1.5 transition text-gray-700 job-preview-button">
                    <i class="fas fa-eye"></i>
                    <span>Preview</span>
                </button>
                <div class="relative group job-download-group">
                    <button class="text-sm px-4 py-1.5 bg-primary-100 hover:bg-primary-200 text-primary-700 rounded-lg flex items-center space-x-1.5 transition">
                        <i class="fas fa-download"></i>
                        <span>Download</span>
                    </button>
                    <div class="absolute right-0 bottom-full mb-2 bg-white rounded-lg shadow-lg py-2 z-10 hidden group-hover:block w-40 border border-gray-100 job-download-options">
                        <!-- Download links added dynamically -->
                    </div>
                </div>
            </div>
       </div>
    </div>
  `;
}

async function updateJobStatus(jobId) {
  if (!activeJobs[jobId]) return; // Job might have been cancelled

  try {
    // Use apiClient.getJobStatus
    const data = await getJobStatus(jobId);
    activeJobs[jobId].status = data.status;
    updateJobCardUI(jobId, data); // Update the UI with the new status

    // Stop polling if job is completed or failed
    if (data.status === "completed" || data.status === "failed") {
      stopPollingJobStatus(jobId);
      if (data.status === "completed") {
        fetchAndPopulateResults(jobId); // Fetch full results for completed job
      }
    }
  } catch (error) {
    console.error(`Error polling status for job ${jobId}:`, error);
    // Optionally stop polling on specific errors
    if (error.status === 404) {
      // Job not found on server (maybe deleted or never existed)
      console.warn(
        `Job ${jobId} not found on server during polling. Stopping polling.`
      );
      stopPollingJobStatus(jobId);
      updateJobCardUI(jobId, {
        status: STATUS_ERROR,
        error: "Job not found on server.",
      });
    } else {
      // Handle other errors (e.g., temporary network issue) - maybe just log and continue polling for a bit
      console.error(
        `Network or other error polling status for job ${jobId}:`,
        error
      );
    }
  }
}

function updateJobCardUI(jobId, data) {
  const jobElement = activeJobs[jobId]?.element;
  if (!jobElement) return;

  const statusTextElement = jobElement.querySelector(".job-status-text");
  const progressBarElement = jobElement.querySelector(".job-progress-bar");
  const statusIndicator = jobElement.querySelector(".status-indicator");
  const cardElement = jobElement; // The main card div
  const errorSection = jobElement.querySelector(".job-error-section");
  const errorText = jobElement.querySelector(".job-error-text");
  const resultsSection = jobElement.querySelector(".job-results-section");
  const statusSection = jobElement.querySelector(".job-status-section");
  const detailsSection = jobElement.querySelector(".job-details-section");
  const detailsText = jobElement.querySelector(".job-details-text");
  const cancelButton = jobElement.querySelector(".job-cancel-button");
  const retryButton = jobElement.querySelector(".job-retry-button");

  // Reset sections and buttons
  errorSection.classList.add("hidden");
  resultsSection.classList.add("hidden");
  statusSection.classList.remove("hidden"); // Show status section by default
  cancelButton?.classList.add("hidden");
  retryButton?.classList.add("hidden");

  let statusText = data.status || "Unknown";
  let statusColorClass = "border-gray-400"; // Default border
  let indicatorColorClass = "bg-gray-400"; // Default indicator
  let progressWidth = "0%"; // Default progress
  let showCancel = false;
  let showRetry = false;

  switch (data.status) {
    case STATUS_PENDING:
      statusText = "Pending...";
      showCancel = true;
      break;
    case STATUS_DOWNLOADING:
      statusText = "Downloading...";
      statusColorClass = "border-secondary-400";
      indicatorColorClass = "bg-secondary-400";
      progressWidth = "25%"; // Example progress
      showCancel = true;
      break;
    case STATUS_TRANSCRIBING:
      statusText = "Transcribing...";
      statusColorClass = "border-primary-500";
      indicatorColorClass = "bg-primary-500";
      progressWidth = "60%"; // Example progress
      showCancel = true;
      break;
    case STATUS_FORMATTING:
      statusText = "Formatting...";
      statusColorClass = "border-yellow-500";
      indicatorColorClass = "bg-yellow-500";
      progressWidth = "90%"; // Example progress
      showCancel = true;
      break;
    case STATUS_CANCELLING:
      statusText = "Cancelling...";
      statusColorClass = "border-red-400"; // Use a slightly different red
      indicatorColorClass = "bg-red-400";
      progressWidth = progressBarElement?.style.width || "0%"; // Keep current progress
      // Keep cancel button visible but maybe disable it? Or hide? Let's hide.
      showCancel = false;
      break;
    case STATUS_CANCELLED:
      statusText = "Cancelled";
      statusColorClass = "border-red-500";
      indicatorColorClass = "bg-red-500";
      progressWidth = progressBarElement?.style.width || "0%"; // Keep progress where it stopped
      statusSection.classList.remove("hidden"); // Keep status section visible
      errorSection.classList.add("hidden"); // Hide error section
      resultsSection.classList.add("hidden"); // Hide results
      break;
    case STATUS_COMPLETED:
      statusText = "Completed";
      statusColorClass = "border-green-500";
      indicatorColorClass = "bg-green-500";
      progressWidth = "100%";
      statusSection.classList.add("hidden"); // Hide progress bar section
      resultsSection.classList.remove("hidden"); // Show results buttons
      break;
    case STATUS_FAILED:
      statusText = "Failed";
      statusColorClass = "border-red-500";
      indicatorColorClass = "bg-red-500";
      progressWidth = "100%"; // Show full bar in red maybe? Or hide.
      statusSection.classList.add("hidden"); // Hide progress bar section
      errorSection.classList.remove("hidden");
      errorText.textContent = data.error || "An unknown error occurred.";
      showRetry = true; // Show retry button on failure
      break;
    case STATUS_ERROR: // Frontend specific error
      statusText = "Error";
      statusColorClass = "border-red-500";
      indicatorColorClass = "bg-red-500";
      statusSection.classList.add("hidden");
      errorSection.classList.remove("hidden");
      errorText.textContent = data.error || "An internal UI error occurred.";
      break;
    default:
      statusText = data.status; // Display unknown status directly
      statusColorClass = "border-gray-500";
      indicatorColorClass = "bg-gray-500";
  }

  // Update UI elements
  if (statusTextElement) statusTextElement.textContent = statusText;
  if (progressBarElement) progressBarElement.style.width = progressWidth;
  if (progressBarElement)
    progressBarElement.className = `progress-bar h-2.5 rounded-full job-progress-bar ${indicatorColorClass}`; // Update bar color too
  if (statusIndicator)
    statusIndicator.className = `status-indicator w-3 h-3 rounded-full mr-2 ${indicatorColorClass}`; // Ensure size/shape
  if (cardElement)
    cardElement.className = `card bg-white rounded-xl shadow-sm p-6 border-l-4 ${statusColorClass}`; // Update border color

  // Show/Hide Action Buttons
  if (cancelButton) {
    if (showCancel) {
      cancelButton.classList.remove("hidden");
    } else {
      cancelButton.classList.add("hidden");
    }
  }
  if (retryButton) {
    if (showRetry) {
      retryButton.classList.remove("hidden");
    } else {
      retryButton.classList.add("hidden");
    }
  }

  // Update details section if job is completed (can be expanded)
  if (data.status === STATUS_COMPLETED && detailsSection && detailsText) {
    detailsText.textContent = `Processed ${
      data.processed_count || "?"
    } URL(s).`; // Example detail
    detailsSection.classList.remove("hidden");
  } else if (detailsSection) {
    detailsSection.classList.add("hidden");
  }
}

async function fetchAndPopulateResults(jobId) {
  const jobElement = activeJobs[jobId]?.element;
  if (!jobElement) return;

  try {
    // Use apiClient.getJobResult
    const resultData = await getJobResult(jobId);

    // Populate download links
    const downloadOptionsContainer = jobElement.querySelector(
      ".job-download-options"
    );
    if (downloadOptionsContainer) {
      downloadOptionsContainer.innerHTML = ""; // Clear existing
      resultData.files?.forEach((filename) => {
        const link = document.createElement("a");
        link.href = `/download/${jobId}/${filename}`;
        link.className = "block px-4 py-2 hover:bg-gray-50 text-sm transition";
        link.textContent = `Download ${filename
          .split(".")
          .pop()
          .toUpperCase()}`;
        link.download = filename; // Suggest filename to browser
        downloadOptionsContainer.appendChild(link);
      });
      // Add audio download link if keep_audio was true and file exists? (Needs more info from backend)
    }

    // Add preview button functionality (if needed)
    const previewButton = jobElement.querySelector(".job-preview-button");
    if (previewButton) {
      previewButton.onclick = () => {
        // TODO: Implement preview logic (e.g., fetch text content and display in modal or results section)
        alert(`Preview for job ${jobId} - Not implemented yet.`);
      };
    }

    // Update details section with more info
    const detailsText = jobElement.querySelector(".job-details-text");
    if (detailsText) {
      detailsText.textContent = `Completed ${
        resultData.processed_count || "?"
      } URL(s). ${resultData.files?.length || 0} files generated.`;
    }
  } catch (error) {
    console.error(`Error fetching results for job ${jobId}:`, error);
    updateJobCardUI(jobId, {
      status: STATUS_ERROR,
      error: "Failed to fetch results.",
    });
  }
}

function stopPollingJobStatus(jobId) {
  if (activeJobs[jobId] && activeJobs[jobId].intervalId !== null) {
    console.log(`Stopping polling for job ${jobId}`);
    clearInterval(activeJobs[jobId].intervalId);
    activeJobs[jobId].intervalId = null;
  }
}

// --- Event Handlers ---

async function handleCancelClick(jobId) {
  console.log(`Requesting cancellation for job ${jobId}`);
  const jobElement = activeJobs[jobId]?.element;
  const cancelButton = jobElement?.querySelector(".job-cancel-button");

  if (cancelButton) cancelButton.disabled = true; // Disable button immediately

  try {
    const result = await cancelJob(jobId); // Use apiClient function
    console.log(
      `Cancellation request for ${jobId} successful:`,
      result.message
    );
    // Update UI immediately to 'Cancelling' - polling will eventually confirm 'Cancelled'
    updateJobCardUI(jobId, { status: STATUS_CANCELLING });
  } catch (error) {
    console.error(`Error cancelling job ${jobId}:`, error);
    alert(`Failed to cancel job ${jobId}: ${error.message}`); // Simple error feedback
    if (cancelButton) cancelButton.disabled = false; // Re-enable button on error
  }
}

async function handleRetryClick(jobId) {
  console.log(`Requesting retry for job ${jobId}`);
  const jobElement = activeJobs[jobId]?.element;
  const retryButton = jobElement?.querySelector(".job-retry-button");

  if (retryButton) retryButton.disabled = true; // Disable button immediately

  try {
    const result = await retryJob(jobId); // Use apiClient function
    console.log(
      `Retry request for ${jobId} successful. New job ID: ${result.new_job_id}`
    );
    alert(`Job ${jobId} submitted for retry as new job ${result.new_job_id}.`); // Simple feedback

    // Visually update the old failed card
    if (jobElement) {
      const statusTextElement = jobElement.querySelector(".job-status-text");
      if (statusTextElement) statusTextElement.textContent = "Retried";
      jobElement.style.opacity = "0.6"; // Grey out slightly
      retryButton?.classList.add("hidden"); // Hide retry button
    }
    stopPollingJobStatus(jobId); // Stop polling the old failed job

    // Add the new job to the UI and start polling it
    // Note: This assumes the backend immediately adds the new job to the 'jobs' dict
    // A small delay might mean polling picks it up anyway. Let's explicitly add it.
    // We need the URL for the new card - fetch it from the old job's data if stored,
    // otherwise, we might need the backend retry endpoint to return more info,
    // or just show a generic title for the new job initially.
    // For now, let's rely on polling to pick up the new job.
  } catch (error) {
    console.error(`Error retrying job ${jobId}:`, error);
    alert(`Failed to retry job ${jobId}: ${error.message}`); // Simple error feedback
    if (retryButton) retryButton.disabled = false; // Re-enable button on error
  }
}

// --- Event Listener Setup ---

function setupEventListeners() {
  if (!jobsListContainer) return;

  jobsListContainer.addEventListener("click", (event) => {
    const cancelButton = event.target.closest(".job-cancel-button");
    const retryButton = event.target.closest(".job-retry-button");

    if (cancelButton) {
      const jobId = cancelButton.dataset.jobId;
      if (jobId) {
        handleCancelClick(jobId);
      }
    } else if (retryButton) {
      const jobId = retryButton.dataset.jobId;
      if (jobId) {
        handleRetryClick(jobId);
      }
    }
  });
}

// Initialize event listeners when the script loads
setupEventListeners();
