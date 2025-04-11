# run_web_ui.py
# Wrapper script to start the FastAPI/Uvicorn server programmatically,
# intended for use with PyInstaller.

import uvicorn
import uvicorn
import os
import sys
import logging
from pathlib import Path # Add this import

# --- Path Setup ---
# Ensure correct paths are set up, especially for the packaged app context.
# PyInstaller might change the execution context.
if getattr(sys, 'frozen', False):
    # If running in a PyInstaller bundle
    PROJECT_ROOT = Path(sys._MEIPASS) # Use the temp directory created by PyInstaller
else:
    # If running as a normal script
    PROJECT_ROOT = Path(__file__).parent

# Add project root to Python path if not running frozen
# (When frozen, PyInstaller handles imports differently)
if not getattr(sys, 'frozen', False):
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.append(str(PROJECT_ROOT))

# --- Logging Setup (Basic) ---
# Configure basic logging; might need adjustment for packaged app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TranscriptorApp.WebRunner")

# --- Main Execution ---
if __name__ == "__main__":
    logger.info("Web UI Runner Script Starting...")
    try:
        # Import the FastAPI app instance
        # Ensure the import path works both in development and when packaged.
        # Assuming PyInstaller bundles interfaces correctly relative to this script.
        from interfaces.web.main import app

        # Get port, default to 8000
        port = int(os.environ.get("PORT", 8000))
        logger.info(f"Attempting to start Uvicorn on http://127.0.0.1:{port}")

        # Run Uvicorn programmatically
        # Note: Reloading is disabled as it doesn't make sense for a packaged app.
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=port,
            log_level="info" # Can adjust log level if needed
        )
        logger.info("Uvicorn server stopped.")

    except ImportError as e:
        logger.exception(f"Failed to import FastAPI app. Ensure paths are correct. Error: {e}")
        # Provide more guidance if possible
        if getattr(sys, 'frozen', False):
             logger.error("Running frozen - check PyInstaller spec for hidden imports or path issues.")
        else:
             logger.error("Running as script - check PYTHONPATH or script location.")
        # Exit with error code
        sys.exit(1)
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)
