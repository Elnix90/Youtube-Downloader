# Migration Guide to V3

## Overview

In **versions prior to V3**, the main entry point function (`main_list_process`) accepted a long list of arguments. You were expected to pass them directly in code or via function calls.

In **V3**, this design has changed.

* **All processing parameters are now defined in `config.toml`.**
* The main function no longer accepts individual arguments — instead, it automatically loads defaults from the configuration file.
* This makes your workflow simpler, avoids duplication, and keeps all options centralized in one place.

---

## Before (V2 and earlier)

```python
from main import main_list_process

main_list_process(
    playlist_id="LL",
    embed_metadata=True,
    add_album=True,
    recompute_album=True,
    get_lyrics=True,
    recompute_lyrics=False,
    get_thumbnail=True,
    thumbnail_format="pad",
    recompute_thumbnails=False,
    use_sponsorblock=True,
    categories=["music_offtopic", "sponsor", "intro", "outro"],
    add_tags=True,
    sep=" ~ ",
    start_def="[",
    end_def="]",
    tag_sep=",",
    recompute_tags=True,
    retry_unavailable=False,
    retry_private=False,
    info=True,
    error=True,
    test_run=False,
    clean=False,
    remove_no_longer_in_playlist=False,
    remove_malformatted=True,
    create_db_if_not=True,
    add_folder_files_not_in_list=True,
)
```

---

## After (V3 and later)

Now you only need to call:

```python
from main import main_list_process

main_list_process()
```

All the settings are taken from **`config.toml`**.
Example:

```toml
[processing]
playlist_id = "LL"
embed_metadata = true
add_album = true
recompute_album = true

get_lyrics = true
recompute_lyrics = false

get_thumbnail = true
thumbnail_format = "pad"
recompute_thumbnails = false

use_sponsorblock = true
sponsorblock_categories = ["music_offtopic", "sponsor", "intro", "outro"]

add_tags = true
tag_separator = " ~ "
tag_start_delimiter = "["
tag_end_delimiter = "]"
tag_inner_separator = ","
recompute_tags = true

retry_unavailable = false
retry_private = false

info = true
error = true
test_run = false

clean = false
remove_no_longer_in_playlist = false
remove_malformatted = true
create_db_if_not = true
add_folder_files_not_in_list = true
```

---

## Migration Steps

 * Just clone the new version and edit the default config file that come with it to your preferences
---

## Benefits of V3

* ✅ Centralized configuration in one file
* ✅ Cleaner and shorter Python code
* ✅ Easier to update defaults without editing function calls
* ✅ Reduces risk of inconsistent arguments across scripts
