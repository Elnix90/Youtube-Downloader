import requests
import subprocess
from pathlib import Path
import json

from logger import setup_logger
logger = setup_logger(__name__)

SPONSORBLOCK_API: str = "https://sponsor.ajay.app/api/skipSegments"



def get_skip_segments(video_id: str, categories: list[str]) -> list[tuple[float, float]]:

    # Properly encode categories list for URL parameter
    params = {
        "videoID": video_id,
        "categories": json.dumps(categories),
    }
    try:
        url = SPONSORBLOCK_API
        response = requests.get(url, params=params)
        response.raise_for_status()
        segments = response.json()  # pyright: ignore[reportAny]
        skips: list[tuple[float, float]] = [(seg["segment"][0], seg["segment"][1]) for seg in segments]  # pyright: ignore[reportAny]
        logger.info(f"[Get skips] Sucessfully got {len(skips)} skips for '{video_id}'")
        return skips
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            # No segments found for this video, treat as empty list
            logger.info(f"[Get skips] Got no skips for '{video_id}'")
            return []
        logger.error(f"[Get skips] Unknown error from sponsoblock api for '{video_id}': {e}")
        return []
    except Exception as e:
        logger.error(f"[Get skips] Got http error for '{video_id}': {e}")
        raise



def cut_segments_ffmpeg(input_file: Path, output_file: Path, segments: list[tuple[float, float]], test_run: bool) -> float:

    if not segments and not test_run:
        _ = subprocess.run(
            ["ffmpeg", "-y", "-i", str(input_file), "-c", "copy", str(output_file)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.warning(f"[Cut Segments] No segments provided for '{input_file}'")
        return 0.0  

    segments = sorted(segments)

    if not test_run: 
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(input_file)],
            text=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        duration = float(probe.stdout.strip())

        total_removed = sum(max(0.0, end - start) for start, end in segments)

        keep_segments: list[tuple[float, float]] = []
        last_end = 0.0
        for start, end in segments:
            if start > last_end:
                keep_segments.append((last_end, start))
            last_end = max(last_end, end)
        if last_end < duration:
            keep_segments.append((last_end, duration))

        filter_parts: list[str] = []
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

        _ = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        logger.info(f"[Cut Segments] Sucessfully cutted {total_removed} seconds from '{input_file}")
        return total_removed
    else:
        logger.debug("[Cut Segments] test_run was enabled, didn't cutted anything")
        return 0.0
