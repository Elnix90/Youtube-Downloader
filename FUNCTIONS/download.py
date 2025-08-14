import yt_dlp
import os
import re
import time
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, USLT, Encoding
from CONSTANTS import VIDEOS_TO_DOWNLOAD_FILE, ERROR_DOWNLOADED_FILE, PRIVATE_VIDEOS_FILE
from FUNCTIONS.extract_lyrics import get_lyrics_from_genius
from FUNCTIONS.fileops import load, dump
from pathlib import Path


def sanitize_filename(filename):
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    filename = filename.rstrip('. ').strip()
    filename = re.sub(r'\s+', ' ', filename)
    return filename

def get_unique_filename(loc, base, ext, video_id):
    counter = 1
    filename = f"{base}{ext}"
    while os.path.exists(os.path.join(loc, filename)):
        try:
            with open(os.path.join(loc, filename), 'rb') as f:
                content = f.read()
                if f"Video ID : {video_id}".encode() in content:
                    return filename
        except Exception:
            pass
        filename = f"{base}_{counter}{ext}"
        counter += 1
    return filename



def embed_lyrics_into_mp3(mp3_path, lyrics, lang='eng'):
    try:
        audio = MP3(mp3_path, ID3=ID3)
        if not audio.tags:
            audio.add_tags()
        uslt = USLT(encoding=Encoding.UTF8, lang=lang, desc='Lyrics', text=lyrics)
        audio.tags.add(uslt)
        audio.save()
    except Exception as e:
        print(f"Error embedding lyrics: {e}")


def safe_extract_info(ydl, url, private_videos, video_id):
    """
    Fetch info safely. Returns None if video is private/unavailable.
    """
    try:
        return ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as e:
        err_msg = str(e).lower()
        if 'private video' in err_msg:
            print(f"Skipping private video: {video_id}")
            private_videos.add(video_id)
            dump(list(private_videos), PRIVATE_VIDEOS_FILE)
        else:
            print(f"Error fetching info for {video_id}: {e}")
        return None


def download_yt_dlp(url, loc, format, video_id, author_name, author_id, title):
    if not os.path.exists(loc):
        os.makedirs(loc)

    renamed_files = []

    ydl_opts = {
        'outtmpl': {'default': f'{loc}/%(title)s.%(ext)s'},
        'quiet': True,
        'noprogress': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'format': 'bestaudio/best' if format in ['mp3', 'wav'] else 'bestvideo+bestaudio/best',
        'postprocessor_args': [
            '-metadata', 'album=Private',
            '-metadata', f'artist={author_name}',
            '-metadata', f'comment=Video ID : {video_id}\nAuthor ID : {author_id}\nAuthor Name : {author_name}'
        ],
        'add_metadata': True,
        'embed_metadata': True,
        'postprocessors': [{'key': 'FFmpegMetadata'}]
    }

    if format in ['mp3', 'wav']:
        ydl_opts['postprocessors'].insert(0, {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format,
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            base = sanitize_filename(os.path.splitext(title)[0])
            new_filename = get_unique_filename(loc, base, f".{format}", video_id)
            ydl.params['outtmpl']['default'] = os.path.join(loc, os.path.splitext(new_filename)[0] + '.%(ext)s')
            ydl.download([url])

        final_filename = f"{os.path.splitext(new_filename)[0]}.{format}"
        final_path = os.path.join(loc, final_filename)

        if os.path.exists(final_path) and final_filename != f"{base}.{format}":
            renamed_files.append(final_filename)

        return True, renamed_files, final_path

    except yt_dlp.utils.DownloadError as e:
        if "private" in str(e).lower():
            return False, "Private video", None
        return False, str(e), None
    except Exception as e:
        return False, str(e), None



def download_playlist(loc, format):
    ids = load(VIDEOS_TO_DOWNLOAD_FILE) or []
    if Path(PRIVATE_VIDEOS_FILE).exists():
        private_videos = set(load(PRIVATE_VIDEOS_FILE))
    else:
        private_videos = set()
    total_videos = len(ids)
    error_downloaded = {}
    all_renamed_files = []

    progress_count = 1
    idx = 0

    while idx < len(ids):
        video_id = ids[idx]
        url = f"https://youtube.com/watch?v={video_id}"

        # Skip known private videos
        if video_id in private_videos:
            print(f"{progress_count}/{total_videos} Skipping private video: {video_id}")
            idx += 1
            progress_count += 1
            continue

        # Extract info
        with yt_dlp.YoutubeDL({'quiet': True,'no_warnings': True,'ignoreerrors': True,'noprogress': True}) as ydl:
            print(f"{progress_count}/{total_videos} Fetching video infos: {video_id}",end="")
            info = safe_extract_info(ydl, url, private_videos, video_id)
            if not info:
                continue

            title = info.get('title', 'Unknown')
            author_name = info.get('uploader', 'N/A')
            author_id = info.get('uploader_id', 'N/A')

        # Download video/audio
        print(f"\r{progress_count}/{total_videos} Downloading: {title}                     ",end="",flush=True)
        success, renamed_files, file_path = download_yt_dlp(url, loc, format, video_id, author_name, author_id, title)

        if success and file_path:
            print(f"\r{progress_count}/{total_videos} Getting lyrics: {title}",end="")
            lyrics = get_lyrics_from_genius(f"{title} {author_name}")
            if lyrics:
                print(f"\r{progress_count}/{total_videos} Embedding lyrics: {title}",end="")
                embed_lyrics_into_mp3(file_path, lyrics)

            print(f"\r{progress_count}/{total_videos} Downloaded: {title} | {'Lyrics Found' if lyrics else 'No lyrics'}")

            # Update timestamp
            now = time.time()
            os.utime(file_path, (now, now))

            all_renamed_files.extend(renamed_files)
            ids.pop(idx)
            dump(ids, VIDEOS_TO_DOWNLOAD_FILE)
        else:
            if renamed_files == "Private video" or success is False and file_path is None:
                private_videos.add(video_id)
                dump(list(private_videos), PRIVATE_VIDEOS_FILE)
                print(f"{progress_count}/{total_videos} Marked as private: {video_id}")
            else:
                error_downloaded[video_id] = renamed_files or "Unknown error"

            idx += 1

        progress_count += 1

    # Save errors if any
    if error_downloaded:
        dump(error_downloaded, ERROR_DOWNLOADED_FILE)
        print(f"\nSome videos could not be downloaded. See {ERROR_DOWNLOADED_FILE} for details.")

    # Print renamed files
    if all_renamed_files:
        print(f"\nNumber of renamed files: {len(all_renamed_files)}")
        for file in all_renamed_files:
            print(file)

    os.remove(VIDEOS_TO_DOWNLOAD_FILE)