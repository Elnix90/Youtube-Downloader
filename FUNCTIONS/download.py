from __future__ import annotations

from pathlib import Path
import time
import re
import shutil
from datetime import datetime,timedelta
import subprocess
from typing import Set ,Dict, List, Optional, Tuple, Union, TYPE_CHECKING, Any, cast

import yt_dlp #type: ignore
from mutagen.mp3 import MP3  # type: ignore
from mutagen.id3 import ID3  # type: ignore
from mutagen.id3._frames import USLT  # type: ignore
from mutagen.id3._specs import Encoding  # type: ignore

from CONSTANTS import ERROR_DOWNLOADED_FILE, UNAVAILABLE_VIDEOS_FILE
from FUNCTIONS.extract_lyrics import get_lyrics_from_syncedlyrics
from FUNCTIONS.fileops import load, dump
from FUNCTIONS.list import Process_list
from FUNCTIONS.create_videos_to_download_file import get_metadata_tag 
from FUNCTIONS.metadata import write_metadata_tag
from FUNCTIONS.sponsorblock import get_skip_segments, cut_segments_ffmpeg
from FUNCTIONS.tags_system import compute_tags,set_tags

if TYPE_CHECKING:
    YtdlInfo = Dict[str, Any]
else:
    YtdlInfo = dict


class QuietLogger:
    def debug(self, msg: str) -> None:
        return None

    def warning(self, msg: str) -> None:
        return None

    def error(self, msg: str) -> None:
        return None


def sanitize_filename(filename: str) -> str:
    filename = filename or ""
    filename = filename.strip()
    filename = re.sub(r'[\\/:*?"<>|~.\x00-\x1F]', "", filename)
    filename = filename.rstrip(". ").strip()
    filename = re.sub(r"\s+", " ", filename)
    return filename


def get_unique_filename(loc: Path, base: str, ext: str, video_id: str) -> str:
    counter = 1
    filename = f"{base}{ext}"
    filepath = loc / filename

    while filepath.exists():
        data, state = get_metadata_tag(filepath)  # type: ignore
        if state == 0 and data is not None:
            vid: str = data.get("id") # type: ignore
            if vid == video_id:
                return filename
        filename = f"{base}_{counter}{ext}"
        filepath = loc / filename
        counter += 1

    return filename


def embed_lyrics_into_mp3(mp3_path: Path, lyrics: str) -> bool:
    try:
        audio = MP3(str(mp3_path), ID3=ID3)  # type: ignore
        if audio.tags is None: # type: ignore
            audio.add_tags() # type: ignore
        uslt = USLT(encoding=Encoding.UTF8, desc="Lyrics", text=lyrics)  # type: ignore
        audio.tags.add(uslt) # type: ignore
        audio.save() # type: ignore
        return True
    except Exception as e:
        print(f"\nError embedding lyrics into {mp3_path}: {e}")
        return False


def safe_extract_info(ydl: Any, url: str, private_videos: set[str], video_id: str) -> Optional[YtdlInfo]:
    try:
        info = ydl.extract_info(url, download=False)  # type: ignore
        if info is None:
            private_videos.add(video_id)
            dump(list(private_videos), UNAVAILABLE_VIDEOS_FILE)
            return None
        return cast(YtdlInfo, info)
    except Exception as e:  # type: ignore
        err_msg = str(e).lower()
        if "private video" in err_msg or "private" in err_msg:
            private_videos.add(video_id)
            dump(list(private_videos), UNAVAILABLE_VIDEOS_FILE)
            return None
        print(f"Error fetching info for {video_id}: {e}")
        return None



def fprint(prefix: str,title: str, suffix: str, overwrite: bool = True, end: str = "",flush: bool = True) -> None:
    term_width = shutil.get_terminal_size((80, 20)).columns
    max_len = term_width - len(prefix) - len(suffix) - 3
    if max_len < 1:
        max_len = 1
    if len(title) > max_len:
        title = title[:max_len-1] + "…"
        space_nb = 0
    else:
        space_nb = max_len - len(title)

    print(f"{'\r\033[K' if overwrite else ''}{prefix}{title}{' ' * space_nb}{suffix}",end=end,flush=flush)


def download_yt_dlp(
    url: str,
    loc: Path,
    video_id: str,
    uploader: str,
    title: str,
    progress_prefix: str,
    use_sponsorblock: bool = True
) -> Tuple[bool, List[str], Optional[Path], Optional[str], int, float]:
    loc_path = Path(loc)
    loc_path.mkdir(parents=True, exist_ok=True)
    renamed_files: List[str] = []

    def progress_hook(d: dict) -> None: # type: ignore
        status: str = d.get("status","unknown") # type: ignore
        if status == "downloading":
            percent: str = d.get("_percent_str", "").strip() # type: ignore
            speed: str = d.get("_speed_str", "N/A").strip() # type: ignore
            eta: str = d.get("_eta_str", "N/A").strip() # type: ignore
            fprint(progress_prefix,f" | Downloading: {title}",f" | {percent} at {speed}, ETA: {eta}")
        elif status == "finished":
            fprint(progress_prefix,f" | Post-processing: {title}","")

    ydl_opts: dict = { # type: ignore
        "outtmpl": {"default": str(loc_path / "%(title)s.%(ext)s")},

        # No logs from yt_dlp, I handle all of this manually
        "quiet": True,
        "noprogress": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "logger": QuietLogger(),
        # "verbose": True,

        "format": "bestaudio/best",
        "postprocessor_args": ["-metadata", f"artist={uploader}", "-metadata", f"title={title}"],
        "add_metadata": True,
        "embed_metadata": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            },
            {"key": "FFmpegMetadata"}
            ],
        "progress_hooks": [progress_hook],
    }


    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
            base = sanitize_filename(title)
            new_filename = get_unique_filename(loc_path, base, f".{"mp3"}", video_id)
            ydl.params["outtmpl"]["default"] = str((loc_path / Path(new_filename).stem).with_suffix(".%(ext)s")) # type: ignore
            ydl.download([url])  # type: ignore
            
            final_path = loc_path / Path(new_filename).with_suffix(".mp3")

            sucessful_segments_cutted: int = 0
            total_removed: float = 0.0

            if use_sponsorblock and final_path.exists():
                fprint(progress_prefix, " | Fetching SponsorBlock segments...", "")
                skips = get_skip_segments(video_id)
                if skips:
                    fprint(progress_prefix, f" | Removing {len(skips)} SponsorBlock segments...", "")
                    temp_output = final_path.with_suffix(".tmp.mp3")
                    try:
                        total_removed = cut_segments_ffmpeg(final_path, temp_output, skips)
                        sucessful_segments_cutted = len(skips)
                    except subprocess.CalledProcessError:
                        if temp_output.exists():
                            temp_output.unlink()
                    else:
                        temp_output.replace(final_path)


        return True, renamed_files, loc_path, final_path.name, sucessful_segments_cutted, total_removed
    
    except Exception as e:  # type: ignore
        msg = str(e)
        if "private" in msg.lower():
            return False, ["Private video"], None, None, 0, 0.0
        return False, [msg], None, None, 0, 0.0


def download_playlist(
    file: Path,
    loc: Path,
    embed_metadata: bool = True,
    get_lyrics: bool = True,
    use_list: bool = False,
    show_ETA: bool = True,
    use_sponsorblock: bool =True,
    add_tags: bool = True
) -> str:
    Download_start_time: float = time.time()

    pl: Optional[Process_list] = Process_list() if use_list else None
    loc_path: Path = Path(loc)
    loc_path.mkdir(parents=True, exist_ok=True)

    if use_list:
        pl = Process_list()


    avg_times: List[int] = []
    eta_str: str = 'N/A'

    ids: List[str] = load(Path(file))

    unavailable_videos: set[str] = set(load(UNAVAILABLE_VIDEOS_FILE)) if Path(UNAVAILABLE_VIDEOS_FILE).exists() else set()
    total_videos: int = len(ids)

    error_downloaded: Dict[str, str] = {}
    all_renamed_files: List[str] = []

    progress_count: int = 1
    idx: int = 0

    print(f"[Download] Downloading {total_videos} videos...")

    while idx < len(ids):

        start_time = round(time.time())

        video_id: str = ids[idx]
        url = f"https://youtube.com/watch?v={video_id}"
        progress_prefix: str = f"{progress_count:{len(str(total_videos))}d}/{total_videos}"
        if show_ETA:
            progress_prefix += f" | ETA : {eta_str}"

        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "noprogress": True, "ignoreerrors": True, "logger": QuietLogger()}) as ydl:
            fprint(progress_prefix,f" | Fetching video infos: {video_id}","",overwrite=show_ETA)
            info = safe_extract_info(ydl, url, unavailable_videos, video_id)
            if not info:
                fprint(progress_prefix,f" | Skipping unavailable video: {video_id}","")
                unavailable_videos.add(video_id)
                dump(list(unavailable_videos), UNAVAILABLE_VIDEOS_FILE)
                try:
                    ids.remove(video_id)
                except ValueError:
                    pass
                dump(ids, Path(file))
                if use_list and pl is not None:
                    pl.update(video_id, {"status": "unavailable"})
                continue

            id_val = str(info.get("id", "N/A"))
            title = str(info.get("fulltitle", info.get("title", "Unknown")))
            thumbnail = str(info.get("thumbnail", "N/A"))
            description = str(info.get("description", "N/A"))
            channel_id = str(info.get("channel_id", "N/A"))
            channel_url = str(info.get("channel_url", "N/A"))
            duration = int(info.get("duration", 0) or 0)
            view_count = int(info.get("view_count", 0) or 0)
            comment_count = int(info.get("comment_count", 0) or 0)
            like_count = int(info.get("like_count", 0) or 0)
            uploader = str(info.get("uploader", "N/A"))
            channel_follower_count = int(info.get("channel_follower_count", 0) or 0)
            uploader_id = str(info.get("uploader_id", "N/A"))
            uploader_url = str(info.get("uploader_url", "N/A"))
            upload_date = str(info.get("upload_date", "N/A"))
            duration_string = str(info.get("duration_string", ""))



            metadata_obj: Dict[str, Union[str, int, float, list[str]]] = {
                "id": id_val,
                "title": title,
                "thumbnail": thumbnail,
                "description": description,
                "channel_id": channel_id,
                "channel_url": channel_url,
                "duration": duration,
                "view_count": view_count,
                "comment_count": comment_count,
                "like_count": like_count,
                "uploader": uploader,
                "channel_follower_count": channel_follower_count,
                "uploader_id": uploader_id,
                "uploader_url": uploader_url,
                "upload_date": upload_date,
                "duration_string": duration_string,
            }

            

            success, renamed_files, returned_loc, filename, nb_cutted_seg, total_removed = download_yt_dlp(
                url=url,
                loc=loc_path,
                video_id=video_id,
                uploader=uploader,
                title=title,
                progress_prefix=progress_prefix,
                use_sponsorblock=use_sponsorblock
            )

            if success and filename and returned_loc is not None:
                filepath: Path = returned_loc / filename

                query_used: str = ""
                end_msg: str = ""
                if get_lyrics:
                    fprint(progress_prefix,f" | Getting lyrics : {title}","")
                    lyrics, query_used = get_lyrics_from_syncedlyrics(title, uploader)
                    if lyrics and filepath.exists() and filepath.stat().st_size > 0:
                        metadata_obj["lyrics"] = lyrics
                        metadata_obj["query_used"] = query_used
                        fprint(progress_prefix,f" | Embedding lyrics: {title}","")
                        embed_lyrics_into_mp3(filepath, lyrics)
                        end_msg = " | 📃 Lyrics Found"


                # Update the file's last modified time
                now: float = time.time()
                filepath.touch()
                filepath.stat()
                file_path_utime: Tuple[float,float] = (now, now)
                try:
                    filepath.utime(file_path_utime) # type: ignore
                except Exception:
                    import os
                    os.utime(str(filepath), file_path_utime)


                if use_sponsorblock and nb_cutted_seg > 0:
                    end_msg += f" | {nb_cutted_seg} Segment removed ({round(total_removed)} seconds)"
                    metadata_obj['removed_segments_int'] = nb_cutted_seg
                    metadata_obj['removed_segments_duration'] = total_removed

                new_filename: Optional[str] = None
                if add_tags:
                    tags: Set[str] = compute_tags(title,uploader)

                    new_uploader: Optional[str] = set_tags(filepath,tags)

                    metadata_obj['tags'] = list(tags)
                    if new_uploader: metadata_obj['uploader'] = new_uploader

                # Prepare metadata for embedding
                if embed_metadata:

                    metadata_obj["filename"] = new_filename if new_filename is not None else filename
                    metadata_obj["date_added_int"] = round(now)
                    metadata_obj["date_added_str"] = datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')
                    metadata_obj['status'] = "downloaded"


                    # Embed metadata into the MP3 file
                    fprint(progress_prefix,f" | Writing metadata: {title}","")
                    if not write_metadata_tag(filepath, metadata_obj):
                        end_msg += " | ❌ Metadata write failed"


                # Finaly show the downloaded message
                fprint(progress_prefix,f" | Downloaded: {title}",end_msg,end="\n")



                if use_list and pl is not None:
                    updated_data: Dict[str, Any] = metadata_obj if embed_metadata else {}
                    pl.update(video_id, updated_data)

                all_renamed_files.extend(renamed_files)
                try:
                    ids.pop(idx)
                except IndexError:
                    try:
                        ids.remove(video_id)
                    except ValueError:
                        pass
                dump(ids, Path(file))

            else:
                if (renamed_files == ["Private video"]) or (success is False and filename is None):
                    unavailable_videos.add(video_id)
                    dump(list(unavailable_videos), UNAVAILABLE_VIDEOS_FILE)
                    fprint(progress_prefix,f" | Error during download or processing : marked as unavailable: {video_id}","",overwrite=True,end="\n")
                    if use_list and pl is not None:
                        pl.update(video_id, {"status": "unavailable","reason": renamed_files[0]})
                else:
                    error_downloaded[video_id] = ", ".join(renamed_files) if renamed_files else "Unknown error"
                    dump(error_downloaded, ERROR_DOWNLOADED_FILE)
                idx += 1

        
        progress_count += 1
        end_time: int = round(time.time())
        avg_times.append(end_time - start_time)
        if len(avg_times) > 10:
            avg_times.pop(0)
        
        if show_ETA:
            eta_seconds = int((sum(avg_times) / len(avg_times)) * (total_videos - progress_count + 1))
            eta_str = str(timedelta(seconds=eta_seconds))



    if error_downloaded:
        print(f"\n[Download] Some videos could not be downloaded. See {ERROR_DOWNLOADED_FILE} for details.")

    Download_end_time: float = time.time()

    Download_total_time: float = Download_end_time - Download_start_time

    file.unlink(missing_ok=True)
    return str(timedelta(seconds=int(Download_total_time)))