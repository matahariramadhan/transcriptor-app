import { submitJob } from "./apiClient.js";
import { initializeUIEventListeners } from "./uiInteractions.js";
import { addJobToUI, startPollingJobStatus } from "./jobManager.js";

// --- Main Setup ---

// Initialize general UI event listeners on page load
initializeUIEventListeners();

// Add event listener for the main job submission button
const startButton = document.querySelector("button:has(.fa-play)");
if (startButton) {
  startButton.addEventListener("click", handleJobSubmit);
}

async function handleJobSubmit() {
  // --- Gather URLs ---
  const urlInputs = document.querySelectorAll(
    ".url-input-container input[type='text']"
  );
  const urls = Array.from(urlInputs)
    .map((input) => input.value.trim())
    .filter((url) => url !== ""); // Filter out empty strings

  if (urls.length === 0) {
    alert("Please enter at least one URL.");
    return;
  }

  // --- Gather Configuration ---
  // Note: Querying elements inside the handler ensures we get current values
  const modelSelect = document.querySelector('select[class*="input-field"]');
  const formatCheckboxes = document.querySelectorAll(
    'input[type="checkbox"][class*="text-primary-600"]'
  );
  const languageSelect = document.querySelector("#advanced-options select");
  const speakerLabelsCheckbox = document.getElementById(
    "speaker-labels-checkbox"
  );
  const keepAudioCheckbox = document.getElementById("keep-audio-checkbox");
  const audioFormatSelect = document.querySelector(
    "#audio-format-container select"
  );

  const selectedFormats = Array.from(formatCheckboxes)
    .filter((cb) => cb.checked)
    .map((cb) => cb.nextElementSibling.textContent.trim().toLowerCase());

  const jobConfig = {
    model: modelSelect ? modelSelect.value : "whisper-1",
    formats: selectedFormats.length > 0 ? selectedFormats : ["txt", "srt"],
    audio_format:
      keepAudioCheckbox?.checked && audioFormatSelect
        ? audioFormatSelect.value
        : "mp3",
    language:
      languageSelect && languageSelect.value !== ""
        ? languageSelect.value
        : null,
    prompt: null,
    temperature: 0.0,
    speaker_labels: speakerLabelsCheckbox
      ? speakerLabelsCheckbox.checked
      : false,
    keep_audio: keepAudioCheckbox ? keepAudioCheckbox.checked : false,
  };

  const jobRequest = {
    urls: urls,
    config: jobConfig,
  };

  console.log("Submitting job:", jobRequest);

  // --- Send Request to Backend ---
  try {
    startButton.disabled = true;
    startButton.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i> Submitting...`;

    const result = await submitJob(jobRequest); // Use imported function
    console.log("Job submitted successfully:", result);

    addJobToUI(result.job_id, jobRequest.urls[0]); // Use imported function
    startPollingJobStatus(result.job_id); // Use imported function
  } catch (error) {
    console.error("Failed to submit job:", error);
    alert(`Failed to submit job: ${error.message}`);
  } finally {
    startButton.disabled = false;
    startButton.innerHTML = `<i class="fas fa-play"></i> <span>Start Transcription</span>`;
  }
}

console.log("TranscriptorApp UI Initialized and event listeners attached.");
