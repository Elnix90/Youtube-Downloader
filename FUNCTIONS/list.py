from __future__ import annotations
from pathlib import Path
import os
from typing import Any, Dict, Set, List, Optional

from dotenv import load_dotenv
from FUNCTIONS.create_videos_to_download_file import clean_download_directory, extract_existing_video_ids
from FUNCTIONS.fileops import load, dump
from FUNCTIONS.tags_system import set_tags,compute_tags,get_tags
from FUNCTIONS.metadata import write_metadata_tag,get_metadata_tag
from CONSTANTS import DOWNLOAD_PATH



load_dotenv()
list_file = Path(os.getenv("musicpath", ""))
if not list_file.exists():
    raise Exception("LIST path not set or file does not exist. Please set one in the .env file. (musicpath=your/path/to/music.json)")



def loadlist() -> Dict[str, Dict[str, Any]]:
    try:
        return load(list_file)
    except Exception as e:
        raise FileNotFoundError(f"[Loadlist] The datalist file does NOT exist or cannot be loaded: {e}")



def dumplist(data: Dict[str, Dict[str, Any]], errors: bool = True) -> bool:
    try:
        dump(data, list_file)
        return True
    except Exception as e:
        if errors: print(f"[Dumplist] Error while updating ({id}) in the datalist: {e}")
        return False



class Process_list:

    datalist: Dict[str, Dict[str, Any]]

    def __init__(self) -> None:
        pass

    def add_new_ids_to_list(
            self,
            video_id_file: Path,
            verbose: bool = True,
            errors: bool = True
    ) -> None:
        """
        Fetch the datalist of ids to add those who aren't in the datalist
        """
        datalist = loadlist()
        video_ids: Set[str] = set()
        try:
            video_ids = set(load(video_id_file))
        except Exception as e:
            if errors: print(f"[Adding ids] Error while loading the videos id file ({video_id_file}): {e}")
        to_add: set[str] = video_ids - set(datalist.keys())
        added_ids: int = 0

        for video_id in to_add:
            datalist[video_id] = {
                "tags": [],
                "recompute_tags": True,
                "status": "unknown"
            }
            added_ids += 1
            if verbose: print(f"\r[Adding ids] Added {added_ids} ids to the datalist", end="")

        if verbose and not to_add: print("[Adding ids] All ids are in the datalist")
        elif verbose: print()
        dumplist(datalist)



    def remove_video_not_in_liked(
            self,
            video_id_file: Path,
            info: bool = True,
            verbose: bool = True,
            errors: bool = True
            ) -> None: # Not used for now
        """
        remove id from list if not in liked list
        """
        datalist = loadlist()
        video_ids: Set[str] = set(load(video_id_file))
        list_ids: Set[str] = set(datalist.keys())

        not_in_video_ids: Set[str] = list_ids - video_ids

        removed_ids: int = 0
        removed_files: int = 0
        for id in not_in_video_ids:
            filename: str = datalist[id].get('filename',"")
            if filename:
                try:
                    os.remove(DOWNLOAD_PATH / filename)
                    removed_files += 1
                except OSError as e:
                    if errors:
                        print(f"[Removing Ids] Error while removing {filename} : {e}")
                except Exception as e:
                    if verbose: print(f"[Removing Ids] Unknown error while deleting {filename}: {e}")

            del datalist[id]
            removed_ids += 1
            if info: print(f"\r[Removing Ids] Removed {removed_ids} from list",end="", flush=True)

        if verbose and not not_in_video_ids:
            if not_in_video_ids:
                print(f"\n - {removed_files} removed from the download dir")
            else:
                print("\r[Removing Ids] No video to remove from the datalist: all present in the video file")
        dumplist(datalist)



    def get_videos_to_download(
            self,
            vids_to_download_path: Path,
            retry_unavailable: bool = False,
            info: bool = True,
            verbose: bool = True,
            errors: bool = True
        ) -> None:
        """
        Check the download directory for existing videos and update the datalist accordingly.
        If a video is already downloaded, it will be marked as such in the datalist.
        If a video is not downloaded, it will be added to the download list.
        """
        datalist = loadlist()
        clean_download_directory(DOWNLOAD_PATH,verbose=verbose)
        ids_present_in_down_dir: Dict[str, Dict[str, Any]] = extract_existing_video_ids(DOWNLOAD_PATH)

        required_keys = [
            "id", "title", "thumbnail", "description", "channel_id", "channel_url",
            "duration", "uploader", "uploader_id", "uploader_url",
            "upload_date", "duration_string", "filename"
        ]

        videos_to_download: Set[str] = set()
        valid_video_count: int = 0
        checked_files: int = 0
        unavailable_videos: int = 0        

        if verbose: print("Checking files in the download directory...", end="")

        for video_id, data in datalist.items():
            
            if video_id in ids_present_in_down_dir: # Video already downloaded and readable
                filename: str = ids_present_in_down_dir[video_id].get('filename', "")
                if not filename or not (DOWNLOAD_PATH / filename).exists(): # Just in case cause the video should be readable with filaname in it cause extract_ids did its job
                    if errors: print(f"Error while reading the filename for {video_id}")
                    videos_to_download.add(video_id)
                else: # Verify that all the keys are in the data
                    metadata = ids_present_in_down_dir.get(video_id, {})
                    if all(key in metadata for key in required_keys):
                        # Do not overwrite the data in the datalist as it is more important but add inexisting keys to the datalist
                        for key in metadata.keys():
                            if key not in data:
                                data[key] = metadata[key]
                        datalist[video_id]["status"] = "downloaded"
                        valid_video_count += 1
                    else: # All keys aren't in the metadata,
                        fusion = metadata | data
                        if all(key in fusion for key in required_keys): # Together the two dicts have enough data, so do not re-download
                            valid_video_count += 1
                            datalist[video_id]["status"] = "downloaded"
                            data[video_id] = fusion
                        else:
                            # Need to download cause all the required keys aren't in the fusion of the metadata and the datalist data
                            videos_to_download.add(video_id)

            else: # Need to download for sure cause video_id not present to the download_dir
                status: str = data.get('status','unknown')
                if status == "unavailable" and not retry_unavailable:
                    unavailable_videos += 1
                else:
                    videos_to_download.add(video_id)
 
            checked_files += 1

            if info: print(f"\r[Checking videos] Processed {checked_files} / {len(datalist)} ids in the datalist",end="", flush=True)

        if verbose:
            print()
            if valid_video_count:
                print(f" - {valid_video_count} valid videos correctly formatted")
            if videos_to_download:
                print(f" - {len(videos_to_download)} videos to download")
            if unavailable_videos:
                print(f" - {unavailable_videos} Unavailable videos {'(pass retry_unavailable=True to try download them again)' if not retry_unavailable else ''}")
        else: print()
        dumplist(datalist)

        if videos_to_download:
            dump(list(videos_to_download), vids_to_download_path)



    def update(
            self,
            id: str,
            data: Dict[str, Any],
            verbose: bool = False,
            errors: bool = True
    ) -> None:
        """
        Update the datalist with new data for a specific video ID.
        If the ID already exists, merge the new data with the existing data.
        Existing keys will be overwritten with new values.
        """
        datalist = loadlist()
        if id in datalist.keys():
            merged_data = datalist[id] | data
            datalist[id] = merged_data
            sucess: bool = dumplist(datalist)

            if verbose and sucess:
                print(f"[Updating list] Id ({id}) updated sucessfully")
            elif errors and not sucess:
                print(f"[Updating list] Update of id ({id}) failed")
            
        else:
            if verbose: print(f"[Updating list] Id ({id}) isn't present in the datalist")



    def add_tags(
            self,
            recompute_tags: bool = True,
            info: bool = True,
            verbose: bool = True,
            errors: bool = True
            ) -> None:
        """
        Add tags to the files in the download directory based on the datalist.
        """
        datalist = loadlist()
        tags_added: int = 0
        ids_processed: int = 0
        file_added: int = 0
        for video_id,video_data in datalist.items():
            if 'filename' in video_data:
                
                filepath: Path = DOWNLOAD_PATH / video_data["filename"]

                old_tags: Set[str] = get_tags(filepath)
                data_tags: Set[str] = set(video_data.get("tags",{}))
                computed_tags: Set[str] = set()
                title: str = video_data.get('title',"")
                uploader: str = video_data.get('uploader',"")
                new_uploader: Optional[str] = None

                file_order_to_recompute: Optional[bool] = video_data.get("recompute_tags")
                if file_order_to_recompute:
                    if title and uploader and recompute_tags:
                        computed_tags = compute_tags(title,uploader)
                elif file_order_to_recompute == None:
                    datalist[video_id]['recompute_tags'] = file_order_to_recompute # If undefined

                tags: Set[str] = data_tags.union(computed_tags)

                try:
                    new_uploader = set_tags(filepath, tags)
                    if new_uploader:
                        datalist[video_id]["uploader"] = new_uploader
                        datalist[video_id]["tags"] = list(tags)
                        tags_added += len(tags - old_tags) # only count new tags, not the already present ones
                        file_added += 1
                except Exception as e:
                    if errors: print(f"[Adding tags] Error while setting tags for {filepath}: {e}")
                
            ids_processed += 1
            if info: print(f"\r[Adding tags] Processed {ids_processed} / {len(datalist)} ids in the datalist", end="", flush=True)
        if verbose and tags_added: print(f"{f'\n - {tags_added} new tags added on {file_added} videos' if tags_added else ''}")
        else: print(" -> Nothing to add")
        dumplist(datalist)



    def update_metadata(
            self,
            info: bool = True,
            verbose: bool = True,
            errors: bool = True
        ) -> None:
        """
        Write metadata contained in the datalist into the files.
        """
        datalist = loadlist()
        metadata_updated: int = 0
        ids_processed: int = 0
        for data in datalist.values():
            filename: str = data.get("filename", "")
            if filename:
                filepath: Path = DOWNLOAD_PATH / filename
                if filepath.exists():
                    if get_metadata_tag(filepath)[0] != data:
                        if not write_metadata_tag(filepath, data):
                            if errors: print(f"\n[Updating metadata] Error while updating metadata of {filepath}")
                        metadata_updated += 1
            ids_processed += 1
            if info: print(f"\r[Upating metadata] Processed {ids_processed} / {len(datalist)} ids in the datalist", end="", flush=True)
        if verbose and metadata_updated: print(f"{f'\n - {metadata_updated} ids updated' if metadata_updated else ''}")
        else: print(" -> Nothing to update")



    def show_final_stats(self,duration: Optional[str]):
        datalist = loadlist()
        clean_download_directory(DOWNLOAD_PATH,verbose=False)
        ids_present_in_down_dir: Dict[str, Dict[str, Any]] = extract_existing_video_ids(DOWNLOAD_PATH)

        list_without_private: Dict[str, Dict[str, Any]] = {}

        for video_id, data in datalist.items():
            status: str = data.get("status","unknown")
            if status == "downloaded":
                list_without_private[video_id] = data


        not_in_dir: Set[str] = set(list_without_private.keys()) - set(ids_present_in_down_dir.keys())
        not_in_list: Set[str] = set(ids_present_in_down_dir.keys()) - set(list_without_private.keys())

        final_stats: List[str] = []


        if not not_in_dir and not not_in_list:
            final_stats.append(" ✅ The datalist and the download dir have been sucessfully synchronized")
        else:
            if not not_in_dir:
                final_stats.append(f" - {len(list_without_private)} ids are in the datalist and correctly downloaded")
            else:
                final_stats.append(f" - {len(datalist) - len(list_without_private)} ids have not been downloaded, marked as unavailable")

            if not not_in_list:
                final_stats.append(f" - All downloaded files are in the datalist and corectly formated")
            else:
                final_stats.append(f" - {len(not_in_list)} correctly formatted files are in the download directory but not in the datalist")


        print(f"""[TOTAL]:
 - {len(datalist)} total videos are in the datalist
 - {len(ids_present_in_down_dir)} total videos are in download directory""")
        print("\n".join(final_stats))

        if duration:
            print(f"Total download time : {duration}")