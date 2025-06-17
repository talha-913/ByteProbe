"""
Core interfaces for ByteProbe forensics tool
"""
from .image_parser import IImageParser, IFileCarver, ITimestampAnalyzer, FileEntry

__all__ = ['IImageParser', 'IFileCarver', 'ITimestampAnalyzer', 'FileEntry']