"""
Voice Input module: Record audio and transcribe using whisper.cpp.

Leverages the existing `transcribe` command for speech-to-text.
Uses ffmpeg for audio recording (press Enter to stop).
"""

import subprocess
import tempfile
import json
import os
import sys
import select
import termios
import tty
import shutil
from pathlib import Path
from typing import Callable

from display import show_voice_status, show_transcription, show_error, console


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
    Transcribe audio using the existing `transcribe` command.

    The transcribe command outputs JSON by default, which we parse
    to extract the transcribed text.

    Args:
        audio_path: Path to the audio file

    Returns:
        Transcribed text or None if transcription failed
    """
    show_voice_status("transcribing")

    try:
        # Run through interactive shell to resolve aliases
        result = subprocess.run(
            ["zsh", "-i", "-c", f"transcribe '{audio_path}'"],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            show_error(f"Transcription failed: {result.stderr}")
            return None

        json_path = Path(audio_path).with_suffix(".json")
        if not json_path.exists():
            base = Path(audio_path).stem
            parent = Path(audio_path).parent
            json_path = parent / f"{base}.json"

        if not json_path.exists():
            for p in Path(audio_path).parent.glob("*.json"):
                if base in p.name:
                    json_path = p
                    break

        if json_path.exists():
            with open(json_path) as f:
                data = json.load(f)

            text_parts = []
            if "transcription" in data:
                for segment in data["transcription"]:
                    if "text" in segment:
                        text_parts.append(segment["text"].strip())
            elif "text" in data:
                text_parts.append(data["text"].strip())
            elif isinstance(data, list):
                for segment in data:
                    if isinstance(segment, dict) and "text" in segment:
                        text_parts.append(segment["text"].strip())

            json_path.unlink()

            text = " ".join(text_parts).strip()
            text = " ".join(text.split())
            return text if text else None

        if result.stdout.strip():
            return result.stdout.strip()

        return None

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

    # Check ffmpeg - standard executable, shutil.which works
    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg")

    # Check transcribe - may be a shell alias, so we need to check via shell
    # First try shutil.which (works for executables in PATH)
    transcribe_found = shutil.which("transcribe")

    if not transcribe_found:
        # Try running 'which transcribe' through the shell to resolve aliases
        try:
            result = subprocess.run(
                ["zsh", "-i", "-c", "which transcribe"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # zsh 'which' shows "aliased to /path" for aliases
            if result.returncode == 0 and result.stdout.strip():
                transcribe_found = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    if not transcribe_found:
        missing.append("transcribe")

    if missing:
        return False, f"Missing: {', '.join(missing)}"

    return True, ""
