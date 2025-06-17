"""
Abstract interface for disk image parsers.
Following SOLID principles - Interface Segregation Principle
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime


class FileEntry:
    """Data model for a file/directory entry"""
    def __init__(self):
        self.name: str = ""
        self.path: str = ""
        self.size: int = 0
        self.is_directory: bool = False
        self.is_deleted: bool = False
        self.created_time: Optional[datetime] = None
        self.modified_time: Optional[datetime] = None
        self.accessed_time: Optional[datetime] = None
        self.mft_entry: Optional[int] = None
        self.parent_mft: Optional[int] = None
        self.attributes: Dict[str, Any] = {}
        self.children: List['FileEntry'] = []
        
    def __repr__(self):
        return f"<FileEntry: {self.path} ({'DIR' if self.is_directory else 'FILE'})>"


class IImageParser(ABC):
    """Abstract interface for disk image parsing"""
    
    @abstractmethod
    def open_image(self, image_path: str) -> bool:
        """
        Open a disk image for parsing
        :param image_path: Path to the disk image file
        :return: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_partitions(self) -> List[Dict[str, Any]]:
        """
        Get list of partitions in the image
        :return: List of partition information dictionaries
        """
        pass
    
    @abstractmethod
    def open_file_system(self, partition_offset: int = 0) -> bool:
        """
        Open a file system at the given partition offset
        :param partition_offset: Byte offset of the partition
        :return: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_file_entries(self, path: str = "/") -> List[FileEntry]:
        """
        Get file entries in a directory
        :param path: Directory path to list
        :return: List of FileEntry objects
        """
        pass
    
    @abstractmethod
    def get_file_content(self, file_path: str) -> Optional[bytes]:
        """
        Read file content
        :param file_path: Path to the file
        :return: File content as bytes or None if error
        """
        pass
    
    @abstractmethod
    def walk_file_system(self) -> Iterator[FileEntry]:
        """
        Walk through entire file system yielding each entry
        :return: Iterator of FileEntry objects
        """
        pass
    
    @abstractmethod
    def close(self):
        """Close the image and cleanup resources"""
        pass


class IFileCarver(ABC):
    """Abstract interface for file carving functionality"""
    
    @abstractmethod
    def carve_files(self, image_path: str, output_dir: str, 
                   file_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Carve files from disk image
        :param image_path: Path to disk image
        :param output_dir: Directory to save carved files
        :param file_types: List of file types to carve (e.g., ['jpg', 'pdf'])
        :return: List of carved file information
        """
        pass


class ITimestampAnalyzer(ABC):
    """Abstract interface for timestamp analysis"""
    
    @abstractmethod
    def analyze_timestamps(self, file_entry: FileEntry) -> Dict[str, Any]:
        """
        Analyze timestamps for manipulation
        :param file_entry: FileEntry to analyze
        :return: Analysis results dictionary
        """
        pass