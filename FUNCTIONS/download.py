import yt_dlp
import os
import re
from CONSTANTS import VIDEOS_TO_DOWNLOAD_FILE, ERROR_DOWNLOADED_FILE
from FUNCTIONS.fileops import load, dump

def sanitize_filename(filename):
    """
    Remove forbidden characters and trailing dots/spaces for safe filenames.
    """
    # Remove forbidden characters for most filesystems
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    # Remove trailing dots and spaces
    filename = filename.rstrip('. ')
    return filename

def get_unique_filename(loc, base, ext, video_id):
    """
    Ensure the filename is unique in the directory and matches the video ID in metadata.
    """
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

def download_yt_dlp(url, loc, format, video_id, author_name, author_id):
    if not os.path.exists(loc):
        os.makedirs(loc)

    renamed_files = []

    # Use yt-dlp's B specifier for safe filenames, and limit length
    ydl_opts = {
        'outtmpl': {'default': f'{loc}/%(title).150B.%(ext)s'},
        'quiet': True,
        'noprogress': True,
        'format': f'bestaudio/best' if format in ['mp3', 'wav'] else 'bestvideo+bestaudio/best',
        'postprocessor_args': [
            '-metadata', 'album=Private',
            '-metadata', f'artist={author_name}',
            '-metadata', f'comment=Video ID : {video_id}\nAuthor ID : {author_id}\nAuthor Name : {author_name}'
        ],
        'add_metadata': True,
        'embed_metadata': True,
        'postprocessors': [{
            'key': 'FFmpegMetadata'
        }]
    }

    if format in ['mp3', 'wav']:
        ydl_opts['postprocessors'].insert(0, {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format,
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # Sanitize base filename for safety
            base = sanitize_filename(os.path.splitext(info['title'])[0])
            new_filename = get_unique_filename(loc, base, f".{format}", video_id)
            # Update output template for this download
            ydl.params['outtmpl']['default'] = os.path.join(loc, os.path.splitext(new_filename)[0] + '.%(ext)s')
            ydl.download([url])

        final_filename = f"{os.path.splitext(new_filename)[0]}.{format}"
        if os.path.exists(os.path.join(loc, final_filename)):
            if final_filename != f"{base}.{format}":
                renamed_files.append(final_filename)
        else:
            print(f"Warning: {final_filename} was not created")

        return True, renamed_files

    except yt_dlp.utils.DownloadError as e:
        print(f"\nError downloading {url}: {e}")
        return False, str(e)
    except Exception as e:
        print(f"\nUnexpected error downloading {url}: {e}")
        return False, str(e)

def download_playlist(loc, format):
    print("Started Downloading...")

    ids = load(VIDEOS_TO_DOWNLOAD_FILE)
    total_videos = len(ids)
    error_downloaded = {}
    all_renamed_files = []

    idx = 0
    progress_count = 1  # This counts how many downloads have been attempted

    while idx < len(ids):
        video_id = ids[idx]
        url = f"https://youtube.com/watch?v={video_id}"

        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown')
                author_name = info.get('uploader', 'N/A')
                author_id = info.get('uploader_id', 'N/A')
        except Exception as e:
            error_msg = str(e)
            print(f"\nError fetching info for video {video_id}: {error_msg}")
            error_downloaded[video_id] = error_msg
            idx += 1
            progress_count += 1
            continue

        print(f"Downloading {progress_count}/{total_videos}: {title}")

        download_result, result_info = download_yt_dlp(url, loc, format, video_id, author_name, author_id)
        if download_result:
            all_renamed_files.extend(result_info)
            # Only remove from list if download succeeded
            ids.pop(idx)
            dump(ids, VIDEOS_TO_DOWNLOAD_FILE)
        else:
            error_msg = result_info
            print(f"Download error for {video_id}: {error_msg}")
            error_downloaded[video_id] = error_msg
            idx += 1

        progress_count += 1  # Always increment after an attempt

    if error_downloaded:
        dump(error_downloaded, ERROR_DOWNLOADED_FILE)
        print(f"\nSome videos could not be downloaded. See {ERROR_DOWNLOADED_FILE} for details.")

    if all_renamed_files:
        print(f"\nNumber of renamed files: {len(all_renamed_files)}")
        for file in all_renamed_files:
            print(file)
