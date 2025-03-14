import hashlib, logging, os
from organiser.section2_configuration import CONFIG

try:
    import xxhash
    XXHASH_AVAILABLE = True
except ImportError:
    XXHASH_AVAILABLE = False

def worker_hash_file(file_path, algo, skip_size):
    try:
        size = os.path.getsize(file_path)
        if skip_size > 0 and size > skip_size:
            return (file_path, None, ("SkipLargeFile", f"Size {size} > {skip_size}"))
        if algo.lower() == 'xxhash' and XXHASH_AVAILABLE:
            h = xxhash.xxh64()
        elif algo.lower() == 'md5':
            h = hashlib.md5()
        elif algo.lower() == 'sha256':
            h = hashlib.sha256()
        else:
            logging.debug("Fallback to sha256.")
            h = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        return (file_path, h.hexdigest(), None)
    except Exception as ex:
        logging.error(f"Error hashing {file_path}: {ex}")
        return (file_path, None, ("HashError", str(ex)))

def select_best_file(file_group):
    if not file_group:
        return None
    best = None
    best_mtime = -1
    best_size = -1
    for f in file_group:
        try:
            st = os.stat(f)
            mtime = st.st_mtime
            size = st.st_size
            # Choose the file with the latest modification time;
            # if there's a tie in mtime, choose the larger file.
            if mtime > best_mtime:
                best = f
                best_mtime = mtime
                best_size = size
            elif abs(mtime - best_mtime) < 0.001:
                if size > best_size:
                    best = f
                    best_size = size
        except Exception as ex:
            logging.error(f"Error selecting best file for {f}: {ex}")
    return best

def compare_file_size(file1, file2):
    try:
        size1 = os.path.getsize(file1)
        size2 = os.path.getsize(file2)
        return size1 == size2
    except Exception as e:
        logging.error(f"Error getting file size: {e}")
        return False