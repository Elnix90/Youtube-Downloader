import requests
import subprocess
from pathlib import Path
from typing import List, Tuple, Any
import json

SPONSORBLOCK_API = "https://sponsor.ajay.app/api/skipSegments"

def get_skip_segments(video_id: str, categories: List[str] = []) -> List[Tuple[float, float]]:
    if not categories:
        categories = ["music_offtopic", "sponsor", "intro", "outro"]

    # Properly encode categories list for URL parameter
    params = {
        "videoID": video_id,
        "categories": json.dumps(categories),
    }
    try:
        url = SPONSORBLOCK_API
        response = requests.get(url, params=params)
        response.raise_for_status()
        segments = response.json()
        skips = [(seg["segment"][0], seg["segment"][1]) for seg in segments]
        return skips
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            # No segments found for this video, treat as empty list
            return []
        else:
            raise
    except Exception:
        raise

def cut_segments_ffmpeg(input_file: Path, output_file: Path, segments: List[Tuple[float, float]]) -> float:

    if not segments:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(input_file), "-c", "copy", str(output_file)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return 0.0  

    segments = sorted(segments)

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(input_file)],
        text=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    duration = float(probe.stdout.strip())

    total_removed = sum(max(0.0, end - start) for start, end in segments)

    keep_segments: List[Any] = []
    last_end = 0.0
    for start, end in segments:
        if start > last_end:
            keep_segments.append((last_end, start))
        last_end = max(last_end, end)
    if last_end < duration:
        keep_segments.append((last_end, duration))

    filter_parts: List[Any] = []
    for i, (start, end) in enumerate(keep_segments):
        filter_parts.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]")
    concat_inputs = "".join(f"[a{i}]" for i in range(len(keep_segments)))
    filter_complex = ";".join(filter_parts) + f";{concat_inputs}concat=n={len(keep_segments)}:v=0:a=1[outa]"

    cmd = [
        "ffmpeg", "-y", "-i", str(input_file),
        "-filter_complex", filter_complex,
        "-map", "[outa]",
        str(output_file)
    ]

    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return total_removed

# Example usage:
if __name__ == "__main__":
    video_id = "4NRXx6U8ABQ"  # Replace with real YouTube ID
    input_file = Path("TESTS/1755854207.mp3")
    output_file = Path("TESTS/output_clean.mp3")

    skips = get_skip_segments(video_id)
    # cut_segments_ffmpeg(input_file, output_file, skips)
    print(f"Processed file saved at {output_file}")
