from CONSTANTS import *
from FUNCTIONS.fileops import load, dump
import webbrowser
import yt_dlp
import os

def get_video_metadata(video_id):
    """Get metadata using yt-dlp for unavailable videos"""
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(f'https://youtube.com/watch?v={video_id}', download=False)
            return {
                'title': info.get('title', 'Title unavailable'),
                'channel': info.get('uploader', 'Channel unavailable'),
                'duration': info.get('duration', 'Duration unknown')
            }
    except Exception as e:
        return {'error': str(e)}

def inteligent_deleting(FILE,youtube):
    video_ids = load(FILE)
    current_index = 0
    delete_all = False

    while current_index < len(video_ids):
        if delete_all:
            action = 'd'
        else:
            video_id = video_ids[current_index]
            
            # Try to get official metadata first
            try:
                request = youtube.videos().list(
                    part="snippet,status",
                    id=video_id
                )
                response = request.execute()
                metadata = response.get('items', [{}])[0].get('snippet', {})
            except:
                metadata = get_video_metadata(video_id)

            print(f"\nVideo ID: {video_id}")
            print(f"Title: {metadata.get('title', 'No title available')}")
            print(f"Channel: {metadata.get('channel', metadata.get('channelTitle', 'Unknown'))}")
            print(f"Duration: {metadata.get('duration', metadata.get('duration', 'Unknown'))} seconds")

            action = input("What do you want to do? (d/n/p/o/all/q): ").lower()

        if action == 'q':
            break
        elif action == 'd':
            try:
                youtube.videos().delete(id=video_id).execute()
                print(f"Deleted video {video_id}")
                video_ids.pop(current_index)
            except Exception as e:
                print(f"Error deleting {video_id}: {str(e)}")
                current_index += 1
        elif action == 'n':
            current_index += 1
        elif action == 'p' and current_index > 0:
            current_index -= 1
        elif action == 'o':
            webbrowser.open(f"https://youtube.com/watch?v={video_id}")
        elif action == 'all':
            confirm = input("Are you sure you want to delete ALL remaining videos? (y/n): ").lower()
            if confirm == 'y':
                delete_all = True
            else:
                print("Canceled mass deletion")
        else:
            print("Invalid option")
            continue

        # Update the JSON file after each operation
        dump(video_ids, FILE)

    remaining = len(video_ids)

    if remaining>0:
        print("\nOperation completed. Remaining videos:", len(video_ids))
    else:
        print("Operaton completed, deleting errors file")
        os.remove(FILE)

