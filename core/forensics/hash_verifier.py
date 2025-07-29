"""
Hash verification module for file integrity checking
"""
import hashlib
import os
from typing import Dict, Optional, Tuple
from datetime import datetime
import json
import sqlite3


class HashVerifier:
    """Handle file hash calculation and verification"""
    
    SUPPORTED_ALGORITHMS = ['md5', 'sha1', 'sha256', 'sha512']
    
    def __init__(self, case_path: Optional[str] = None):
        self.case_path = case_path
        self.hash_db_path = None
        if case_path:
            self.hash_db_path = os.path.join(case_path, "file_hashes.db")
            self._init_hash_database()
    
    def _init_hash_database(self):
        """Initialize hash database for case"""
        if not self.hash_db_path:
            return
            
        conn = sqlite3.connect(self.hash_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_hashes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                md5_hash TEXT,
                sha1_hash TEXT,
                sha256_hash TEXT,
                sha512_hash TEXT,
                calculated_at TEXT NOT NULL,
                source_type TEXT,  -- 'carved', 'file_system', 'evidence'
                UNIQUE(file_path, source_type)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def calculate_file_hash(self, file_path: str, algorithms: list = None) -> Dict[str, str]:
        """
        Calculate hash(es) for a file
        
        Args:
            file_path: Path to file
            algorithms: List of algorithms to use (default: ['md5', 'sha256'])
            
        Returns:
            Dictionary with algorithm names as keys and hash values as values
        """
        if algorithms is None:
            algorithms = ['md5', 'sha256']
            
        # Validate algorithms
        algorithms = [alg.lower() for alg in algorithms if alg.lower() in self.SUPPORTED_ALGORITHMS]
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Initialize hash objects
        hashers = {}
        for alg in algorithms:
            hashers[alg] = hashlib.new(alg)
        
        # Read file in chunks to handle large files
        chunk_size = 64 * 1024  # 64KB chunks
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    for hasher in hashers.values():
                        hasher.update(chunk)
        except Exception as e:
            raise Exception(f"Error reading file {file_path}: {e}")
        
        # Get final hashes
        results = {}
        for alg, hasher in hashers.items():
            results[alg] = hasher.hexdigest()
        
        return results
    
    def calculate_data_hash(self, data: bytes, algorithms: list = None) -> Dict[str, str]:
        """Calculate hash(es) for raw data"""
        if algorithms is None:
            algorithms = ['md5', 'sha256']
            
        algorithms = [alg.lower() for alg in algorithms if alg.lower() in self.SUPPORTED_ALGORITHMS]
        
        results = {}
        for alg in algorithms:
            hasher = hashlib.new(alg)
            hasher.update(data)
            results[alg] = hasher.hexdigest()
            
        return results
    
    def store_file_hash(self, file_path: str, hashes: Dict[str, str], 
                       source_type: str = 'file_system') -> bool:
        """Store calculated hashes in database"""
        if not self.hash_db_path:
            return False
            
        try:
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            calculated_at = datetime.now().isoformat()
            
            conn = sqlite3.connect(self.hash_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO file_hashes 
                (file_path, file_size, md5_hash, sha1_hash, sha256_hash, sha512_hash, 
                 calculated_at, source_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_path,
                file_size,
                hashes.get('md5'),
                hashes.get('sha1'),
                hashes.get('sha256'),
                hashes.get('sha512'),
                calculated_at,
                source_type
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error storing hash: {e}")
            return False
    
    def get_file_hash(self, file_path: str, source_type: str = 'file_system') -> Optional[Dict[str, str]]:
        """Retrieve stored hash for a file"""
        if not self.hash_db_path:
            return None
            
        try:
            conn = sqlite3.connect(self.hash_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT md5_hash, sha1_hash, sha256_hash, sha512_hash, calculated_at
                FROM file_hashes 
                WHERE file_path = ? AND source_type = ?
            ''', (file_path, source_type))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'md5': row[0],
                    'sha1': row[1],
                    'sha256': row[2],
                    'sha512': row[3],
                    'calculated_at': row[4]
                }
                
        except Exception as e:
            print(f"Error retrieving hash: {e}")
            
        return None
    
    def verify_file_integrity(self, file_path: str, expected_hashes: Dict[str, str]) -> Dict[str, bool]:
        """
        Verify file integrity against expected hashes
        
        Returns:
            Dictionary with algorithm names and verification results
        """
        if not os.path.exists(file_path):
            return {alg: False for alg in expected_hashes.keys()}
        
        # Calculate current hashes
        algorithms = list(expected_hashes.keys())
        current_hashes = self.calculate_file_hash(file_path, algorithms)
        
        # Compare
        results = {}
        for alg in algorithms:
            if alg in current_hashes and alg in expected_hashes:
                results[alg] = current_hashes[alg].lower() == expected_hashes[alg].lower()
            else:
                results[alg] = False
                
        return results
    
    def batch_calculate_hashes(self, file_paths: list, algorithms: list = None,
                             progress_callback=None) -> Dict[str, Dict[str, str]]:
        """Calculate hashes for multiple files"""
        if algorithms is None:
            algorithms = ['md5', 'sha256']
            
        results = {}
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            try:
                if progress_callback:
                    progress_callback(i, total_files, f"Hashing: {os.path.basename(file_path)}")
                    
                hashes = self.calculate_file_hash(file_path, algorithms)
                results[file_path] = hashes
                
                # Store in database if case is active
                if self.case_path:
                    self.store_file_hash(file_path, hashes)
                    
            except Exception as e:
                print(f"Error hashing {file_path}: {e}")
                results[file_path] = {"error": str(e)}
        
        if progress_callback:
            progress_callback(total_files, total_files, "Hash calculation complete")
            
        return results
    
    def export_hash_report(self, output_path: str, format: str = 'csv') -> bool:
        """Export hash database to file"""
        if not self.hash_db_path or not os.path.exists(self.hash_db_path):
            return False
            
        try:
            conn = sqlite3.connect(self.hash_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT file_path, file_size, md5_hash, sha1_hash, sha256_hash, 
                       sha512_hash, calculated_at, source_type
                FROM file_hashes 
                ORDER BY calculated_at
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            if format.lower() == 'csv':
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write("File Path,File Size,MD5,SHA1,SHA256,SHA512,Calculated At,Source Type\n")
                    for row in rows:
                        f.write(','.join([f'"{str(cell) if cell else ""}"' for cell in row]) + '\n')
                        
            elif format.lower() == 'json':
                data = []
                for row in rows:
                    data.append({
                        'file_path': row[0],
                        'file_size': row[1],
                        'md5': row[2],
                        'sha1': row[3],
                        'sha256': row[4],
                        'sha512': row[5],
                        'calculated_at': row[6],
                        'source_type': row[7]
                    })
                    
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error exporting hash report: {e}")
            return False
    
    def compare_hash_sets(self, other_hashes: Dict[str, Dict[str, str]]) -> Dict[str, str]:
        """
        Compare current hash database with another set of hashes
        
        Returns:
            Dictionary with file paths and comparison results
        """
        if not self.hash_db_path:
            return {}
            
        results = {}
        
        try:
            conn = sqlite3.connect(self.hash_db_path)
            cursor = conn.cursor()
            
            for file_path, expected_hashes in other_hashes.items():
                cursor.execute('''
                    SELECT md5_hash, sha256_hash 
                    FROM file_hashes 
                    WHERE file_path = ?
                ''', (file_path,))
                
                row = cursor.fetchone()
                if row:
                    stored_md5, stored_sha256 = row
                    
                    # Check MD5
                    if 'md5' in expected_hashes:
                        if stored_md5 and stored_md5.lower() == expected_hashes['md5'].lower():
                            results[file_path] = 'match'
                        else:
                            results[file_path] = 'mismatch'
                    # Check SHA256
                    elif 'sha256' in expected_hashes:
                        if stored_sha256 and stored_sha256.lower() == expected_hashes['sha256'].lower():
                            results[file_path] = 'match'
                        else:
                            results[file_path] = 'mismatch'
                else:
                    results[file_path] = 'not_found'
            
            conn.close()
            
        except Exception as e:
            print(f"Error comparing hashes: {e}")
            
        return results


# Known file hash database for common forensic files
KNOWN_HASHES = {
    # Common Windows system files (examples)
    "C:/Windows/System32/notepad.exe": {
        "md5": "various",  # These would be actual hashes
        "description": "Windows Notepad"
    },
    # NSRL (National Software Reference Library) integration could go here
}


def load_nsrl_hashes(nsrl_file_path: str) -> Dict[str, Dict[str, str]]:
    """Load NSRL hash database for known file identification"""
    # This would implement NSRL hash database loading
    # NSRL format: "SHA-1","MD5","CRC32","FileName","FileSize","ProductCode","OpSystemCode","SpecialCode"
    pass


def get_file_reputation(file_hash: str, hash_type: str = 'sha256') -> Dict[str, str]:
    """
    Check file reputation using hash (integration point for VirusTotal API, etc.)
    This would be implemented with external APIs
    """
    return {
        'reputation': 'unknown',
        'source': 'local',
        'last_checked': datetime.now().isoformat()
    }