import yt_dlp
import os
import re
import time
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, USLT, Encoding
from CONSTANTS import ERROR_DOWNLOADED_FILE, UNAVAILABLE_VIDEOS_FILE
from FUNCTIONS.extract_lyrics import get_lyrics_from_syncedlyrics
from FUNCTIONS.fileops import load, dump
from FUNCTIONS.get_album_and_tags import get_album
from pathlib import Path


# Custom logger to silence yt-dlp completely
class QuietLogger:
    def debug(self, msg):   pass
    def warning(self, msg): pass
    def error(self, msg):   pass

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
            # print(f"Skipping private video: {video_id}")
            private_videos.add(video_id)
            dump(list(private_videos), UNAVAILABLE_VIDEOS_FILE)
        else:
            print(f"Error fetching info for {video_id}: {e}")
        return None


def download_yt_dlp(url, loc, format, add_album, video_id, author_name, author_id, title, showed_title, progress_count, total_videos):
    if not os.path.exists(loc):
        os.makedirs(loc)

    renamed_files = []

    def progress_hook(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '').strip()
            speed = d.get('_speed_str', 'N/A').strip()
            eta = d.get('_eta_str', 'N/A').strip()
            print(f"\r{progress_count}/{total_videos} | Downloading: {showed_title} |  {percent} at {speed}, ETA: {eta}",end='')
        elif d['status'] == 'finished':
            print(f"\r{progress_count}/{total_videos} | Post-processing: {showed_title}                                                     ", end='')


    ydl_opts = {
        'outtmpl': {'default': f'{loc}/%(title)s.%(ext)s'},
        'quiet': True,
        'noprogress': True,
        'no_warnings': True,
        'ignoreerrors' : True,
        'logger' : QuietLogger(),
        'format': 'bestaudio/best' if format in ['mp3', 'wav'] else 'bestvideo+bestaudio/best',
        'postprocessor_args': [
            '-metadata', f'artist={author_name}',
            '-metadata', f'comment=Video ID : {video_id}\nAuthor ID : {author_id}\nAuthor Name : {author_name}'
        ],
        'add_metadata': True,
        'embed_metadata': True,
        'postprocessors': [{'key': 'FFmpegMetadata'}],
        'progress_hooks' : [progress_hook]
    }

    if add_album:
        album_name = get_album(title, author_name)
        ydl_opts['postprocessor_args'].extend(['-metadata', f'album={album_name}'])


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



def download_playlist(file,loc, format,get_lyrics=True, add_album=True):
    ids = load(file)
    if Path(UNAVAILABLE_VIDEOS_FILE).exists():
        unavailable_videos = set(load(UNAVAILABLE_VIDEOS_FILE))
    else:
        unavailable_videos = set()
    total_videos = len(ids)
    error_downloaded = {}
    all_renamed_files = []

    progress_count = 1
    idx = 0

    while idx < len(ids):
        video_id = ids[idx]
        url = f"https://youtube.com/watch?v={video_id}"

        # Skip known unavailable videos
        if video_id in unavailable_videos:
            print(f"{progress_count}/{total_videos} | Skipping unavailable video: {video_id}")
            ids.remove(video_id)
            dump(ids,file)
            idx += 1
            progress_count += 1
            continue

        # Extract info
        with yt_dlp.YoutubeDL({'quiet': True,'no_warnings': True,'noprogress': True,'ignoreerrors' : True,'logger': QuietLogger()}) as ydl:
            print(f"{progress_count}/{total_videos} | Fetching video infos: {video_id}",end="",flush=True)
            info = safe_extract_info(ydl, url, unavailable_videos, video_id)
            if not info:
                print(f"\r{progress_count}/{total_videos} | Skipping unavailable video: {video_id}")
                unavailable_videos.add(video_id)
                dump(list(unavailable_videos),UNAVAILABLE_VIDEOS_FILE)
                ids.remove(video_id)
                dump(ids,file)
                idx += 1
                continue

            title = info.get('title', 'Unknown')
            author_name = info.get('uploader', 'N/A')
            author_id = info.get('uploader_id', 'N/A')

            show_title = title[:100] if len(title) > 100 else title

            # Download video/audio
            success, renamed_files, file_path = download_yt_dlp(url,loc,format, add_album, video_id,author_name,author_id,title,show_title,progress_count,total_videos)

            lyrics = False
            
            if success and file_path:
                if get_lyrics:
                    print(f"\r{progress_count}/{total_videos} | Getting lyrics",end="")
                    lyrics, reason, query = get_lyrics_from_syncedlyrics(f"{title} {author_name}")
                    if lyrics:
                        print(f"\r{progress_count}/{total_videos} | Embedding lyrics: {show_title}                                                             ",end="")
                        embed_lyrics_into_mp3(file_path, lyrics)

                    print(f"\r{progress_count}/{total_videos} | Downloaded: {show_title}" + " "* (100 - len(show_title)) + f"{f'| 📃 Lyrics Found (query: {query})' if lyrics else f'| No Lyrics ({reason})'}")

                # Update timestamp
                now = time.time()
                os.utime(file_path, (now, now))

                all_renamed_files.extend(renamed_files)
                ids.pop(idx)
                dump(ids, file)
            else:
                if renamed_files == "Private video" or success is False and file_path is None:
                    unavailable_videos.add(video_id)
                    dump(list(unavailable_videos), UNAVAILABLE_VIDEOS_FILE)
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

    os.remove(file)