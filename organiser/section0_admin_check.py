import sys, ctypes, os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def check_admin():
    if not is_admin():
        # Re-run the program with administrator privileges.
        script = sys.argv[0]
        params = " ".join(sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        sys.exit(0)

# Run the admin check on import.
check_admin()