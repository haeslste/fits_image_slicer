
import os
import json
from datetime import datetime
from config import Config

def _normalize_path(path):
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))

class Project:
    def __init__(self):
        self.name = ""
        self.directory = ""
        self.files = []
        self.source_folders = []
        self.patches = {} # {file_path: [patch_meta]}
        self.config = Config()
        self.project_file_path = ""

    def create(self, name, directory, files):
        self.name = name
        self.directory = _normalize_path(os.path.join(directory, name))
        self.files = [_normalize_path(f) for f in files]
        self.source_folders = list(set(os.path.dirname(f) for f in self.files))
        self.project_file_path = os.path.join(self.directory, "project.json")
        
        os.makedirs(self.directory, exist_ok=True)
        self.config.out_dir = os.path.join(self.directory, "patches")
        
        self.save()
        return self

    def load(self, file_path):
        self.project_file_path = _normalize_path(file_path)
        self.directory = os.path.dirname(self.project_file_path)
        with open(self.project_file_path, 'r') as f:
            data = json.load(f)
            self.name = data["name"]
            self.files = [_normalize_path(f) for f in data["files"]]
            self.source_folders = data.get("source_folders", [])
            
            if not self.source_folders and self.files:
                self.source_folders = list(set(os.path.dirname(f) for f in self.files))

            patches_raw = data.get("patches", {})
            self.patches = {_normalize_path(k): v for k, v in patches_raw.items()}

            self.config.labels = data.get("labels", [])
            self.config.out_dir = os.path.join(self.directory, "patches")
        return self

    def save(self):
        data = {
            "name": self.name,
            "files": self.files,
            "source_folders": self.source_folders,
            "patches": self.patches,
            "labels": self.config.labels,
            "last_modified": datetime.now().isoformat()
        }
        with open(self.project_file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def add_files(self, files_to_add):
        for f in files_to_add:
            normalized_f = _normalize_path(f)
            if normalized_f not in self.files:
                self.files.append(normalized_f)
            
            dir_name = os.path.dirname(normalized_f)
            if dir_name not in self.source_folders:
                self.source_folders.append(dir_name)
        self.save()

    def scan_for_new_files(self):
        if not self.source_folders:
            return []

        new_files = []
        current_files_normalized = set(self.files)

        for directory in self.source_folders:
            try:
                if not os.path.isdir(directory): continue
                for filename in os.listdir(directory):
                    if filename.lower().endswith(('.fits','fts' ,'.fit', '.fz')):
                        full_path = _normalize_path(os.path.join(directory, filename))
                        if full_path not in current_files_normalized:
                            new_files.append(full_path)
            except FileNotFoundError:
                continue
        return new_files
