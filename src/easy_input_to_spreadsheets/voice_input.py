"""
Voice Input module: Record audio and transcribe using whisper.cpp.

Uses ffmpeg for audio recording and whisper.cpp for speech-to-text.
Requires whisper.cpp to be built and a model downloaded.

Setup:
    1. Build whisper.cpp: https://github.com/ggml-org/whisper.cpp
    2. Download a model: ./models/download-ggml-model.sh base.en
    3. Set environment variables (optional):
       - WHISPER_CPP_PATH: Path to whisper-cli executable
       - WHISPER_CPP_MODEL: Path to .bin model file
"""

import subprocess
import tempfile
import os
import sys
import select
import termios
import tty
import shutil
from pathlib import Path

from easy_input_to_spreadsheets.display import (
    show_voice_status,
    show_transcription,
    show_error,
    console,
)


# Default paths to search for whisper.cpp
WHISPER_SEARCH_PATHS = [
    Path.home() / "whisper.cpp" / "build" / "bin" / "whisper-cli",
    Path.home() / "whisper.cpp" / "main",  # Older build name
    Path("/usr/local/bin/whisper-cli"),
    Path("/opt/homebrew/bin/whisper-cli"),
]

# Default model search paths
MODEL_SEARCH_PATHS = [
    Path.home() / "whisper.cpp" / "models" / "ggml-base.en.bin",
    Path.home() / "whisper.cpp" / "models" / "ggml-base.bin",
    Path.home() / "whisper.cpp" / "models" / "ggml-small.en.bin",
    Path.home() / "whisper.cpp" / "models" / "ggml-tiny.en.bin",
]


def find_whisper_cli() -> Path | None:
    """
    Find the whisper-cli executable.

    Checks WHISPER_CPP_PATH env var first, then searches common locations.

    Returns:
        Path to whisper-cli or None if not found
    """
    # Check environment variable first
    env_path = os.environ.get("WHISPER_CPP_PATH")
    if env_path:
        path = Path(env_path)
        if path.exists() and path.is_file():
            return path

    # Check if it's in PATH
    which_result = shutil.which("whisper-cli")
    if which_result:
        return Path(which_result)

    # Search common locations
    for search_path in WHISPER_SEARCH_PATHS:
        if search_path.exists() and search_path.is_file():
            return search_path

    return None


def find_whisper_model() -> Path | None:
    """
    Find a whisper.cpp model file.

    Checks WHISPER_CPP_MODEL env var first, then searches common locations.

    Returns:
        Path to model .bin file or None if not found
    """
    # Check environment variable first
    env_path = os.environ.get("WHISPER_CPP_MODEL")
    if env_path:
        path = Path(env_path)
        if path.exists() and path.is_file():
            return path

    # Search common locations
    for search_path in MODEL_SEARCH_PATHS:
        if search_path.exists() and search_path.is_file():
            return search_path

    # Search for any .bin model in ~/whisper.cpp/models/
    models_dir = Path.home() / "whisper.cpp" / "models"
    if models_dir.exists():
        for model_file in models_dir.glob("ggml-*.bin"):
            return model_file

    return None


def record_audio_ffmpeg(output_path: str, max_duration: int = 30) -> bool:
    """
    Record audio using ffmpeg until Enter is pressed or max duration reached.

    Args:
        output_path: Path to save the audio file
        max_duration: Maximum recording duration in seconds

    Returns:
        True if recording was successful
    """
    console.print(f"[bold magenta]Recording...[/bold magenta] (press [yellow]Enter[/yellow] to stop, max {max_duration}s)")

    try:
        process = subprocess.Popen(
            [
                "ffmpeg",
                "-f", "avfoundation",
                "-i", ":0",
                "-t", str(max_duration),
                "-ar", "16000",
                "-ac", "1",
                "-y",
                "-loglevel", "error",
                output_path
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            while process.poll() is None:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1)
                    if char == '\n' or char == '\r':
                        process.terminate()
                        break
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

        process.wait(timeout=2)
        console.print("[green]Recording stopped[/green]")
        return Path(output_path).exists() and Path(output_path).stat().st_size > 0

    except FileNotFoundError:
        show_error("ffmpeg not found. Please install it: brew install ffmpeg")
        return False
    except Exception as e:
        show_error(f"Recording failed: {e}")
        return False


def transcribe_audio(audio_path: str) -> str | None:
    """
    Transcribe audio using whisper.cpp.

    Args:
        audio_path: Path to the audio file (16-bit WAV, 16kHz, mono)

    Returns:
        Transcribed text or None if transcription failed
    """
    show_voice_status("transcribing")

    whisper_cli = find_whisper_cli()
    model_path = find_whisper_model()

    if not whisper_cli:
        show_error("whisper-cli not found. Set WHISPER_CPP_PATH or build whisper.cpp in ~/whisper.cpp")
        return None

    if not model_path:
        show_error("No whisper model found. Set WHISPER_CPP_MODEL or download a model to ~/whisper.cpp/models/")
        return None

    try:
        # Run whisper-cli with the model and audio file
        # -nt: no timestamps, -np: no prints (cleaner output)
        result = subprocess.run(
            [
                str(whisper_cli),
                "-m", str(model_path),
                "-f", audio_path,
                "-nt",  # No timestamps in output
                "-np",  # No progress prints
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            show_error(f"Transcription failed: {error_msg}")
            return None

        # whisper-cli outputs the transcription to stdout
        text = result.stdout.strip()

        # Clean up the text (remove extra whitespace, newlines)
        text = " ".join(text.split())

        return text if text else None

    except subprocess.TimeoutExpired:
        show_error("Transcription timed out")
        return None
    except Exception as e:
        show_error(f"Transcription error: {e}")
        return None


def get_voice_input(max_duration: int = 30) -> str | None:
    """
    Complete voice input workflow: record audio and transcribe.

    Args:
        max_duration: Maximum recording duration in seconds

    Returns:
        Transcribed text or None if failed
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        audio_path = f.name

    try:
        if not record_audio_ffmpeg(audio_path, max_duration):
            return None

        text = transcribe_audio(audio_path)

        if text:
            show_transcription(text)
            return text
        else:
            show_error("Could not transcribe audio - no speech detected")
            return None

    finally:
        try:
            Path(audio_path).unlink(missing_ok=True)
        except Exception:
            pass


def check_voice_available() -> tuple[bool, str]:
    """
    Check if voice input dependencies are available.

    Returns:
        Tuple of (is_available, error_message)
    """
    missing = []

    # Check ffmpeg
    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg (brew install ffmpeg)")

    # Check whisper-cli
    if not find_whisper_cli():
        missing.append("whisper-cli (build whisper.cpp or set WHISPER_CPP_PATH)")

    # Check model
    if not find_whisper_model():
        missing.append("whisper model (download model or set WHISPER_CPP_MODEL)")

    if missing:
        return False, f"Missing: {', '.join(missing)}"

    return True, ""
