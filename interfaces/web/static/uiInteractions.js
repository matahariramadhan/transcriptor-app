/**
 * uiInteractions.js
 * Handles general UI interactions, form management, and modal display.
 */

// --- DOM Element References ---
const advancedToggle = document.getElementById("advanced-toggle");
const advancedOptions = document.getElementById("advanced-options");
const keepAudioCheckbox = document.getElementById("keep-audio-checkbox");
const audioFormatContainer = document.getElementById("audio-format-container");
const addUrlButton = document.querySelector(
  'button[class*="text-secondary-600"]'
);
const urlInputContainer = document.querySelector(".url-input-container");
const modal = document.getElementById("modal");
const closeModalButton = document.getElementById("close-modal");
const modalCancelButton = document.getElementById("modal-cancel");
const modalConfirmButton = document.getElementById("modal-confirm");
const modalTitle = document.getElementById("modal-title");
const modalContent = document.getElementById("modal-content");
const resultsSection = document.getElementById("results-section");
const clearFormButton = document.querySelector(
  "button.bg-gray-100.text-gray-700"
); // Assuming this is the clear button

// --- Event Listeners Setup ---

export function initializeUIEventListeners() {
  // Advanced Options Toggle
  if (advancedToggle && advancedOptions) {
    advancedToggle.addEventListener("click", toggleAdvancedOptions);
  }

  // Keep Audio Checkbox
  if (keepAudioCheckbox && audioFormatContainer) {
    keepAudioCheckbox.addEventListener("change", toggleAudioFormatDisplay);
    // Initial state
    toggleAudioFormatDisplay();
  }

  // URL Input Management
  if (addUrlButton && urlInputContainer) {
    addUrlButton.addEventListener("click", addUrlInput);
  }
  // Add listeners for initially present remove/paste buttons
  const initialRemoveButton = urlInputContainer?.querySelector(".text-red-500");
  if (initialRemoveButton) {
    initialRemoveButton.addEventListener("click", clearSingleUrlInput);
  }
  const initialPasteButton =
    urlInputContainer?.querySelector(".far.fa-clipboard");
  if (initialPasteButton) {
    addClipboardListener(initialPasteButton);
  }

  // Modal Buttons
  if (closeModalButton) closeModalButton.addEventListener("click", hideModal);
  if (modalCancelButton) modalCancelButton.addEventListener("click", hideModal);

  // Example Error Details Modal Trigger (can be moved/adapted)
  document.querySelectorAll('button[title="Details"]').forEach((button) => {
    button.addEventListener("click", () => {
      const errorDetails =
        "Error Code: 403 - This video is private or requires authentication. Please check if the video is publicly accessible or if you have the correct permissions to access it.";
      showModal(
        "Error Details",
        `<p class="text-red-500">${errorDetails}</p>`,
        hideModal // Simple confirm action
      );
    });
  });

  // Preview Section Toggle
  document.querySelectorAll("button:has(.fa-eye)").forEach((button) => {
    button.addEventListener("click", showPreviewSection);
  });
  document
    .querySelectorAll("#results-section .text-gray-700:has(.fa-times)")
    .forEach((button) => {
      button.addEventListener("click", hidePreviewSection);
    });

  // Clear Form Button
  if (clearFormButton && clearFormButton.textContent.trim() === "Clear Form") {
    clearFormButton.addEventListener("click", clearForm);
  }

  // Initial setup calls
  if (audioFormatContainer) audioFormatContainer.classList.add("hidden");
  if (advancedOptions) advancedOptions.classList.add("hidden");
}

// --- UI Interaction Functions ---

function toggleAdvancedOptions() {
  advancedOptions.classList.toggle("hidden");
  const chevron = advancedToggle.querySelector(
    ".fa-chevron-down, .fa-chevron-up"
  );
  if (chevron) {
    if (advancedOptions.classList.contains("hidden")) {
      chevron.classList.replace("fa-chevron-up", "fa-chevron-down");
    } else {
      chevron.classList.replace("fa-chevron-down", "fa-chevron-up");
    }
  }
}

function toggleAudioFormatDisplay() {
  if (keepAudioCheckbox.checked) {
    audioFormatContainer.classList.remove("hidden");
  } else {
    audioFormatContainer.classList.add("hidden");
  }
}

function addUrlInput() {
  const newUrlInputDiv = document.createElement("div");
  newUrlInputDiv.className = "flex items-start space-x-2";
  newUrlInputDiv.innerHTML = `
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
  urlInputContainer.appendChild(newUrlInputDiv);

  // Add event listeners to new buttons
  newUrlInputDiv
    .querySelector(".remove-url")
    .addEventListener("click", () =>
      urlInputContainer.removeChild(newUrlInputDiv)
    );
  addClipboardListener(newUrlInputDiv.querySelector(".far.fa-clipboard"));
}

function clearSingleUrlInput(event) {
  const input = event.target.closest(".flex").querySelector("input");
  if (input) {
    input.value = "";
  }
}

function addClipboardListener(button) {
  if (!button) return;
  button.parentElement.addEventListener("click", async () => {
    try {
      const text = await navigator.clipboard.readText();
      button.closest(".relative").querySelector("input").value = text;
    } catch (err) {
      console.error("Failed to read clipboard: ", err);
    }
  });
}

export function showModal(title, contentHtml, confirmAction = hideModal) {
  if (!modal || !modalTitle || !modalContent || !modalConfirmButton) return;
  modalTitle.textContent = title;
  modalContent.innerHTML = contentHtml;

  // Clone and replace the confirm button to remove previous listeners
  const newConfirmButton = modalConfirmButton.cloneNode(true);
  modalConfirmButton.parentNode.replaceChild(
    newConfirmButton,
    modalConfirmButton
  );
  newConfirmButton.addEventListener("click", confirmAction);

  modal.classList.remove("hidden");
}

export function hideModal() {
  if (modal) modal.classList.add("hidden");
}

function showPreviewSection() {
  if (resultsSection) {
    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: "smooth" });
    // TODO: Populate preview data based on the specific job card
  }
}

function hidePreviewSection() {
  if (resultsSection) resultsSection.classList.add("hidden");
}

function clearForm() {
  // Clear all URL inputs except the first one
  const urlInputs = urlInputContainer?.querySelectorAll(
    ".flex.items-start.space-x-2"
  );
  urlInputs?.forEach((inputDiv, index) => {
    if (index === 0) {
      const input = inputDiv.querySelector('input[type="text"]');
      if (input) input.value = "";
    } else {
      urlInputContainer.removeChild(inputDiv);
    }
  });

  // Reset selects to first option
  document.querySelectorAll("select").forEach((select) => {
    select.selectedIndex = 0;
  });

  // Reset checkboxes to defaults
  document.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
    const label = checkbox.nextElementSibling?.textContent.trim();
    if (label === "TXT" || label === "SRT") {
      checkbox.checked = true; // Default formats
    } else {
      checkbox.checked = false; // Default others to unchecked
    }
  });

  // Hide conditional elements and reset toggles
  if (audioFormatContainer) audioFormatContainer.classList.add("hidden");
  if (advancedOptions) {
    advancedOptions.classList.add("hidden");
    const chevron = advancedToggle?.querySelector(".fa-chevron-up");
    if (chevron) {
      chevron.classList.replace("fa-chevron-up", "fa-chevron-down");
    }
  }

  console.log("Form cleared");
}
