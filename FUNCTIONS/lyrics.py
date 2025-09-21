from pathlib import Path
import re
import json
import os

from FUNCTIONS.helpers import lyrics_lrc_path_for_mp3


from logger import setup_logger
logger = setup_logger(__name__)






def embed_lyrics_into_mp3(
    filepath: Path,
    lyrics: str,
    test_run: bool,
    file_duration: int,
    skips: list[tuple[float, float]] | None,
    original_duration: int | None
) -> tuple[bool, str]:
    """
    Instead of embedding into mp3 tags, write a .lrc file next to the mp3.
    Returns True on success, False otherwise.
    """
    if not filepath.exists():
        logger.error(f"[Embed lyrics] File not found : '{filepath}'")
        return False, ""


    try:
        # Sanitize/adjust lyrics for skips/tempo and convert to LRC string when appropriate.
        try:
                lrc_text = sanitize_lyrics_to_lrc(
                lyrics=lyrics,
                skips=skips,
                file_duration=float(file_duration) if file_duration else 0.0,
                original_duration=float(original_duration) if original_duration else None
            )

        except Exception as e:
            logger.error(f"[Embed lyrics] Failed to sanitize/adjust lyrics: {e}")
            # fallback to raw lyrics
            lrc_text = lyrics

        lrc_path = lyrics_lrc_path_for_mp3(mp3_path=filepath)
        logger.verbose(f"[Embed lyrics] Writing LRC to '{lrc_path}'")
        if not test_run:
            # Ensure parent exists
            lrc_path.parent.mkdir(parents=True, exist_ok=True)
            with open(lrc_path, "w", encoding="utf-8") as f:
                _ = f.write(lrc_text)
        logger.info(f"[Embed lyrics] Wrote lyrics file '{lrc_path.name}' for '{filepath.name}'")
        return True, lrc_text
    except Exception as e:
        logger.error(f"[Embed lyrics] Failed to write LRC file for '{filepath}': {e}")
        return False, ""







def remove_lyrics_from_mp3(filepath: Path, error: bool, test_run: bool) -> bool:
    """
    Remove the corresponding .lrc file (if present). Keep the same signature for compatibility.
    """
    try:
        lrc_path = lyrics_lrc_path_for_mp3(filepath)
        if not lrc_path.exists():
            logger.debug(f"[Remove lyrics] No .lrc file to remove at '{lrc_path}'")
            return True
        if not test_run:
            os.remove(lrc_path)
        logger.info(f"[Remove lyrics] Removed lyrics file '{lrc_path}'")
        return True
    except Exception as e:
        logger.error(f"[Remove lyrics] Failed to remove .lrc for '{filepath}': {e}")
        if error:
            print(f"\nError removing lyrics file for {filepath}: {e}")
        return False






def has_lyrics(mp3_path: Path) -> str | None:
    """
    Check if a .lrc file exists next to the mp3 and is non-empty.
    """
    try:
        lrc_path = lyrics_lrc_path_for_mp3(mp3_path)
        if not lrc_path.exists():
            logger.debug(f"[Lyrics Check] No .lrc file for '{mp3_path.name}'")
            return None
        try:
            txt = lrc_path.read_text(encoding="utf-8")
            if txt and txt.strip():
                logger.debug(f"[Lyrics Check] .lrc lyrics found for '{mp3_path.name}'")
                return txt
            logger.warning(f"[Lyrics Check] .lrc file empty for '{mp3_path.name}'")
            return None
        except Exception as e:
            logger.error(f"[Lyrics Check] Error reading .lrc file for '{mp3_path.name}': {e}")
            return None
    except Exception as e:
        logger.error(f"[Lyrics Check] Error checking lyrics for '{mp3_path.name}': {e}")
        return None









logger = setup_logger(__name__)

# ---------- Helpers for timestamps ----------
_ts_lrc_re = re.compile(r'\[(\d{1,2}:\d{2}(?:\.\d{1,3})?)\]')   # [mm:ss.xx] or [h:mm:ss.xx]
_srt_time_re = re.compile(r'\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[.,]\d{3}')
_vtt_re = re.compile(r'^\s*WEBVTT', re.IGNORECASE | re.MULTILINE)


def _parse_timestamp_to_seconds(ts: str) -> float:
    """Parse timestamp to float seconds"""
    try:
        parts = ts.split(':')
        if len(parts) == 2:
            mm = int(parts[0])
            ss = float(parts[1])
            return mm * 60.0 + ss
        elif len(parts) == 3:
            hh = int(parts[0])
            mm = int(parts[1])
            ss = float(parts[2])
            return hh * 3600.0 + mm * 60.0 + ss
        return float(ts)
    except Exception as e:
        logger.warning(f"[Parse Timestamp] Failed to parse '{ts}': {e}")
        return 0.0


def _format_seconds_to_lrc(ts_seconds: float, centis: int = 2) -> str:
    """Format seconds to LRC timestamp"""
    ts_seconds = max(0.0, ts_seconds)
    hours = int(ts_seconds // 3600)
    rem = ts_seconds - hours * 3600
    minutes = int(rem // 60)
    seconds = rem - minutes * 60
    frac = f"{seconds:.{centis}f}"
    int_sec = int(float(frac))
    frac_part = frac.split('.')[-1] if '.' in frac else '0'*centis
    if hours:
        return f"[{hours:02d}:{minutes:02d}:{int_sec:02d}.{frac_part}]"
    return f"[{minutes:02d}:{int_sec:02d}.{frac_part}]"


# ---------- 1. Detect synchronized lyrics ----------
def is_synchronized_lyrics(text: str) -> bool:
    if not text:
        return False

    # Case 1: LRC, SRT, VTT
    if _ts_lrc_re.search(text) or _srt_time_re.search(text) or _vtt_re.search(text):
        logger.debug("[Lyrics Detection] Text is synchronized (LRC/SRT/VTT)")
        return True

    # Case 2: JSON-based subtitles (YouTube style: [[start, end, text], ...])
    try:
        maybe = json.loads(text)  # pyright: ignore[reportAny]
        if isinstance(maybe, list) and all(
            isinstance(item, (list, tuple)) and len(item) in (2, 3)  # pyright: ignore[reportUnknownArgumentType]
            for item in maybe  # pyright: ignore[reportUnknownVariableType]
        ):
            logger.debug("[Lyrics Detection] Text is synchronized (JSON triplets)")
            return True
    except Exception:
        pass

    logger.debug("[Lyrics Detection] Text is NOT synchronized")
    return False

# ---------- 2. Parse LRC ----------
def parse_lrc(lyrics: str) -> list[tuple[float, str]]:
    out: list[tuple[float, str]] = []
    if not lyrics:
        return out
    for line in lyrics.splitlines():
        matches = list(_ts_lrc_re.finditer(line))
        if not matches:
            continue
        last = matches[-1]
        text = line[last.end():].strip() or ""
        for m in matches:
            t = _parse_timestamp_to_seconds(m.group(1))
            out.append((t, text))
    logger.debug(f"[Parse LRC] Parsed {len(out)} timestamped lines")
    return out


# ---------- 3. Compose LRC ----------
def compose_lrc(entries: list[tuple[float, str]], centis: int = 2) -> str:
    lines = [f"{_format_seconds_to_lrc(t, centis)}{txt}" for t, txt in entries]
    logger.debug(f"[Compose LRC] Composed {len(lines)} lines")
    return "\n".join(lines)


# ---------- 4. Shift timestamps ----------
def shift_lrc_timestamps(lyrics: str, offset_seconds: float, drop_before_zero: bool = True) -> str:
    entries = parse_lrc(lyrics)
    shifted: list[tuple[float, str]] = []
    for t, txt in entries:
        new_t = t + offset_seconds
        if new_t < 0 and drop_before_zero:
            continue
        shifted.append((max(0.0, new_t), txt))
    logger.debug(f"[Shift LRC] Shifted {len(shifted)} lines by {offset_seconds}s")
    return compose_lrc(shifted)


# ---------- 5. Apply removed segments (shift timestamps) ----------
def apply_removed_segments_to_lrc(lyrics: str, removed_segments: list[tuple[float, float]]) -> str:
    if not removed_segments:
        logger.debug("[Apply Skips] No segments to apply")
        return lyrics

    segments = sorted((float(s), float(e)) for s, e in removed_segments)
    entries = parse_lrc(lyrics)
    mapped: list[tuple[float, str]] = []

    for t, txt in entries:
        shift = 0.0
        drop_line = False
        for s, e in segments:
            if t >= e:
                shift += (e - s)
            elif s <= t < e:
                drop_line = True
                break
        if drop_line:
            continue
        mapped.append((t - shift, txt))

    logger.debug(f"[Apply Skips] Shifted {len(mapped)} lines after applying {len(segments)} segments")
    return compose_lrc(mapped)


# ---------- 6. Scale timestamps ----------
def scale_lrc_timestamps(lyrics: str, scale: float) -> str:
    entries = parse_lrc(lyrics)
    scaled = [(t * scale, txt) for t, txt in entries]
    logger.debug(f"[Scale LRC] Scaled {len(scaled)} lines by factor {scale}")
    return compose_lrc(scaled)


# ---------- 7. Sanitize lyrics ----------
def sanitize_lyrics_to_lrc(
    lyrics: str,
    skips: list[tuple[float, float]] | None,
    file_duration: float,
    original_duration: float | None
) -> str:
    if not lyrics:
        return ""

    if not is_synchronized_lyrics(lyrics):
        logger.info("[Sanitize Lyrics] Lyrics are not synchronized, returning original")
        return lyrics

    # Parse JSON, LRC, or SRT/VTT
    parsed_triplets: list[tuple[float, float, str]] = []

    try:
        maybe = json.loads(lyrics)  # pyright: ignore[reportAny]
        if isinstance(maybe, list):
            for item in maybe:  # pyright: ignore[reportUnknownVariableType]
                if isinstance(item, (list, tuple)) and len(item) in (2, 3):  # pyright: ignore[reportUnknownArgumentType]
                    s = float(item[0])  # pyright: ignore[reportUnknownArgumentType]
                    e = float(item[1]) if len(item) == 3 else file_duration  # pyright: ignore[reportUnknownArgumentType]
                    t = str(item[2]) if len(item) == 3 else str(item[1])  # pyright: ignore[reportUnknownArgumentType]
                    parsed_triplets.append((s, e, t))
    except Exception:
        parsed_triplets = []

    if not parsed_triplets:
        # Fallback: LRC parsing
        pairs = parse_lrc(lyrics)
        for i, (start, txt) in enumerate(pairs):
            end = pairs[i + 1][0] if i + 1 < len(pairs) else file_duration or start + 5.0
            parsed_triplets.append((start, end, txt))

    parsed_triplets.sort(key=lambda x: x[0])

    # Apply skips
    if skips:
        segments = sorted((float(s), float(e)) for s, e in skips)
        mapped: list[tuple[float, float, str]] = []
        for s, e, txt in parsed_triplets:
            shift = 0.0
            drop_line = False
            for seg_start, seg_end in segments:
                if s >= seg_end:
                    shift += seg_end - seg_start
                elif seg_start <= s < seg_end:
                    drop_line = True
                    break
            if drop_line:
                continue
            mapped.append((s - shift, e - shift, txt))
        parsed_triplets = mapped
        logger.debug(f"[Sanitize Lyrics] Applied skips, {len(parsed_triplets)} lines remain")

    # Apply tempo scaling
    if original_duration and original_duration > 0:
        total_removed = sum(max(0.0, e - s) for s, e in skips) if skips else 0.0
        expected_after = original_duration - total_removed
        if expected_after > 0:
            scale = file_duration / expected_after
            if abs(scale - 1.0) > 0.001:
                parsed_triplets = [(s * scale, e * scale, txt) for s, e, txt in parsed_triplets]
                logger.debug(f"[Sanitize Lyrics] Applied tempo scaling factor {scale}")

    # Final LRC lines (start time + text)
    final_entries: list[tuple[float, str]] = [(max(0.0, s), txt) for s, e, txt in parsed_triplets]  # pyright: ignore[reportUnusedVariable]
    final_entries.sort(key=lambda x: x[0])

    # Deduplicate
    cleaned: list[tuple[float, str]] = []
    last = None
    for item in final_entries:
        if last and item[0] == last[0] and item[1] == last[1]:
            continue
        cleaned.append(item)
        last = item

    lrc_text = compose_lrc(cleaned, centis=2)
    logger.info(f"[Sanitize Lyrics] Final LRC composed with {len(cleaned)} lines")
    return lrc_text
