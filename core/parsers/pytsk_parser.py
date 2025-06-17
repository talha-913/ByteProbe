"""
PyTSK3-based disk image parser implementation
"""
import os
import sys
from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime
import logging

try:
    import pytsk3
    # import pyewf
    PYTSK3_AVAILABLE = True
except ImportError:
    PYTSK3_AVAILABLE = False
    logging.warning("PyTSK3 not available. Disk parsing functionality will be limited.")

from ..interfaces.image_parser import IImageParser, FileEntry


class PyTSKParser(IImageParser):
    """PyTSK3-based implementation of disk image parser"""
    
    def __init__(self):
        self.img_info = None
        self.fs_info = None
        self.current_partition_offset = 0
        self._ewf_handle = None
        
    def open_image(self, image_path: str) -> bool:
        """Open a disk image for parsing"""
        if not PYTSK3_AVAILABLE:
            logging.error("PyTSK3 is not installed")
            return False
            
        try:
            # Check if it's an E01 image
            if image_path.lower().endswith('.e01'):
                self._ewf_handle = pyewf.handle()
                self._ewf_handle.open([image_path])
                self.img_info = EWFImgInfo(self._ewf_handle)
            else:
                # Regular disk image (DD, RAW, etc.)
                self.img_info = pytsk3.Img_Info(image_path)
            
            logging.info(f"Successfully opened image: {image_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to open image: {e}")
            return False
    
    def get_partitions(self) -> List[Dict[str, Any]]:
        """Get list of partitions in the image"""
        if not self.img_info:
            return []
            
        partitions = []
        
        try:
            # Try to open volume system
            vol_info = pytsk3.Volume_Info(self.img_info)
            
            for partition in vol_info:
                if partition.len > 0:  # Skip unallocated entries
                    part_info = {
                        'index': partition.addr,
                        'type': partition.desc.decode('utf-8', errors='ignore'),
                        'start': partition.start * 512,  # Convert to bytes
                        'length': partition.len * 512,
                        'flags': partition.flags
                    }
                    partitions.append(part_info)
                    
        except Exception as e:
            # No partition table, treat as single partition
            logging.info(f"No partition table found, treating as single partition: {e}")
            partitions.append({
                'index': 0,
                'type': 'Whole Disk',
                'start': 0,
                'length': self.img_info.get_size(),
                'flags': pytsk3.TSK_VS_PART_FLAG_ALLOC
            })
            
        return partitions
    
    def open_file_system(self, partition_offset: int = 0) -> bool:
        """Open a file system at the given partition offset"""
        if not self.img_info:
            return False
            
        try:
            self.fs_info = pytsk3.FS_Info(self.img_info, offset=partition_offset)
            self.current_partition_offset = partition_offset
            
            # Log file system info
            fs_type = self.fs_info.info.ftype
            logging.info(f"Opened file system type: {fs_type} at offset {partition_offset}")
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to open file system: {e}")
            return False
    
    def get_file_entries(self, path: str = "/") -> List[FileEntry]:
        """Get file entries in a directory"""
        if not self.fs_info:
            return []
            
        entries = []
        
        try:
            # Open directory
            directory = self.fs_info.open_dir(path)
            
            for entry in directory:
                # Skip . and .. entries
                if entry.info.name.name in [b".", b".."]:
                    continue
                    
                file_entry = self._create_file_entry(entry, path)
                if file_entry:
                    entries.append(file_entry)
                    
        except Exception as e:
            logging.error(f"Error reading directory {path}: {e}")
            
        return entries
    
    def get_file_content(self, file_path: str) -> Optional[bytes]:
        """Read file content"""
        if not self.fs_info:
            return None
            
        try:
            file_obj = self.fs_info.open(file_path)
            
            # Read file content
            file_size = file_obj.info.meta.size
            if file_size > 0:
                return file_obj.read_random(0, file_size)
            else:
                return b""
                
        except Exception as e:
            logging.error(f"Error reading file {file_path}: {e}")
            return None
    
    def walk_file_system(self) -> Iterator[FileEntry]:
        """Walk through entire file system yielding each entry"""
        if not self.fs_info:
            return
            
        def walk_directory(path: str = "/"):
            try:
                entries = self.get_file_entries(path)
                
                for entry in entries:
                    yield entry
                    
                    # Recursively walk subdirectories
                    if entry.is_directory and not entry.is_deleted:
                        # Construct full path
                        sub_path = f"{path.rstrip('/')}/{entry.name}"
                        yield from walk_directory(sub_path)
                        
            except Exception as e:
                logging.error(f"Error walking directory {path}: {e}")
        
        yield from walk_directory()
    
    def close(self):
        """Close the image and cleanup resources"""
        self.fs_info = None
        self.img_info = None
        
        if self._ewf_handle:
            self._ewf_handle.close()
            self._ewf_handle = None
            
        logging.info("Closed disk image")
    
    def _create_file_entry(self, tsk_file, parent_path: str) -> Optional[FileEntry]:
        """Create FileEntry from TSK file object"""
        try:
            entry = FileEntry()
            
            # Basic info
            entry.name = tsk_file.info.name.name.decode('utf-8', errors='ignore')
            entry.path = f"{parent_path.rstrip('/')}/{entry.name}"
            
            # Check if it's a directory
            if tsk_file.info.meta:
                entry.is_directory = (tsk_file.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR)
                entry.size = tsk_file.info.meta.size
                
                # Check if deleted
                if tsk_file.info.meta.flags & pytsk3.TSK_FS_META_FLAG_UNALLOC:
                    entry.is_deleted = True
                
                # Timestamps (NTFS timestamps are in Windows FILETIME format)
                if tsk_file.info.meta.crtime:
                    entry.created_time = datetime.fromtimestamp(tsk_file.info.meta.crtime)
                if tsk_file.info.meta.mtime:
                    entry.modified_time = datetime.fromtimestamp(tsk_file.info.meta.mtime)
                if tsk_file.info.meta.atime:
                    entry.accessed_time = datetime.fromtimestamp(tsk_file.info.meta.atime)
                
                # NTFS specific - MFT entry number
                if hasattr(tsk_file.info.meta, 'addr'):
                    entry.mft_entry = tsk_file.info.meta.addr
            
            return entry
            
        except Exception as e:
            logging.error(f"Error creating file entry: {e}")
            return None


class EWFImgInfo(pytsk3.Img_Info):
    """Wrapper for EWF (E01) images"""
    
    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super().__init__(url="", type=pytsk3.TSK_IMG_TYPE_EXTERNAL)
        
    def close(self):
        self._ewf_handle.close()
        
    def read(self, offset, length):
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(length)
        
    def get_size(self):
        return self._ewf_handle.get_media_size()


class MockParser(IImageParser):
    """Mock parser for testing when PyTSK3 is not available"""
    
    def __init__(self):
        self.is_open = False
        
    def open_image(self, image_path: str) -> bool:
        self.is_open = os.path.exists(image_path)
        return self.is_open
        
    def get_partitions(self) -> List[Dict[str, Any]]:
        if not self.is_open:
            return []
        return [{'index': 0, 'type': 'Mock Partition', 'start': 0, 'length': 1024*1024, 'flags': 0}]
        
    def open_file_system(self, partition_offset: int = 0) -> bool:
        return self.is_open
        
    def get_file_entries(self, path: str = "/") -> List[FileEntry]:
        if not self.is_open:
            return []
            
        # Return some mock entries
        entries = []
        for i in range(3):
            entry = FileEntry()
            entry.name = f"MockFile{i}.txt"
            entry.path = f"{path}/{entry.name}"
            entry.size = 1024 * (i + 1)
            entry.is_directory = False
            entry.created_time = datetime.now()
            entries.append(entry)
            
        return entries
        
    def get_file_content(self, file_path: str) -> Optional[bytes]:
        return b"Mock file content"
        
    def walk_file_system(self) -> Iterator[FileEntry]:
        for entry in self.get_file_entries():
            yield entry
            
    def close(self):
        self.is_open = False


def get_parser() -> IImageParser:
    """Factory function to get appropriate parser"""
    if PYTSK3_AVAILABLE:
        return PyTSKParser()
    else:
        logging.warning("Using mock parser - install pytsk3 for full functionality")
        return MockParser()