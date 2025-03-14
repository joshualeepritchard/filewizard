import json, os, logging

def load_config():
    default_config = {
        "target_folders": [],
        "organised_folder": "",
        "hash_algorithm": "sha256",
        "skip_larger_than": 0,
        "multiprocessing_cores": 0,
        "categories": []
    }
    if not os.path.exists("config.json"):
        with open("config.json", "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config
    else:
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.error("Failed to decode config.json. Using default config.")
            return default_config

def save_config(cfg):
    with open("config.json", "w") as f:
        json.dump(cfg, f, indent=4)

CONFIG = load_config()