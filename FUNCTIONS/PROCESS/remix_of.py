from sqlite3 import Connection, Cursor
from difflib import SequenceMatcher
import time


from FUNCTIONS.clean_song_query import clean_song_query
from FUNCTIONS.sql_requests import update_video_db
from FUNCTIONS.HELPERS.fprint import fprint
from CONSTANTS import REMIX_CONFIDENCE_THRESHOLD


from FUNCTIONS.HELPERS.logger import setup_logger
logger = setup_logger(__name__)


def process_remix_of_for_video(
    video_id: str,
    progress_prefix: str,
    remix_of: str | None,
    recompute_remix_of: bool,
    test_run: bool,
    cur: Cursor,
    conn: Connection
) -> float:
    """
    Try to detect if a given video is a remix of another track.
    If recompute_remix_of is True, the remix_of field is re-evaluated.
    """

    start_processing: float = time.time()

    # Recompute only if requested and remix_of candidate exists
    if remix_of is not None and recompute_remix_of:
        # Clean and normalize the given remix_of string
        cleaned_remix_title = clean_song_query(remix_of)

        # Fetch all distinct titles from the database
        _ = cur.execute("SELECT video_id, title FROM videos WHERE video_id != ?", (video_id,))
        candidates: list[tuple[str, str]] = cur.fetchall()

        best_match: tuple[str, float] | None = None

        for other_id, other_title in candidates:
            cleaned_other = clean_song_query(other_title)

            # Compute similarity ratio
            similarity = SequenceMatcher(None, cleaned_remix_title, cleaned_other).ratio()

            if best_match is None or similarity > best_match[1]:
                best_match = (other_id, similarity)

        # If a strong enough match is found, set remix_of
        if best_match and best_match[1] >= REMIX_CONFIDENCE_THRESHOLD:
            match_id, confidence = best_match
            update_video_db(video_id,{"remix_of": match_id,"confidence": confidence, "recompute_remix_of": False}, cur, conn, test_run=test_run)
            logger.info(f"[Remix Of] '{remix_of}' matched '{match_id}' with confidence {confidence:.2f}, updated remix_of")
            fprint(progress_prefix,f"[Remix Of] '{remix_of}' matched '{match_id}' with confidence {confidence:.2f}, updated remix_of")
        else:
            logger.info(f"[Remix Of] No confident match for '{remix_of}' (best={best_match})")
            fprint(progress_prefix,f"[Remix Of] No confident match for '{remix_of}' (best={best_match})")

    return time.time() - start_processing