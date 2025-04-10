// Advanced Options Toggle
const advancedToggle = document.getElementById("advanced-toggle");
const advancedOptions = document.getElementById("advanced-options");

advancedToggle.addEventListener("click", function () {
  advancedOptions.classList.toggle("hidden");

  // Toggle chevron icon
  const chevron = advancedToggle.querySelector(".fa-chevron-down");
  if (chevron.classList.contains("fa-chevron-down")) {
    chevron.classList.replace("fa-chevron-down", "fa-chevron-up");
  } else {
    chevron.classList.replace("fa-chevron-up", "fa-chevron-down");
  }
});

// Keep Audio Checkbox
const keepAudioCheckbox = document.getElementById("keep-audio-checkbox");
const audioFormatContainer = document.getElementById("audio-format-container");

keepAudioCheckbox.addEventListener("change", function () {
  if (this.checked) {
    audioFormatContainer.classList.remove("hidden");
  } else {
    audioFormatContainer.classList.add("hidden");
  }
});

// URL Input Management
const addUrlButton = document.querySelector(
  'button[class*="text-secondary-600"]'
);
const urlInputContainer = document.querySelector(".url-input-container");

addUrlButton.addEventListener("click", function () {
  const newUrlInput = document.createElement("div");
  newUrlInput.className = "flex items-start space-x-2";
  newUrlInput.innerHTML = `
                            <div class="flex-grow">
                              <div class="relative">
                                <input
                                  type="text"
                                  placeholder="Enter URL (YouTube, TikTok, Instagram, etc.)"
                                  class="input-field w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none text-gray-700"
                                />
                                <button
                                  class="absolute right-3 top-3 text-gray-400 hover:text-secondary-500 transition"
                                  title="Paste from clipboard"
                                >
                                  <i class="far fa-clipboard"></i>
                                </button>
                              </div>
                            </div>
                            <button class="text-red-500 hover:text-red-700 pt-3 transition remove-url">
                              <i class="fas fa-times"></i>
                            </button>
                          `;
  urlInputContainer.appendChild(newUrlInput);

  // Add event listener to new remove button
  newUrlInput
    .querySelector(".remove-url")
    .addEventListener("click", function () {
      urlInputContainer.removeChild(newUrlInput);
    });
});

// Add event listener to existing remove button
document
  .querySelector(".url-input-container .text-red-500")
  .addEventListener("click", function () {
    const input = this.closest(".flex").querySelector("input");
    input.value = "";
  });

// Clipboard paste functionality
document.querySelectorAll(".far.fa-clipboard").forEach((button) => {
  button.parentElement.addEventListener("click", async function () {
    try {
      const text = await navigator.clipboard.readText();
      this.closest(".relative").querySelector("input").value = text;
    } catch (err) {
      console.error("Failed to read clipboard: ", err);
    }
  });
});

// Modal functionality
const modal = document.getElementById("modal");
const closeModal = document.getElementById("close-modal");
const modalCancel = document.getElementById("modal-cancel");

function showModal(title, content, confirmAction) {
  document.getElementById("modal-title").textContent = title;
  document.getElementById("modal-content").innerHTML = content;

  const confirmButton = document.getElementById("modal-confirm");
  confirmButton.onclick = confirmAction;

  modal.classList.remove("hidden");
}

function hideModal() {
  modal.classList.add("hidden");
}

closeModal.addEventListener("click", hideModal);
modalCancel.addEventListener("click", hideModal);

// Example usage of modal
document.querySelectorAll('button[title="Details"]').forEach((button) => {
  button.addEventListener("click", function () {
    const errorDetails =
      "Error Code: 403 - This video is private or requires authentication. Please check if the video is publicly accessible or if you have the correct permissions to access it.";

    showModal(
      "Error Details",
      `<p class="text-red-500">${errorDetails}</p>`,
      function () {
        hideModal();
      }
    );
  });
});

// Preview functionality - toggle results section
document.querySelectorAll("button:has(.fa-eye)").forEach((button) => {
  button.addEventListener("click", function () {
    const resultsSection = document.getElementById("results-section");
    resultsSection.classList.remove("hidden");

    // Scroll to results section
    resultsSection.scrollIntoView({ behavior: "smooth" });
  });
});

// Close preview button
const closePreviewButtons = document.querySelectorAll(
  "#results-section .text-gray-700:has(.fa-times)"
);
closePreviewButtons.forEach((button) => {
  button.addEventListener("click", function () {
    document.getElementById("results-section").classList.add("hidden");
  });
});

// --- Job Submission ---
const startButton = document.querySelector("button:has(.fa-play)");
// const urlInputContainer = document.querySelector(".url-input-container"); // Already declared above
const jobsListContainer = document.querySelector(".space-y-5"); // Container for job cards

// Helper to get selected checkbox values
function getSelectedCheckboxes(name) {
  return Array.from(
    document.querySelectorAll(`input[name="${name}"]:checked`)
  ).map((cb) => cb.value);
}

// Helper to add a new job card to the UI
function addJobCard(jobId, urls) {
  const card = document.createElement("div");
  card.className =
    "job-card card bg-white rounded-xl shadow-sm p-6 border-l-4 border-gray-400"; // Initial pending style
  card.dataset.jobId = jobId; // Store job ID on the element

  // Truncate URL for display if needed
  const displayUrl =
    urls[0].length > 60 ? urls[0].substring(0, 57) + "..." : urls[0];
  const urlCount = urls.length > 1 ? ` (+${urls.length - 1} more)` : "";

  card.innerHTML = `
        <div class="flex justify-between items-start mb-4">
            <div>
                <div class="flex items-center mb-1">
                    <span class="status-indicator bg-gray-400"></span>
                    <h3 class="job-title font-medium text-gray-800">Processing Job ${jobId.substring(
                      0,
                      8
                    )}...</h3>
                </div>
                <p class="job-url text-sm text-gray-500 truncate max-w-2xl" title="${urls.join(
                  ", "
                )}">${displayUrl}${urlCount}</p>
            </div>
            <div class="flex space-x-2">
                <button class="text-red-500 hover:text-red-700 p-1 transition" title="Cancel">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
        <div class="job-status-details mb-3">
            <div class="flex justify-between mb-2">
                <span class="job-status-text text-sm font-medium text-gray-700">Status: Pending...</span>
                <span class="job-progress-percentage text-sm text-gray-500">0%</span>
            </div>
            <div class="w-full bg-gray-100 rounded-full h-2.5">
                <div class="job-progress-bar progress-bar bg-gray-400 h-2.5 rounded-full" style="width: 0%"></div>
            </div>
        </div>
        <div class="job-config-info flex items-center text-xs text-gray-500 bg-gray-50 p-2 rounded">
            <i class="fas fa-info-circle mr-2"></i>
            <span>Loading config...</span>
        </div>
        <div class="job-results hidden mt-3"> <!-- Section for results/downloads -->
        </div>
        <div class="job-error hidden mt-3 text-xs text-red-500 bg-red-50 p-3 rounded">
            <!-- Error message goes here -->
        </div>
    `;
  // Prepend new job to the top of the list
  jobsListContainer.prepend(card);
  return card;
}

startButton.addEventListener("click", async function () {
  // 1. Collect URLs
  const urlInputs = urlInputContainer.querySelectorAll('input[type="text"]');
  const urls = Array.from(urlInputs)
    .map((input) => input.value.trim())
    .filter((url) => url); // Get non-empty URLs

  if (urls.length === 0) {
    alert("Please enter at least one URL.");
    return;
  }

  // 2. Collect Config Options
  const model = document.querySelector('select[class*="input-field"]').value; // Assuming first select is model
  const formats = getSelectedCheckboxes("output_format"); // Need to add name="output_format" to checkboxes in HTML
  const languageSelect = document.querySelector("#advanced-options select"); // Assuming first select in advanced is language
  const language = languageSelect.value || null; // Use null if auto-detect
  const speaker_labels = document.getElementById(
    "speaker-labels-checkbox"
  ).checked;
  const keep_audio = document.getElementById("keep-audio-checkbox").checked;
  const audio_format = keep_audio
    ? document.querySelector("#audio-format-container select").value
    : "mp3"; // Get format if keep_audio is checked

  const jobConfig = {
    model: model,
    formats: formats,
    audio_format: audio_format,
    language: language,
    // prompt: promptValue, // Add if prompt input exists
    // temperature: tempValue, // Add if temperature input exists
    speaker_labels: speaker_labels,
    keep_audio: keep_audio,
  };

  const jobData = {
    urls: urls,
    config: jobConfig,
  };

  // 3. Submit Job to Backend
  try {
    startButton.disabled = true; // Prevent double-clicks
    startButton.textContent = "Submitting...";

    const response = await fetch("/submit_job", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(jobData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(
        errorData.detail || `HTTP error! status: ${response.status}`
      );
    }

    const result = await response.json();
    const jobId = result.job_id;
    console.log("Job submitted successfully:", jobId);

    // 4. Add Job Card to UI
    const jobCard = addJobCard(jobId, urls);
    // Update config display in the card
    const configInfoSpan = jobCard.querySelector(".job-config-info span");
    configInfoSpan.textContent = `${jobConfig.model} • ${jobConfig.formats.join(
      ", "
    )} ${jobConfig.speaker_labels ? "• Speaker Labels" : ""} ${
      jobConfig.keep_audio ? `• Keep ${jobConfig.audio_format}` : ""
    }`;

    // 5. Start Polling for this job (implementation below)
    startPollingJobStatus(jobId);

    // Optional: Clear the form after submission?
    // clearButton.click();
  } catch (error) {
    console.error("Error submitting job:", error);
    alert(`Failed to submit job: ${error.message}`);
  } finally {
    startButton.disabled = false;
    startButton.innerHTML =
      '<i class="fas fa-play"></i> <span>Start Transcription</span>'; // Restore button text/icon
  }
});

// --- Job Status Polling ---
const activePolls = {}; // Keep track of active polling intervals

function updateJobCardUI(jobId, data) {
  const jobCard = jobsListContainer.querySelector(
    `.job-card[data-job-id="${jobId}"]`
  );
  if (!jobCard) return; // Card might have been removed

  const statusText = jobCard.querySelector(".job-status-text");
  const progressBar = jobCard.querySelector(".job-progress-bar");
  const progressPercentage = jobCard.querySelector(".job-progress-percentage");
  const statusIndicator = jobCard.querySelector(".status-indicator");
  const resultsContainer = jobCard.querySelector(".job-results");
  const errorContainer = jobCard.querySelector(".job-error");

  // Update status text
  statusText.textContent = `Status: ${data.status || "Unknown"}`;

  // Update progress bar and percentage (simple mapping for now)
  let progress = 0;
  let barColor = "bg-gray-400"; // Default pending/unknown
  let indicatorColor = "bg-gray-400";

  switch (data.status) {
    case "pending":
      progress = 5;
      break;
    case "processing": // Could be downloading or transcribing
      progress = 30; // Placeholder progress
      barColor = "bg-secondary-400";
      indicatorColor = "bg-secondary-400";
      break;
    // TODO: Add more granular statuses if backend provides them (downloading, transcribing, formatting)
    case "completed":
      progress = 100;
      barColor = "bg-green-500";
      indicatorColor = "bg-green-500";
      // Fetch and display results
      fetchAndDisplayResults(jobId, jobCard);
      // Stop polling for this job
      stopPollingJobStatus(jobId);
      break;
    case "failed":
      progress = 100; // Show full bar but red
      barColor = "bg-red-500";
      indicatorColor = "bg-red-500";
      // Display error
      errorContainer.textContent = `Error: ${data.error || "Unknown error"}`;
      errorContainer.classList.remove("hidden");
      resultsContainer.classList.add("hidden"); // Hide results section on failure
      // Stop polling for this job
      stopPollingJobStatus(jobId);
      break;
    default: // not_found or unknown
      progress = 0;
      barColor = "bg-gray-400";
      indicatorColor = "bg-gray-400";
      errorContainer.textContent = `Error: Job status unknown or not found.`;
      errorContainer.classList.remove("hidden");
      stopPollingJobStatus(jobId); // Stop polling if job not found
      break;
  }

  progressBar.style.width = `${progress}%`;
  progressBar.className = `job-progress-bar progress-bar h-2.5 rounded-full ${barColor}`; // Update color class
  statusIndicator.className = `status-indicator ${indicatorColor}`;
  progressPercentage.textContent = `${progress}%`;
}

async function fetchJobStatus(jobId) {
  try {
    const response = await fetch(`/status/${jobId}`);
    if (!response.ok) {
      if (response.status === 404) {
        console.warn(`Job ${jobId} not found.`);
        updateJobCardUI(jobId, {
          status: "not_found",
          error: "Job not found on server.",
        });
      } else {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return; // Don't continue if fetch failed
    }
    const data = await response.json();
    updateJobCardUI(jobId, data);
  } catch (error) {
    console.error(`Error fetching status for job ${jobId}:`, error);
    // Optionally update UI to show a fetch error
    updateJobCardUI(jobId, {
      status: "error",
      error: "Could not fetch status.",
    });
    stopPollingJobStatus(jobId); // Stop polling on error
  }
}

function startPollingJobStatus(jobId) {
  if (activePolls[jobId]) {
    console.warn(`Polling already active for job ${jobId}`);
    return;
  }
  console.log(`Starting polling for job ${jobId}`);
  // Initial fetch
  fetchJobStatus(jobId);
  // Set interval for subsequent fetches (e.g., every 5 seconds)
  activePolls[jobId] = setInterval(() => fetchJobStatus(jobId), 5000);
}

function stopPollingJobStatus(jobId) {
  if (activePolls[jobId]) {
    console.log(`Stopping polling for job ${jobId}`);
    clearInterval(activePolls[jobId]);
    delete activePolls[jobId];
  }
}

// --- Result Handling ---
async function fetchAndDisplayResults(jobId, jobCard) {
  const resultsContainer = jobCard.querySelector(".job-results");
  const errorContainer = jobCard.querySelector(".job-error");
  resultsContainer.innerHTML =
    '<p class="text-sm text-gray-500">Loading results...</p>'; // Placeholder
  resultsContainer.classList.remove("hidden");
  errorContainer.classList.add("hidden"); // Hide error section if showing results

  try {
    const response = await fetch(`/result/${jobId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();

    if (data.status === "completed" && data.files && data.files.length > 0) {
      let resultsHTML = `
                 <div class="flex justify-between items-center">
                     <span class="text-sm font-medium text-green-600">Completed</span>
                     <div class="flex space-x-2">
                         <!-- Add Preview Button if needed -->
                         <button class="text-sm px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700 transition">
                             <i class="fas fa-eye mr-1"></i>Preview
                         </button>
                         <div class="relative group">
                             <button class="text-sm px-3 py-1 bg-primary-100 hover:bg-primary-200 text-primary-700 rounded-lg flex items-center space-x-1.5 transition">
                                 <i class="fas fa-download"></i>
                                 <span>Download</span>
                             </button>
                             <div class="absolute right-0 mt-1 bg-white rounded-lg shadow-lg py-1 z-10 hidden group-hover:block w-40 border border-gray-100">
                                 ${data.files
                                   .map(
                                     (filename) => `
                                     <a href="/download/${jobId}/${filename}" download="${filename}" class="block px-3 py-1.5 hover:bg-gray-50 text-sm transition">
                                         Download ${filename
                                           .split(".")
                                           .pop()
                                           .toUpperCase()}
                                     </a>
                                 `
                                   )
                                   .join("")}
                                 ${
                                   data.config?.keep_audio
                                     ? `
                                     <a href="/download/${jobId}/_audio_files/..." download class="block px-3 py-1.5 hover:bg-gray-50 text-sm transition">
                                         Download Audio <!-- Need actual audio filename -->
                                     </a>`
                                     : ""
                                 }
                             </div>
                         </div>
                     </div>
                 </div>`;
      resultsContainer.innerHTML = resultsHTML;
    } else if (data.status === "failed") {
      resultsContainer.classList.add("hidden");
      errorContainer.textContent = `Error: ${data.error || "Job failed."}`;
      errorContainer.classList.remove("hidden");
    } else {
      resultsContainer.innerHTML =
        '<p class="text-sm text-gray-500">No result files found or job not completed.</p>';
    }
  } catch (error) {
    console.error(`Error fetching results for job ${jobId}:`, error);
    resultsContainer.innerHTML = `<p class="text-sm text-red-500">Could not load results: ${error.message}</p>`;
  }
}

// --- Initial Setup & Other UI ---

// Clear Form button (basic implementation)
const clearButton = document.querySelector("button.bg-gray-100.text-gray-700");
clearButton.addEventListener("click", function () {
  // Clear all inputs
  document.querySelectorAll('input[type="text"]').forEach((input) => {
    input.value = "";
  });

  // Reset checkboxes to defaults
  document.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
    if (
      checkbox.id === "speaker-labels-checkbox" ||
      checkbox.id === "keep-audio-checkbox"
    ) {
      checkbox.checked = false;
    } else {
      checkbox.checked = true; // Default for formats (TXT, SRT)
    }
  });

  // Reset selects to first option
  document.querySelectorAll("select").forEach((select) => {
    select.selectedIndex = 0;
  });

  // Hide conditional elements
  audioFormatContainer.classList.add("hidden");

  // Optional: show confirmation toast
  alert("Form has been cleared");
});
