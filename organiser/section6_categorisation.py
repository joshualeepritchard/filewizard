import os, logging
from datetime import datetime
from organiser.section3_helpers import ensure_dir_exists

def build_final_path_default(base, file_path):
    """
    Builds the destination path based on the file extension and modification year,
    following the requested hierarchical structure.
    """

    try:
        year = str(datetime.fromtimestamp(os.path.getmtime(file_path)).year)
    except Exception:
        year = "UnknownYear"

    _, ext = os.path.splitext(file_path)
    ext = ext.lower().strip()

    if ext == "":  # Handle no extension
        ext_is_empty = True
    else:
        ext_is_empty = False

    # Define extension sets for each category:
    text_docs = {".doc", ".docx", ".odt", ".rtf", ".wpd", ".txt", ".tex", ".md", ".wps", ".pages", ".epub"}
    worksheets = {".xls", ".xlsx", ".xlsm", ".ods", ".numbers", ".csv", ".tsv"}
    presentations = {".ppt", ".pptx", ".odp", ".key", ".pps", ".ppsx", ".pptm"}
    pdf_docs = {".pdf"}
    emails = {".eml", ".msg", ".pst", ".mbox", ".ost"}

    videos = {".mp4", ".mov", ".avi", ".wmv", ".flv", ".mkv", ".mpeg", ".mpg", ".m4v", ".3gp", ".3g2",
              ".webm", ".ogv", ".amv", ".vob", ".rm", ".rmvb"}
    audio = {".mp3", ".wav", ".wma", ".aac", ".ogg", ".flac", ".m4a", ".aiff", ".amr", ".alac", ".opus",
             ".mid", ".midi"}
    images = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg", ".webp", ".ico", ".heic",
              ".heif", ".raw", ".psd", ".eps", ".ai", ".xcf", ".indd", ".cr2"}
    threed = {".3ds", ".obj", ".fbx", ".blend", ".dae", ".stl", ".ply", ".max", ".skp", ".gltf", ".glb",
              ".igs", ".step"}

    source_code = {".c", ".cpp", ".h", ".hpp", ".cs", ".java", ".js", ".jsx", ".ts", ".tsx", ".py", ".rb",
                   ".php", ".pl", ".swift", ".go", ".rs", ".sh", ".bash", ".sql", ".lua", ".m", ".scala",
                   ".kt", ".dart", ".r"}
    compiled_exec = {".exe", ".bat", ".msi", ".com", ".jar", ".class", ".dll", ".apk", ".bin", ".so",
                     ".app", ".deb", ".rpm", ".ipa"}
    web_files = {".html", ".htm", ".css", ".scss", ".sass", ".less", ".xml", ".json", ".yaml", ".yml",
                 ".toml"}

    compressed = {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".lzma", ".iso", ".dmg",
                  ".cab", ".z", ".arj"}

    fonts = {".ttf", ".otf", ".woff", ".woff2", ".eot", ".pfb", ".pfm", ".fon"}
    shortcuts = {".lnk", ".url", ".webloc"}
    logs = {".log"}
    system_temp = {".tmp", ".sys", ".bak", ".cache", ".dat", ".db", ".ini", ".cfg"}

    # Decide the folder structure:
    if ext_is_empty:
        # 5.5 No Extension -> other\no extension\year
        final_dir = os.path.join(base, "Other", "No Extension", year)
    elif ext == ".prproj":
        # Special case for Adobe Premiere projects
        final_dir = os.path.join(base, "Media", "Video", "Adobe", year)
    elif ext in text_docs:
        # 1.1 -> documents\text documents\.ext\year
        final_dir = os.path.join(base, "Documents", "Text Documents", ext, year)
    elif ext in worksheets:
        # 1.2 -> documents\worksheets\.ext\year
        final_dir = os.path.join(base, "Documents", "Worksheets", ext, year)
    elif ext in presentations:
        # 1.3 -> documents\presentations\year
        final_dir = os.path.join(base, "Documents", "Presentations", year)
    elif ext in pdf_docs:
        # 1.4 -> documents\pdf documents\year
        final_dir = os.path.join(base, "Documents", "PDF Documents", year)
    elif ext in emails:
        # 1.5 -> documents\emails\year
        final_dir = os.path.join(base, "Documents", "Emails", year)
    elif ext in videos:
        # 2.1 -> media\video\year
        final_dir = os.path.join(base, "Media", "Video", year)
    elif ext in audio:
        # 2.2 -> media\audio\year
        final_dir = os.path.join(base, "Media", "Audio", year)
    elif ext in images:
        # 2.3 -> media\images\year
        final_dir = os.path.join(base, "Media", "Images", year)
    elif ext in threed:
        # 2.4 -> media\3d files\.ext\year
        final_dir = os.path.join(base, "Media", "3D Files", ext, year)
    elif ext in source_code:
        # 3.1 -> programs\source code files\year
        final_dir = os.path.join(base, "Programs", "Source Code Files", year)
    elif ext in compiled_exec:
        # 3.2 -> programs\compiled and executables\year
        final_dir = os.path.join(base, "Programs", "Compiled and Executables", year)
    elif ext in web_files:
        # 3.3 -> programs\web files\year
        final_dir = os.path.join(base, "Programs", "Web Files", year)
    elif ext in compressed:
        # 4 -> compressed files\year
        final_dir = os.path.join(base, "Compressed Files", year)
    elif ext in fonts:
        # 5.1 -> other\fonts\.ext (no year)
        final_dir = os.path.join(base, "Other", "Fonts", ext)
    elif ext in shortcuts:
        # 5.2 -> other\links and shortcuts (no year)
        final_dir = os.path.join(base, "Other", "Links and Shortcuts")
    elif ext in logs:
        # 5.3 -> other\log files\year
        final_dir = os.path.join(base, "Other", "Log Files", year)
    elif ext in system_temp:
        # 5.4 -> other\systemfiles\.ext (no year)
        final_dir = os.path.join(base, "Other", "SystemFiles", ext)
    else:
        # 5.6 -> other\uncategorised\year
        final_dir = os.path.join(base, "Other", "Uncategorised", year)

    ensure_dir_exists(final_dir)
    return os.path.join(final_dir, os.path.basename(file_path))