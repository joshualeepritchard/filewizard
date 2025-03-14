import time, logging, os, multiprocessing, re
from functools import partial
from PyQt5.QtCore import QThread, pyqtSignal
from organiser.section2_configuration import CONFIG
from organiser.section3_helpers import ensure_dir_exists, move_with_collision, duplicates_dir, to_be_deleted_dir, categorised_dir
from organiser.section4_hashing import worker_hash_file, select_best_file, compare_file_size
from organiser.section5_empty_cleanup import is_folder_transitively_empty, sweep_empty_folders, move_empty_folders_single_pass
from organiser.section6_categorisation import build_final_path_default


class ProcessingThread(QThread):
    """
    This thread processes files by hashing them to detect duplicates,
    then moving duplicates to the 'Duplicates' folder (or 'To Be Deleted'),
    and non-duplicates to the 'Categorised' folder.
    """
    done_signal = pyqtSignal(str, int, int)  # (status, duplicates, nonduplicates)
    progress_signal = pyqtSignal(int, int, float)
    progress_cat_signal = pyqtSignal(int, int)
    error_signal = pyqtSignal(str, str, str)

    def __init__(self, filepaths, algo, categories, skip_size, organised_folder, target_folders):
        super().__init__()
        self.filepaths = filepaths
        self.algo = algo
        self.categories = categories
        self.skip_size = skip_size
        self.organised_folder = organised_folder
        self.target_folders = target_folders
        self.stop_event = multiprocessing.Event()

        # We'll track duplicates for final summary
        self.duplicate_files_count = 0
        self.nonduplicate_files_count = 0

    def run(self):
        try:
            self._process_files()
        except Exception as ex:
            logging.error(f"ProcessingThread error: {ex}")
            self.done_signal.emit("aborted", 0, 0)

    def stop(self):
        self.stop_event.set()

    def _process_files(self):
        """
        Orchestrates the file processing workflow, including hashing, duplicate detection,
        categorization, and cleanup.
        """
        total_files = len(self.filepaths)

        # Prepare main directories
        cat_path = categorised_dir(self.organised_folder)
        dup_path = duplicates_dir(self.organised_folder)
        tbd_path = to_be_deleted_dir(self.organised_folder)
        ensure_dir_exists(cat_path)
        ensure_dir_exists(dup_path)
        ensure_dir_exists(tbd_path)
        hashes_in_dup = set()

        # Hash the destination folder
        dest_hashes = self.hash_folder(self.organised_folder)

        # Hash the source folder
        source_hashes = self.hash_files(self.filepaths)

        # Process files for duplicates and categorization
        processed_count = 0
        for filepath, file_hash in source_hashes.items():

            processed_count += 1

            if self.stop_event.is_set():
                self.done_signal.emit("aborted", 0, 0)
                return

            # Check for potential filename duplicates
            potential_duplicates = self.find_potential_duplicates([filepath])
            is_duplicate = False

            for file1, file2 in potential_duplicates:
                if compare_file_size(file1, file2):
                    # Process the filename duplicate and move it
                    self.process_filename_duplicate(file1, file2, cat_path, dup_path, tbd_path, hashes_in_dup, source_hashes)
                    is_duplicate = True
                    break  # Only process file pairs once

            if not is_duplicate:
                # Check against hashed files to see if it exists in the final destination
                dest_match = self.find_duplicate_in_hashes(file_hash,dest_hashes.copy())
                if dest_match is not None:
                    self.duplicate_files_count += 1
                    # It's a duplicate
                    self.move_duplicate_file(filepath, dest_match, cat_path, dup_path, tbd_path, hashes_in_dup)
                else:
                    # It is NOT a duplicate and should be moved to a categorised folder
                    try:
                        final_path = build_final_path_default(cat_path, filepath)
                        logging.info(f"[Non-Dup => Categorised] {filepath} => {final_path}")
                        move_with_collision(filepath, final_path)
                        self.nonduplicate_files_count += 1
                    except Exception as ex:
                        self.error_signal.emit("MoveError", filepath, str(ex))

        # Clean up leftover files and process empty folders
        self.cleanup_and_process_empty_folders(cat_path, dup_path, tbd_path, hashes_in_dup)

        self.done_signal.emit("success", self.duplicate_files_count, self.nonduplicate_files_count)

    def find_duplicate_in_hashes(self, file_hash,hashes):
        """
        Checks if the file hash exists in the source or destination hashes and returns the file
        :param file_hash: Hash of the file to check
        :return: Full file path of the hash file
        """
        for path, hash in hashes.items():
            if file_hash == hash:
                #remove_hash = path
                return path
        return None

    def hash_folder(self, folder):
        """
        Hashes all files in a folder and returns a dictionary of {filepath: hash}.
        """
        file_hashes = {}
        for root, _, files in os.walk(folder):
            for filename in files:
                filepath = os.path.join(root, filename)
                try:
                    fhash, err = self.hash_file(filepath)
                    if err is None:
                        file_hashes[filepath] = fhash
                    else:
                        self.error_signal.emit("Hashing", filepath, f"{err[0]}: {err[1]}")
                except Exception as ex:
                    self.error_signal.emit("Hashing", filepath, str(ex))

        return file_hashes

    def hash_files(self, filepaths):
        """
        Hashes a list of files and returns a dictionary of {filepath: hash}.
        """
        file_hashes = {}
        start_time = time.time()
        total_files = len(filepaths)
        processed = 0
        # Create a multiprocessing pool for hashing
        pool = multiprocessing.Pool(
            processes=(
                multiprocessing.cpu_count() if CONFIG['multiprocessing_cores'] <= 0
                else CONFIG['multiprocessing_cores']
            )
        )
        worker = partial(worker_hash_file, algo=self.algo, skip_size=self.skip_size)
        results_iter = pool.imap_unordered(worker, filepaths)

        # Hashing loop
        for result in results_iter:
            if self.stop_event.is_set():
                pool.terminate()
                pool.join()
                self.done_signal.emit("aborted", 0, 0)
                return
            (fpath, fhash, err) = result
            processed += 1
            if err is not None:
                self.error_signal.emit("Hashing", fpath, f"{err[0]}: {err[1]}")
            else:
                file_hashes[fpath] = fhash

        pool.close()
        pool.join()

        return file_hashes

    def hash_file(self, filepath):
        """
        Hashes a single file using worker_hash_file.
        """
        try:
            fhash = worker_hash_file(filepath, self.algo, self.skip_size)
            return fhash[1], fhash[2]
        except Exception as e:
            logging.error(f"Error hashing {filepath}: {e}")
            return None, ("HashError", str(e))

    def find_potential_duplicates(self, filepaths):
        """
        Finds potential duplicate file pairs based on the 'name (number).ext' pattern.
        Returns a list of tuples, where each tuple contains the paths of the potential duplicates.
        """
        potential_duplicates = []
        name_pattern = re.compile(r"^(.*) \(\d+\)(\..*)?$")
        base_names = {}

        for fpath in filepaths:
            fname = os.path.basename(fpath)
            match = name_pattern.match(fname)
            if match:
                base_name = match.group(1) + (match.group(2) if match.group(2) else "")
                if base_name not in base_names:
                    base_names[base_name] = []
                base_names[base_name].append(fpath)
            else:
                base, ext = os.path.splitext(fname)
                if base in base_names:
                    base_names[base].append(fpath)
                else:
                    base_names[base] = []
                    base_names[base].append(fpath)

        #Now match back to the original name of file that exists
        #base_names = {} #clear the base_names dict so it only checks the name of file duplicates

        for base, files in base_names.items():
            if len(files) > 1:
                # Check for the base file name
                base_file = None
                name_match_pattern = re.compile(r"^(.*)(\..*)?$")
                fmatch = name_match_pattern.match(base)
                if fmatch:
                    base_file_location = fmatch.group(1) + (fmatch.group(2) if fmatch.group(2) else "")
                
                for file in files:
                    if file.endswith(base_file_location):
                        base_file = file
                        break
                if base_file:
                    # If there is a base name of file pair it with all other files that share the same name
                    for file in files:
                        if file != base_file:
                            potential_duplicates.append((base_file, file))

        return potential_duplicates

    def process_filename_duplicate(self, file1, file2, cat_path, dup_path, tbd_path, hashes_in_dup, file_hash_map):
        """
        Processes duplicate files based on filename patterns like 'name' and 'name (number)'.
        """
        # file1 will be the original file name such as nameoffile.extension
        # and file2 will be the file name with a number after such as nameoffile (1).extension
        original = file1
        duplicate = file2
        final_path = build_final_path_default(cat_path, original)
        logging.info(f"[Dup-Name => Categorised] {original} => {final_path}")
        try:
            move_with_collision(original, final_path)
        except Exception as ex:
            self.error_signal.emit("MoveError", original, str(ex))

        self.duplicate_files_count += 1 #It's a duplicate

        found_hash = None #The other duplicate should go to Duplicates Folder or To Be Deleted if another duplicate exists
        for h, flist in file_hash_map.items():
            if duplicate in flist:
                found_hash = h
                break
        if not found_hash:
            found_hash = "unknown" #No Hash Found

        if found_hash in hashes_in_dup:
            # Already have a file of this hash in Duplicates => move to "To Be Deleted"
            del_path = os.path.join(tbd_path, os.path.basename(duplicate))
            logging.info(f"[Dup => AlreadyInDup => TBD] {duplicate} => {del_path}")
            try:
                move_with_collision(duplicate, del_path)
            except Exception as ex:
                self.error_signal.emit("MoveError", duplicate, str(ex))
        else:
            # Place the first encountered duplicate in the Duplicates folder
            d_path = build_final_path_default(dup_path, duplicate)
            logging.info(f"[Dup => Duplicates] {duplicate} => {d_path}")
            try:
                move_with_collision(duplicate, d_path)
                hashes_in_dup.add(found_hash)
            except Exception as ex:
                self.error_signal.emit("MoveError", duplicate, str(ex))

    def move_duplicate_file(self, src_path,dest_path, cat_path, dup_path, tbd_path, hashes_in_dup):
        """
        Moves the duplicate file to the appropriate destination, either Duplicates or To Be Deleted.
        """
        try:
            found_hash = None
            d_path = os.path.join(to_be_deleted_dir(self.organised_folder), os.path.basename(src_path))
            logging.info(f"[Dup => AlreadyInDup => TBD] {src_path} => {d_path}")
            move_with_collision(src_path, d_path)
            # Remove all files so that they do not hash or move to new location
            try:
                src_path_string = src_path
                dest_path_string = dest_path
                del src_path_string
                del dest_path_string
            except Exception as ex:
                self.error_signal.emit("DeletionError", src_path, str(ex))

        except Exception as ex:
            self.error_signal.emit("MoveError", src_path, str(ex))

    def cleanup_and_process_empty_folders(self, cat_path, dup_path, tbd_path, hashes_in_dup):
        """
        Cleans up any leftover files in the source folders and processes empty folders.
        """
        # Handle empty folders *after* everything else
        logging.info("[EmptyFolders] Running empty folder cleanup.")
        total_moved_count = 0  # Initialize total_moved_count here
        for folder in self.target_folders:
            if os.path.isdir(folder):
                # Moved the empty folder sweep to after processing non-duplicates
                total_moved_count += move_empty_folders_single_pass(self.organised_folder, [folder])

        logging.info(f"[EmptyFolders] Moved a total of {total_moved_count} empty folders.")