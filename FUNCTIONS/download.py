from pathlib import Path
import time
import re
from sqlite3 import Connection, Cursor
from typing import TypeAlias, cast, Literal
import requests
import json

import yt_dlp 
from yt_dlp.utils import DownloadError, ExtractorError, UnavailableVideoError
from yt_dlp.networking.exceptions import HTTPError 

from FUNCTIONS.helpers import ExtractedInfo, QuietLogger, Ydl_opt, fprint, VideoInfo, youtube_required_info
from FUNCTIONS.metadata import get_metadata_tag, repair_mp3_file
from FUNCTIONS.sql_requests import get_video_info_from_db, update_video_db
from logger import setup_logger

logger = setup_logger(__name__)





def _sanitize_filename(filename: str) -> str:
    old_filename = filename
    filename = filename or ""
    filename = filename.strip()
    filename = re.sub(r'[\\/:*?"<>|~.\x00-\x1F]', "", filename)
    filename = filename.rstrip(". ").strip()
    filename = re.sub(r"\s+", " ", filename)
    logger.debug(f"[Sanitize Filename] Sanitized '{old_filename}' to '{filename}'")
    return filename




def _get_unique_filename(loc: Path, base: str, ext: str, video_id: str) -> str:
    """
    Returns a unique filename not already present in the download dir.
    If file exists and contains matching metadata ID, reuse it.
    """
    counter = 1
    filename = base
    filepath = loc / f"{filename}{ext}"

    while filepath.exists():
        data, state = get_metadata_tag(filepath)
        if state == 0 and data is not None:
            vid: str | None = data.get("video_id")
            if vid is not None:
                if vid == video_id:
                    return filename

        filename = f"{base}_{counter}"
        filepath = loc / f"{filename}{ext}"
        counter += 1

    logger.debug(f"[Get unique filename] computed '{filename}' ({counter - 1} duplicates)")
    return filename







def _build_ydl_opts(loc: Path, filename: str | None = None, format_str: str = "bestaudio/best") -> Ydl_opt:
    """
    Returns yt-dlp options with proper format, output path, and headers.
    """
    outtmpl = str(loc / (filename if filename else "%(title)s.%(ext)s"))

    return {
        "outtmpl": {"default": outtmpl},
        "format": format_str,
        "add_metadata": True,
        "embed_metadata": True,
        "verbose": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            },
            {"key": "FFmpegMetadata"}
        ],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        },
        'extractor_args': {
            'youtube': ['formats=never_pot']
        },
        'fragment_retries': 2,
        'retries': 3,

        "quiet": True,
        "noprogress": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "logger": QuietLogger(),
        "verbose": False
    }







# --- Safe conversion helpers ---
def safe_str(value: object, default: str = "") -> str:
    return str(value) if isinstance(value, str) else default if value is None else str(value)

def safe_int(value: object, default: int = 0) -> int:
    return int(value) if isinstance(value, int) else default

def safe_float(value: object, default: float = 0.0) -> float:
    return float(value) if isinstance(value, float) else default

def safe_bool(value: object, default: bool = False) -> bool:
    return bool(value) if value is not None else default









SubtitleLine: TypeAlias = tuple[float, float, str]  # (start_seconds, end_seconds, text)


def _parse_timestamp(ts: str) -> float:
    """Convert timestamp (HH:MM:SS.mmm or HH:MM:SS,mmm) into seconds (float)"""
    ts = ts.replace(",", ".")
    parts = ts.split(":")
    parts = [float(p) for p in parts]
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m, s = 0.0, parts[0], parts[1]
    else:
        return 0.0
    return h * 3600 + m * 60 + s




def _vtt_to_synced(vtt: str) -> list[SubtitleLine]:
    """Convert WebVTT subtitle text into (start, end, text) tuples"""
    lines: list[SubtitleLine] = []
    pattern = re.compile(r"(\d{2}:\d{2}:\d{2}[.,]\d{3}) --> (\d{2}:\d{2}:\d{2}[.,]\d{3})")

    current_start: float | None = None
    current_end: float | None = None
    current_text: list[str] = []

    for line in vtt.splitlines():
        line = line.strip()
        if not line:
            if current_start is not None and current_end is not None and current_text:
                lines.append((current_start, current_end, " ".join(current_text)))
            current_start, current_end, current_text = None, None, []
            continue

        match = pattern.match(line)
        if match:
            current_start = _parse_timestamp(match.group(1))
            current_end = _parse_timestamp(match.group(2))
            current_text = []
        elif current_start is not None:
            current_text.append(line)

    return lines




def _srt_to_synced(srt: str) -> list[SubtitleLine]:
    """Convert SRT subtitle text into (start, end, text) tuples"""
    lines: list[SubtitleLine] = []
    pattern = re.compile(r"(\d{2}:\d{2}:\d{2}[.,]\d{3}) --> (\d{2}:\d{2}:\d{2}[.,]\d{3})")

    blocks = re.split(r"\n\s*\n", srt.strip())  # split by empty lines (subtitle blocks)

    for block in blocks:
        parts = block.strip().splitlines()
        if len(parts) < 2:
            continue

        # first line might be the sequence number → skip if it's just a number
        if re.match(r"^\d+$", parts[0].strip()):
            parts = parts[1:]

        if not parts:
            continue

        match = pattern.match(parts[0])
        if not match:
            continue

        start = _parse_timestamp(match.group(1))
        end = _parse_timestamp(match.group(2))
        text = " ".join(p.strip() for p in parts[1:])
        if text:
            lines.append((start, end, text))

    return lines



def _pick_subtitles(info: ExtractedInfo, auto: bool = False) -> list[SubtitleLine]:
    """
    Fetch the subtitles.
    Parameters:
      - auto: If True, fetch the auto-generated subtitles; otherwise, fetch manual subtitles.
    Returns:
      - list of (start, end, text) for synced lyrics
      - raw subtitle text (if available, e.g. SRT or VTT)
    """
    subtitles = info.get("subtitles", {}) or {}
    automatic_subtitles = info.get("automatic_captions", {}) or {}

    original_lang: str | None = None
    if isinstance(info.get("language_code"), str):
        original_lang = info.get("language_code")
    elif isinstance(info.get("language"), str):
        original_lang = info.get("language")

    if not original_lang:
        logger.debug(f"[Sub Fetch] No original language detected for {'automatic subtitles' if auto else 'manual subtitles'}")
        return []

    entries = automatic_subtitles.get(original_lang, []) if auto else subtitles.get(original_lang, [])
    if not entries:
        logger.debug(f"[Sub Fetch] No {'automatic' if auto else 'manual'} subtitles found for '{original_lang}'")
        return []

    for entry in entries:
        sub_url = entry.get("url")
        ext = entry.get("ext")
        name = entry.get("name")

        # skip translations for manual subtitles
        if not auto and isinstance(name, str) and "from" in name.lower():
            continue
        if not auto and isinstance(sub_url, str) and "tlang=" in sub_url:
            continue

        if isinstance(sub_url, str) and ext in ("vtt", "srt"):
            try:
                r = requests.get(sub_url, timeout=15)
                if r.status_code == 200:
                    text = r.text
                    if ext == "vtt":
                        return _vtt_to_synced(text)
                    elif ext == "srt":
                        return _srt_to_synced(text)
            except Exception as e:
                logger.error(f"[Sub Fetch] Failed to fetch {'automatic' if auto else 'manual'} subtitles: {e}")
                return []
    return []




def _safe_extract_info(id_or_url: str) -> tuple[Literal[0,1,2,3], VideoInfo]:
    """
    Fetches and returns the videos infos for a YouTube id or URL.
    Returns a tuple of a status code and the formatted data in a dict if data is found:
      0 -> data found and correctly extracted and formatted
      1 -> no data returned by youtube but no exception raised
      2 -> video private
      3 -> unknown error, debug output is printed
    """
    if "https://youtube.com/watch?v=" in id_or_url:
        url = id_or_url
        video_id = id_or_url.replace("https://youtube.com/watch?v=", "")
    else:
        url = f"https://youtube.com/watch?v={id_or_url}"
        video_id = id_or_url

    try:
        ydl_fetch_opt: Ydl_opt = {
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "ignoreerrors": True,
            "logger": QuietLogger(),
            "verbose": False,

            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitlesformat": "vtt",
            "subtitleslangs": ["all"],  # request all available languages
        }

        with yt_dlp.YoutubeDL(ydl_fetch_opt) as ydl:  # pyright: ignore[reportArgumentType]
            info = cast(ExtractedInfo, cast(object, ydl.extract_info(url, download=False)))

            if not info:
                logger.warning(f"[Safe Extract] Data is null for {video_id}")
                return 1, {}




            manual_subs = _pick_subtitles(info, auto=False)
            auto_subs = _pick_subtitles(info, auto=True)

            data: VideoInfo = {
                "video_id": safe_str(info.get("id")),
                "title": safe_str(info.get("fulltitle", info.get("title"))),
                "thumbnail_url": safe_str(info.get("thumbnail")),
                "description": safe_str(info.get("description")),
                "channel_id": safe_str(info.get("channel_id")),
                "channel_url": safe_str(info.get("channel_url")),
                "view_count": safe_int(info.get("view_count")),
                "comment_count": safe_int(info.get("comment_count")),
                "like_count": safe_int(info.get("like_count")),
                "uploader": safe_str(info.get("uploader")),
                "channel_follower_count": safe_int(info.get("channel_follower_count")),
                "uploader_id": safe_str(info.get("uploader_id")),
                "uploader_url": safe_str(info.get("uploader_url")),
                "upload_date": safe_str(info.get("upload_date")),
                "duration": safe_int(info.get("duration")),
                "duration_string": safe_str(info.get("duration_string")),
            }
            if manual_subs:
                logger.debug("[Safe extract] Got manual subs")
                data["subtitles"] =json.dumps(manual_subs, ensure_ascii=False)
            if auto_subs:
                logger.debug("[Safe extract] Got auto subs")
                data["auto_subs"] = json.dumps(auto_subs, ensure_ascii=False)

            logger.info(f"[Safe Extract] Data correctly returned for {video_id} -> '{data['title']}'")
            # print(data)
            return 0, data

    except Exception as e:
        err_msg = str(e).lower()
        if "private video" in err_msg or "private" in err_msg:
            logger.error(f"[Safe Extract] Private video: {video_id}")
            return 2, {}
        logger.error(f"[Safe Extract] Error fetching info for {video_id}: {e}")
        return 3, {}








def download_yt_dlp(
    loc: Path,
    video_id: str,
    title: str,
    uploader: str,
    max_retries: int = 3,
    retry_delay: int = 5
) -> tuple[bool, str, str | None]:
    """
    Download YouTube video as mp3 with retries and detailed error handling.

    Returns:
        success (bool)
        message (str)
        final filename (str)
    """
    url: str = f"https://youtube.com/watch?v={video_id}"
    loc.mkdir(parents=True, exist_ok=True)

    base = _sanitize_filename(title)
    final_filename = _get_unique_filename(loc, base, ".mp3", video_id)
    final_filename_with_ext = final_filename + ".mp3"
    ydl_opts = _build_ydl_opts(loc, final_filename, format_str="bestaudio/best")

    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"[Download] Attempt {attempt} for video {video_id}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # pyright: ignore[reportArgumentType]
                ydl.download([url]) # type:ignore
            # Check file after download - optional: add call to your repair_mp3_file here
            final_path = loc / final_filename_with_ext
            if not final_path.exists():
                raise FileNotFoundError(f"Expected file '{final_path}' not exists after download")

            logger.info(f"[Download] Finished successfully: '{final_filename_with_ext}' from '{uploader}'")
            return True, "", final_filename_with_ext

        except (HTTPError, DownloadError, ExtractorError, UnavailableVideoError) as e:
            logger.warning(f"[Download] Download error on attempt {attempt}: {e}")
            if attempt < max_retries:
                logger.info(f"[Download] Retrying in {retry_delay} seconds")
                time.sleep(retry_delay)
            else:
                return False, f"Download failed after {max_retries} attempts: {e}", None

        except FileNotFoundError as e:
            logger.error(f"[Download] File after download missing: {e}")
            return False, str(e), None

        except Exception as e:
            logger.error(f"[Download] Unexpected error on attempt {attempt}: {e}")
            logger.debug("Exception details:", exc_info=True)
            if attempt < max_retries:
                logger.info(f"[Download] Retrying in {retry_delay} seconds")
                time.sleep(retry_delay)
            else:
                return False, f"Unexpected error after {max_retries} attempts: {e}", None

    return False, "Download failed after retries", None









def download_video(
    download_path: Path,
    video_id: str,
    progress_prefix: str,
    info: bool,
    cur: Cursor,
    conn: Connection,
    test_run: bool
) -> float:

    Download_start_time: float = time.time()

    download_path.mkdir(parents=True, exist_ok=True)


    if info: fprint(progress_prefix, f"Fetching infos for '{video_id}'")
    logger.info(f"[Download] Fetching infos for '{video_id}'")

    # Extracts youtube video's infos if the already present isn't enough
    state: Literal[0,1,2,3] = 0
    data = get_video_info_from_db(video_id=video_id,cur=cur)
    if not all(key in youtube_required_info for key in data.keys()):
        state, data = _safe_extract_info(id_or_url=video_id)
    else:
        logger.debug("[Download] Enough data in db, no need to fetch yt_dlp")

    if state == 0: # Data ok, can proceed to download


        title: str | None = data.get("title", None)
        uploader: str | None = data.get("uploader", None)

        if not isinstance(title, str) or not isinstance(uploader, str):

            update_video_db(video_id,{"status": 3}, cur, conn)
            if info: fprint(progress_prefix, f"title and/or uploader returned not str, probalby a fetching error, skipping video '{video_id}'")
            logger.error(f"[Download] title and/or uploader returned not str, probalby a fetching error, skipping video '{video_id}'")
            return time.time() - Download_start_time

        if info: fprint(progress_prefix,f"Downloading '{title}'")


        download_success, message, final_filename = download_yt_dlp(
            loc=download_path,
            video_id=video_id,
            title=title,
            uploader=uploader
        )

        if download_success and final_filename:
            filename: str = final_filename
            filepath: Path = Path(download_path / filename)

            logger.debug(f"[Download] Downloaded finished, checking file intergity: '{filename}'")
            if repair_mp3_file(filepath=filepath, test_run=test_run): # Newly downloaded file is readable and clean

                # Update metadata
                data["filename"] = final_filename
                data["status"] = 0
                logger.debug(f"[Download] Sucessfully downloaded '{title}")
                if info: fprint(prefix=progress_prefix, title=f"Downloaded '{title}'")
                update_video_db(video_id=video_id, update_fields=data, cur=cur, conn=conn)

            else:
                if info: fprint(prefix=progress_prefix,title=" Downloaded file is corrupted, skipping rest of processing")
                logger.error(f"[Download] Downloaded file is corrupted, skipping rest of processing")

            return time.time() - Download_start_time

        else:
            if message == "Private video":
                data["status"] = 2
                if info: fprint(prefix=progress_prefix, title=f"Video {video_id} is private, skipping")
                logger.warning(f"[Download] Video {video_id} is private, skipping")
            else:
                data["status"] = 3
                if info: fprint(prefix=progress_prefix, title=f"Video {video_id} failed to download, reason : {message}")
                logger.error(f"[Download] Video {video_id} failed to download, reason : {message}")
            
            update_video_db(video_id=video_id, update_fields=data, cur=cur, conn=conn)
            return time.time() - Download_start_time

    else: # Data is null or unavavailable, probalby unavailable video, skipping
        data["status"] = 3
        if info: fprint(progress_prefix, f"Failed to fetch infos for '{video_id}', skipping")
        logger.error(f"[Download] Failed to fetch infos for '{video_id}', skipping")
        update_video_db(video_id=video_id, update_fields=data, cur=cur, conn=conn)
        return time.time() - Download_start_time