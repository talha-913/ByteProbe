import os
import json
import sqlite3
from datetime import datetime

# Define constants for case structure
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_BASE_DIR_NAME = "cases"
RECENT_CASES_FILE = "recent_cases.json" 
CASE_METADATA_DB_NAME = "case_metadata.db" 

class CaseManager:
    """
    Manages the creation, loading, and listing of forensic cases.
    Each case gets its own directory and an SQLite database for its metadata.
    """
    def __init__(self):
        self.cases_root_dir = os.path.join(APP_ROOT, CASES_BASE_DIR_NAME)
        os.makedirs(self.cases_root_dir, exist_ok=True)
        self.recent_cases_path = os.path.join(APP_ROOT, RECENT_CASES_FILE)

    def _initialize_case_db(self, db_path):
        """Initialize the SQLite database schema for a new case, including data sources table."""
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Table for Case Details 
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS case_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_name TEXT NOT NULL UNIQUE,
                    case_number TEXT,
                    case_type TEXT,
                    description TEXT,
                    investigator_name TEXT,
                    investigator_organization TEXT,
                    creation_timestamp TEXT NOT NULL,
                    last_accessed_timestamp TEXT NOT NULL
                )
            ''')

            # --- NEW: Table for Data Sources ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id INTEGER NOT NULL,          -- Foreign key to case_details
                    source_type TEXT NOT NULL,         -- e.g., 'Disk Image', 'Logical Drive', 'Folder'
                    path TEXT NOT NULL UNIQUE,         -- Path to the source file/device/folder
                    name TEXT,                         -- User-provided name for the source
                    description TEXT,                  -- User-provided description
                    added_timestamp TEXT NOT NULL,     -- When this source was added
                    FOREIGN KEY (case_id) REFERENCES case_details(id) ON DELETE CASCADE
                )
            ''')

            conn.commit()
            print(f"Database schema initialized (including data_sources table) at: {db_path}")
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")
            raise # Re-raise to indicate failure
        finally:
            if conn:
                conn.close()

    def create_new_case(self, case_name, case_number, case_type, description,
                         investigator_name, investigator_organization, base_output_dir=None):
        """
        Creates a new case directory and initializes its metadata database.
        """
        case_dir_name = self._sanitize_case_name(case_name)
        
        if base_output_dir:
            case_path = os.path.join(base_output_dir, case_dir_name)
        else:
            case_path = os.path.join(self.cases_root_dir, case_dir_name)

        if os.path.exists(case_path):
            print(f"Error: Case directory '{case_path}' already exists.")
            return None

        try:
            os.makedirs(case_path)
            print(f"Case directory created at: {case_path}")

            db_path = os.path.join(case_path, CASE_METADATA_DB_NAME)
            self._initialize_case_db(db_path) # This call now initializes the new table

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            current_timestamp = datetime.now().isoformat()

            cursor.execute(
                "INSERT INTO case_details (case_name, case_number, case_type, description, "
                "investigator_name, investigator_organization, creation_timestamp, last_accessed_timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (case_name, case_number, case_type, description,
                 investigator_name, investigator_organization,
                 current_timestamp, current_timestamp)
            )
            conn.commit()
            conn.close()

            self._add_to_recent_cases(case_name, case_path)
            return case_path
        except Exception as e:
            print(f"Failed to create case '{case_name}': {e}")
            if os.path.exists(case_path):
                import shutil
                shutil.rmtree(case_path)
            return None

    def _sanitize_case_name(self, name):
        """Sanitizes a string to be used as a directory name."""
        return "".join(c for c in name if c.isalnum() or c in (' ', '.', '_')).rstrip().replace(' ', '_')

    def get_recent_cases(self):
        """Loads and returns a list of recent cases."""
        if not os.path.exists(self.recent_cases_path):
            return []
        try:
            with open(self.recent_cases_path, 'r') as f:
                recent_cases = json.load(f)
            unique_cases = []
            seen_paths = set()
            for case in recent_cases:
                if case['path'] not in seen_paths:
                    unique_cases.append(case)
                    seen_paths.add(case['path'])
            return unique_cases
        except json.JSONDecodeError as e:
            print(f"Error reading recent cases file: {e}")
            return []

    def _add_to_recent_cases(self, case_name, case_path):
        """Adds a case to the recent cases list, keeping the list ordered and limited."""
        recent_cases = self.get_recent_cases()
        new_entry = {'name': case_name, 'path': case_path, 'timestamp': datetime.now().isoformat()}

        recent_cases = [c for c in recent_cases if c['path'] != case_path]
        recent_cases.insert(0, new_entry)

        recent_cases = recent_cases[:10]

        try:
            with open(self.recent_cases_path, 'w') as f:
                json.dump(recent_cases, f, indent=4)
        except Exception as e:
            print(f"Error saving recent cases: {e}")

    def load_case(self, case_path):
        """
        Loads an existing case by marking it as recently accessed.
        Returns the case_path on success, None on failure.
        """
        if not os.path.isdir(case_path):
            print(f"Error: Case path '{case_path}' is not a valid directory.")
            return None

        db_path = os.path.join(case_path, CASE_METADATA_DB_NAME)
        if not os.path.exists(db_path):
            print(f"Error: Case metadata DB not found at '{db_path}'.")
            return None

        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            current_timestamp = datetime.now().isoformat()
            
            # Get the case_id from the case_details table (assuming one case per DB)
            cursor.execute("SELECT id, case_name FROM case_details LIMIT 1")
            result = cursor.fetchone()
            if not result:
                print(f"Error: No case details found in DB at '{db_path}'. Cannot load case.")
                return None
            
            case_id, case_name = result

            cursor.execute(
                "UPDATE case_details SET last_accessed_timestamp = ? WHERE id = ?",
                (current_timestamp, case_id)
            )
            conn.commit()
            conn.close() # Close connection after commit

            self._add_to_recent_cases(case_name, case_path)
            print(f"Case '{case_name}' loaded successfully from: {case_path}")
            return case_path
        except sqlite3.Error as e:
            print(f"Error loading case from DB '{db_path}': {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_case_metadata(self, case_path):
        """
        Retrieves the main case details from the case's database.
        Used to get the actual case name after loading by path.
        """
        db_path = os.path.join(case_path, CASE_METADATA_DB_NAME)
        if not os.path.exists(db_path):
            print(f"Error: Case metadata DB not found at '{db_path}'.")
            return None
        
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT case_name, case_number, case_type, description, "
                           "investigator_name, investigator_organization, "
                           "creation_timestamp, last_accessed_timestamp FROM case_details LIMIT 1")
            row = cursor.fetchone()
            if row:
                metadata = {
                    "case_name": row[0],
                    "case_number": row[1],
                    "case_type": row[2],
                    "description": row[3],
                    "investigator_name": row[4],
                    "investigator_organization": row[5],
                    "creation_timestamp": row[6],
                    "last_accessed_timestamp": row[7]
                }
                return metadata
            return None
        except sqlite3.Error as e:
            print(f"Error retrieving case metadata from DB '{db_path}': {e}")
            return None
        finally:
            if conn:
                conn.close()

    def add_data_source(self, case_path, source_info):
        """
        Adds a new data source to the specified case's database.
        :param case_path: Full path to the case directory.
        :param source_info: Dictionary containing source_type, path, name, description.
        :return: True on success, False on failure.
        """
        db_path = os.path.join(case_path, CASE_METADATA_DB_NAME)
        if not os.path.exists(db_path):
            print(f"Error: Case metadata DB not found at '{db_path}'. Cannot add data source.")
            return False
        
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get the case_id for the current case
            cursor.execute("SELECT id FROM case_details LIMIT 1")
            result = cursor.fetchone()
            if not result:
                print(f"Error: No case details found in DB at '{db_path}'. Cannot add data source.")
                return False
            case_id = result[0]

            # Insert data source into the data_sources table
            current_timestamp = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO data_sources (case_id, source_type, path, name, description, added_timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (case_id, source_info["source_type"], source_info["path"],
                 source_info.get("name", ""), source_info.get("description", ""), current_timestamp)
            )
            conn.commit()

            # Update the last_accessed_timestamp of the main case to reflect modification
            cursor.execute(
                "UPDATE case_details SET last_accessed_timestamp = ? WHERE id = ?",
                (current_timestamp, case_id)
            )
            conn.commit()

            print(f"Data source '{source_info.get('name', source_info['path'])}' added to case at {case_path}.")
            return True
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: data_sources.path" in str(e):
                print(f"Error: A data source with the path '{source_info['path']}' already exists in this case.")
                return False
            print(f"SQLite Integrity Error adding data source: {e}")
            return False
        except sqlite3.Error as e:
            print(f"Error adding data source to DB '{db_path}': {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_data_sources(self, case_path):
        """
        Retrieves all data sources for a given case from its database.
        :param case_path: Full path to the case directory.
        :return: A list of dictionaries, each representing a data source. Returns empty list on error/no sources.
        """
        db_path = os.path.join(case_path, CASE_METADATA_DB_NAME)
        if not os.path.exists(db_path):
            print(f"Error: Case metadata DB not found at '{db_path}'. Cannot retrieve data sources.")
            return []
        
        conn = None
        data_sources = []
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get the case_id for the current case
            cursor.execute("SELECT id FROM case_details LIMIT 1")
            result = cursor.fetchone()
            if not result:
                print(f"Error: No case details found in DB at '{db_path}'.")
                return []
            case_id = result[0]

            cursor.execute(
                "SELECT id, source_type, path, name, description, added_timestamp FROM data_sources WHERE case_id = ?",
                (case_id,)
            )
            
            rows = cursor.fetchall()
            for row in rows:
                data_sources.append({
                    "id": row[0],
                    "source_type": row[1],
                    "path": row[2],
                    "name": row[3],
                    "description": row[4],
                    "added_timestamp": row[5]
                })
            return data_sources
        except sqlite3.Error as e:
            print(f"Error retrieving data sources from DB '{db_path}': {e}")
            return []
        finally:
            if conn:
                conn.close()

# The example usage block is commented out as per your original file.

# Example Usage (for testing purposes, not part of the final app flow)
# if __name__ == '__main__':
#     manager = CaseManager()
#     print("--- Creating new case ---")
#     new_case_path = manager.create_new_case(
#         case_name="MyFirstForensicCase",
#         case_number="2024-001",
#         case_type="Cyber Incident",
#         description="Initial investigation of a malware outbreak.",
#         investigator_name="John Doe",
#         investigator_organization="CyberSec Inc."
#     )
#     if new_case_path:
#         print(f"New case created at: {new_case_path}")
#     else:
#         print("Failed to create case.")

#     print("\n--- Listing recent cases ---")
#     recent = manager.get_recent_cases()
#     if recent:
#         for c in recent:
#             print(f"- {c['name']} ({c['path']})")
#     else:
#         print("No recent cases.")

#     print("\n--- Attempting to load the first recent case ---")
#     if recent:
#         loaded_path = manager.load_case(recent[0]['path'])
#         if loaded_path:
#             print(f"Successfully loaded: {loaded_path}")
#         else:
#             print("Failed to load case.")