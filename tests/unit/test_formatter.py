import pytest
from core.formatter import _format_timestamp, generate_txt, generate_srt # Added generate_txt, generate_srt

# Test cases for _format_timestamp
# Input seconds, expected output string
timestamp_test_cases = [
    (0, "00:00:00,000"),
    (5.5, "00:00:05,500"),
    (65.123, "00:01:05,123"),
    (3600, "01:00:00,000"),
    (3665.999, "01:01:05,999"),
    (86400, "24:00:00,000"), # One full day
    (86399.001, "23:59:59,001"),
    (123.4567, "00:02:03,456"), # Check rounding/truncation of milliseconds
]

@pytest.mark.parametrize("input_seconds, expected_output", timestamp_test_cases)
def test_format_timestamp(input_seconds, expected_output):
    """Tests the _format_timestamp function with various inputs."""
    assert _format_timestamp(input_seconds) == expected_output

def test_format_timestamp_separator():
    """Tests the _format_timestamp function with a custom separator."""
    assert _format_timestamp(12.345, separator='.') == "00:00:12.345"
    assert _format_timestamp(61.0, separator=':') == "00:01:01:000"

# Add more tests for edge cases or invalid inputs if necessary
# e.g., negative numbers, non-numeric types (though type hinting should help)
# Use unittest.mock to patch 'open' and 'os.makedirs'
from unittest.mock import patch, mock_open # Removed MagicMock as it wasn't used directly
import os # Need os for os.path.dirname

def test_format_timestamp_negative():
    """Tests that negative timestamps are formatted as 00:00:00,000 and log a warning."""
    # Patch the logger within the formatter module to check for warnings
    with patch('core.formatter.logger') as mock_logger:
        assert _format_timestamp(-10.5) == "00:00:00,000"
        mock_logger.warning.assert_called_once_with(
            "Received negative timestamp (-10.5s), formatting as 00:00:00,000."
        )


# --- Tests for generate_txt ---

# Mock data for generate_txt tests
txt_test_data_simple = {"text": "This is the transcript text."}
txt_test_data_segments = {
    "segments": [
        {"text": " First segment."},
        {"text": "Second segment. "},
        {"text": None}, # Should be skipped
        {"text": " Third segment."},
    ]
}
txt_test_data_segments_with_speaker = {
    "segments": [
        {"text": " Speaker A says this.", "speaker": "SPEAKER_A"},
        {"text": " Speaker B says that. ", "speaker": "SPEAKER_B"},
    ]
}
txt_test_data_empty = {"text": ""}
txt_test_data_empty_segments = {"segments": []}
txt_test_data_missing = {}

# Expected outputs for generate_txt tests
expected_txt_simple = "This is the transcript text.\n"
expected_txt_segments = "First segment.\nSecond segment.\nThird segment.\n"
expected_txt_segments_with_speaker = "Speaker A says this.\nSpeaker B says that.\n"
expected_txt_empty = "\n" # Writes empty string + newline


# Helper to run generate_txt with mocks
def run_generate_txt_test(mock_data, expected_content, tmp_path):
    output_file = tmp_path / "output.txt"
    # Patch os.makedirs and builtins.open
    with patch("os.makedirs") as mock_makedirs, \
         patch("builtins.open", mock_open()) as mock_file:
        
        success = generate_txt(mock_data, str(output_file))
        
        # Assertions
        mock_makedirs.assert_called_once_with(os.path.dirname(str(output_file)), exist_ok=True)
        mock_file.assert_called_once_with(str(output_file), 'w', encoding='utf-8')
        mock_file().write.assert_called_once_with(expected_content)
        assert success is True

def run_generate_txt_fail_test(mock_data, tmp_path):
     output_file = tmp_path / "output.txt"
     with patch("os.makedirs"), patch("builtins.open", mock_open()):
         success = generate_txt(mock_data, str(output_file))
         assert success is False


def test_generate_txt_simple(tmp_path):
    """Tests generate_txt with simple 'text' input."""
    run_generate_txt_test(txt_test_data_simple, expected_txt_simple, tmp_path)

def test_generate_txt_from_segments(tmp_path):
    """Tests generate_txt reconstructing from 'segments'."""
    run_generate_txt_test(txt_test_data_segments, expected_txt_segments, tmp_path)

def test_generate_txt_from_segments_with_speaker(tmp_path):
    """Tests generate_txt ignores speaker labels in segments."""
    run_generate_txt_test(txt_test_data_segments_with_speaker, expected_txt_segments_with_speaker, tmp_path)

def test_generate_txt_empty(tmp_path):
    """Tests generate_txt with empty 'text'."""
    run_generate_txt_test(txt_test_data_empty, expected_txt_empty, tmp_path)

def test_generate_txt_empty_segments(tmp_path):
     """Tests generate_txt with empty 'segments' list."""
     # Expects empty string + newline if text is None and segments is empty
     run_generate_txt_test(txt_test_data_empty_segments, "\n", tmp_path)

def test_generate_txt_missing_data(tmp_path):
    """Tests generate_txt fails when data is missing."""
    run_generate_txt_fail_test(txt_test_data_missing, tmp_path)


# --- Tests for generate_srt ---

# Mock data for generate_srt tests
srt_test_data_basic = {
    "segments": [
        {"start": 0.0, "end": 2.5, "text": " Segment one."},
        {"start": 3.12, "end": 5.8, "text": " Segment two. "},
    ]
}
srt_test_data_with_speaker = {
    "segments": [
        {"start": 1.0, "end": 3.5, "text": "Hello.", "speaker": "SPEAKER_00"},
        {"start": 4.0, "end": 6.2, "text": "World.", "speaker": "SPEAKER_01"},
    ]
}
srt_test_data_missing_fields = {
    "segments": [
        {"start": 0.0, "end": 1.0, "text": "Good segment."},
        {"start": None, "end": 3.0, "text": "Missing start."}, # Should skip
        {"start": 4.0, "end": 5.0, "text": None}, # Should skip
        {"start": 6.0, "end": 7.0, "text": "Another good one."},
    ]
}
srt_test_data_empty_segments = {"segments": []}
srt_test_data_missing_segments = {}
srt_test_data_preformatted = {
    "text": "1\n00:00:01,000 --> 00:00:02,000\nPreformatted Line 1\n\n2\n00:00:03,000 --> 00:00:04,000\nPreformatted Line 2\n"
}

# Expected outputs for generate_srt tests
expected_srt_basic = """1
00:00:00,000 --> 00:00:02,500
Segment one.

2
00:00:03,120 --> 00:00:05,800
Segment two.
""" # Removed trailing newline
expected_srt_with_speaker = """1
00:00:01,000 --> 00:00:03,500
(SPEAKER_00) Hello.

2
00:00:04,000 --> 00:00:06,200
(SPEAKER_01) World.
""" # Removed trailing newline
expected_srt_missing_fields = """1
00:00:00,000 --> 00:00:01,000
Good segment.

2
00:00:06,000 --> 00:00:07,000
Another good one.
""" # Removed trailing newline
expected_srt_preformatted = srt_test_data_preformatted["text"] # This one already lacks the extra newline


# Helper to run generate_srt with mocks
def run_generate_srt_test(mock_data, expected_content, tmp_path):
    output_file = tmp_path / "output.srt"
    with patch("os.makedirs") as mock_makedirs, \
         patch("builtins.open", mock_open()) as mock_file:
        
        success = generate_srt(mock_data, str(output_file))
        
        mock_makedirs.assert_called_once_with(os.path.dirname(str(output_file)), exist_ok=True)
        mock_file.assert_called_once_with(str(output_file), 'w', encoding='utf-8')
        mock_file().write.assert_called_once_with(expected_content)
        assert success is True

def run_generate_srt_fail_test(mock_data, tmp_path):
     output_file = tmp_path / "output.srt"
     with patch("os.makedirs"), patch("builtins.open", mock_open()):
         success = generate_srt(mock_data, str(output_file))
         assert success is False


def test_generate_srt_basic(tmp_path):
    """Tests generate_srt with basic valid segments."""
    run_generate_srt_test(srt_test_data_basic, expected_srt_basic, tmp_path)

def test_generate_srt_with_speaker(tmp_path):
    """Tests generate_srt includes speaker labels."""
    run_generate_srt_test(srt_test_data_with_speaker, expected_srt_with_speaker, tmp_path)

def test_generate_srt_missing_fields(tmp_path):
    """Tests generate_srt skips segments with missing fields."""
    run_generate_srt_test(srt_test_data_missing_fields, expected_srt_missing_fields, tmp_path)

def test_generate_srt_empty_segments(tmp_path):
    """Tests generate_srt fails with empty segments list."""
    run_generate_srt_fail_test(srt_test_data_empty_segments, tmp_path)

def test_generate_srt_missing_segments(tmp_path):
    """Tests generate_srt fails when 'segments' key is missing."""
    run_generate_srt_fail_test(srt_test_data_missing_segments, tmp_path)

def test_generate_srt_preformatted_fallback(tmp_path):
    """Tests generate_srt writes preformatted text as fallback."""
    run_generate_srt_test(srt_test_data_preformatted, expected_srt_preformatted, tmp_path)
