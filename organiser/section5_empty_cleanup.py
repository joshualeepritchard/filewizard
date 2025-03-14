import os, shutil, logging
from organiser.section3_helpers import is_hidden, ensure_dir_exists, to_be_deleted_dir

def is_folder_transitively_empty(folder):
    """
    Checks if a folder is transitively empty, meaning it contains no files
    and all subfolders are also transitively empty.
    """
    try:
        for entry in os.scandir(folder):
            path = os.path.join(folder, entry.name)
            if entry.is_file() and not is_hidden(path):
                return False  # Found a visible file, so it's not empty
            if entry.is_dir():
                if not is_folder_transitively_empty(path):
                    return False  # Found a non-empty subfolder
        return True  # No visible files and all subfolders are empty
    except Exception as ex:
        logging.error(f"Error checking if folder {folder} is empty: {ex}")
        return False

def sweep_empty_folders(target_folder, tbd_empty_folder):
    moved_count = 0
    for root, dirs, files in os.walk(target_folder, topdown=False):
        for d in dirs:
            d_path = os.path.join(root, d)
            if os.path.exists(d_path) and is_folder_transitively_empty(d_path):
                final_path = os.path.join(tbd_empty_folder, os.path.basename(d_path))
                ensure_dir_exists(tbd_empty_folder)
                try:
                    shutil.move(d_path, final_path)
                    moved_count += 1
                    logging.info(f"Swept empty folder: {d_path} -> {final_path}")
                except Exception as ex:
                    logging.error(f"Error moving empty folder {d_path}: {ex}")
    return moved_count

def move_empty_folders_single_pass(organised_folder, target_folders):
    tbd = to_be_deleted_dir(organised_folder)
    tbd_empty = os.path.join(tbd, "empty folders")
    ensure_dir_exists(tbd_empty)
    total_moved_count = 0
    while True:
        changes = False
        for folder in target_folders:
            if os.path.isdir(folder):
                moved = sweep_empty_folders(folder, tbd_empty)
                if moved > 0:
                    total_moved_count += moved
                    changes = True
        logging.info(f"Empty folder sweep: moved {total_moved_count} empty folders")
        if not changes:
            break
    return total_moved_count