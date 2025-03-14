import os, shutil, logging, ctypes

def ensure_dir_exists(path):
    try:
        os.makedirs(path, exist_ok=True)
        logging.debug(f"Ensured directory exists: {path}")
    except Exception as ex:
        logging.error(f"Error creating directory {path}: {ex}")
    return path

def duplicates_dir(organised_folder):
    return os.path.join(organised_folder, "Duplicates")

def categorised_dir(organised_folder):
    return os.path.join(organised_folder, "Categorised")

def to_be_deleted_dir(organised_folder):
    return os.path.join(organised_folder, "To Be Deleted")

def move_with_collision(src, dest):
    base, ext = os.path.splitext(dest)
    counter = 1
    final_dest = dest
    while os.path.exists(final_dest):
        final_dest = f"{base} ({counter}){ext}"
        counter += 1
    shutil.move(src, final_dest)
    logging.debug(f"Moved '{src}' -> '{final_dest}'")

def is_hidden(filepath):
    FILE_ATTRIBUTE_HIDDEN = 0x02
    FILE_ATTRIBUTE_SYSTEM = 0x04
    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(filepath))
        if attrs == -1:
            return False
        return bool(attrs & (FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM))
    except Exception as ex:
        logging.error(f"Error checking hidden attribute for {filepath}: {ex}")
        return False