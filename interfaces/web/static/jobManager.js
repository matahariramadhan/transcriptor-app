/**
 * jobManager.js
 * Handles adding jobs to the UI, polling status, and updating job cards.
 */

import { getJobStatus, getJobResult } from "./apiClient.js";
// Potentially import UI update functions if we further modularize updateJobCardUI
// import { showModal } from './uiInteractions.js'; // If needed for error display

// --- State and DOM References ---
const activeJobs = {}; // Store job data and interval IDs: { job_id: { intervalId: null, status: 'pending', element: null } }
const jobsListContainer = document.querySelector(".space-y-5"); // Container for job cards

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

  // Add event listener for the cancel button on the new card
  const cancelButton = jobElement.querySelector(".job-cancel-button");
  if (cancelButton) {
    cancelButton.addEventListener("click", () => cancelJob(jobId));
  }
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
        <div class="flex space-x-2">
          <button class="text-red-500 hover:text-red-700 p-1 transition job-cancel-button" title="Cancel">
            <i class="fas fa-times"></i>
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
    // Optionally stop polling on network errors
    if (error.status === 404) {
      // Check specific error status if needed
      stopPollingJobStatus(jobId);
      updateJobCardUI(jobId, {
        status: "error",
        error: "Job not found on server.",
      });
    } else {
      // Handle other errors (e.g., temporary network issue) - maybe retry or just log
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

  // Reset sections
  errorSection.classList.add("hidden");
  resultsSection.classList.add("hidden");
  statusSection.classList.remove("hidden"); // Show status section by default

  let statusText = data.status || "Unknown";
  let statusColorClass = "border-gray-400"; // Default border
  let indicatorColorClass = "bg-gray-400"; // Default indicator
  let progressWidth = "0%"; // Default progress

  switch (data.status) {
    case "pending":
      statusText = "Pending...";
      break;
    case "downloading":
      statusText = "Downloading...";
      statusColorClass = "border-secondary-400";
      indicatorColorClass = "bg-secondary-400";
      progressWidth = "25%"; // Example progress
      break;
    case "transcribing":
      statusText = "Transcribing...";
      statusColorClass = "border-primary-500";
      indicatorColorClass = "bg-primary-500";
      progressWidth = "60%"; // Example progress
      break;
    case "formatting":
      statusText = "Formatting...";
      statusColorClass = "border-yellow-500";
      indicatorColorClass = "bg-yellow-500";
      progressWidth = "90%"; // Example progress
      break;
    case "completed":
      statusText = "Completed";
      statusColorClass = "border-green-500";
      indicatorColorClass = "bg-green-500";
      progressWidth = "100%";
      statusSection.classList.add("hidden"); // Hide progress bar section
      resultsSection.classList.remove("hidden"); // Show results buttons
      break;
    case "failed":
      statusText = "Failed";
      statusColorClass = "border-red-500";
      indicatorColorClass = "bg-red-500";
      progressWidth = "100%"; // Show full bar in red maybe? Or hide.
      statusSection.classList.add("hidden"); // Hide progress bar section
      errorSection.classList.remove("hidden");
      errorText.textContent = data.error || "An unknown error occurred.";
      break;
    default:
      statusText = data.status; // Display unknown status directly
  }

  if (statusTextElement) statusTextElement.textContent = statusText;
  if (progressBarElement) progressBarElement.style.width = progressWidth;
  if (progressBarElement)
    progressBarElement.className = `progress-bar h-2.5 rounded-full job-progress-bar ${indicatorColorClass}`; // Update bar color too
  if (statusIndicator)
    statusIndicator.className = `status-indicator ${indicatorColorClass}`;
  if (cardElement)
    cardElement.className = `card bg-white rounded-xl shadow-sm p-6 border-l-4 ${statusColorClass}`; // Update border color

  // Update details section if job is completed (can be expanded)
  if (data.status === "completed" && detailsSection && detailsText) {
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
    console.error(`Error processing results for job ${jobId}:`, error);
    updateJobCardUI(jobId, {
      status: "error",
      error: "Error processing results.",
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

function cancelJob(jobId) {
  // TODO: Implement API call to backend to request cancellation
  console.log(`Requesting cancellation for job ${jobId} (Not implemented)`);
  // For now, just remove from UI and stop polling
  const jobElement = activeJobs[jobId]?.element;
  if (jobElement) {
    jobElement.remove();
  }
  stopPollingJobStatus(jobId);
  delete activeJobs[jobId];
}
