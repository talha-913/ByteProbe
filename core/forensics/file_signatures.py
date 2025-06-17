"""
File signatures for file carving
"""
from typing import Dict, List, Tuple, Optional

class FileSignature:
    """Represents a file type signature"""
    def __init__(self, extension: str, description: str, 
                 header: bytes, footer: Optional[bytes] = None,
                 max_size: Optional[int] = None):
        self.extension = extension
        self.description = description
        self.header = header
        self.footer = footer
        self.max_size = max_size or (100 * 1024 * 1024)  # Default 100MB
        
    def __repr__(self):
        return f"<FileSignature: {self.extension} - {self.description}>"


# Common file signatures database
FILE_SIGNATURES = {
    'jpg': FileSignature(
        'jpg',
        'JPEG Image',
        header=b'\xFF\xD8\xFF',
        footer=b'\xFF\xD9',
        max_size=50 * 1024 * 1024  # 50MB
    ),
    'png': FileSignature(
        'png',
        'PNG Image',
        header=b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A',
        footer=b'\x49\x45\x4E\x44\xAE\x42\x60\x82',
        max_size=50 * 1024 * 1024
    ),
    'gif': FileSignature(
        'gif',
        'GIF Image',
        header=b'GIF87a',  # or GIF89a
        footer=b'\x00\x3B',
        max_size=20 * 1024 * 1024
    ),
    'pdf': FileSignature(
        'pdf',
        'PDF Document',
        header=b'%PDF',
        footer=b'%%EOF',
        max_size=500 * 1024 * 1024  # 500MB
    ),
    'docx': FileSignature(
        'docx',
        'Microsoft Word Document',
        header=b'\x50\x4B\x03\x04',  # ZIP header
        footer=None,  # Variable
        max_size=100 * 1024 * 1024
    ),
    'xlsx': FileSignature(
        'xlsx',
        'Microsoft Excel Document',
        header=b'\x50\x4B\x03\x04',  # ZIP header
        footer=None,
        max_size=100 * 1024 * 1024
    ),
    'zip': FileSignature(
        'zip',
        'ZIP Archive',
        header=b'\x50\x4B\x03\x04',
        footer=b'\x50\x4B\x05\x06',  # End of central directory
        max_size=1024 * 1024 * 1024  # 1GB
    ),
    'mp4': FileSignature(
        'mp4',
        'MP4 Video',
        header=b'\x00\x00\x00\x20\x66\x74\x79\x70',  # ftyp box
        footer=None,
        max_size=4096 * 1024 * 1024  # 4GB
    ),
    'exe': FileSignature(
        'exe',
        'Windows Executable',
        header=b'MZ',  # DOS header
        footer=None,
        max_size=500 * 1024 * 1024
    ),
    'txt': FileSignature(
        'txt',
        'Plain Text File',
        header=None,  # No specific header
        footer=None,
        max_size=10 * 1024 * 1024
    )
}

# Alternative headers for some file types
ALTERNATIVE_HEADERS = {
    'gif': [b'GIF87a', b'GIF89a'],
    'jpg': [b'\xFF\xD8\xFF\xE0', b'\xFF\xD8\xFF\xE1', b'\xFF\xD8\xFF\xE8'],
    'docx': [b'\x50\x4B\x03\x04\x14\x00\x06\x00'],  # More specific Office signature
    'xlsx': [b'\x50\x4B\x03\x04\x14\x00\x06\x00']
}


def get_signature(file_type: str) -> Optional[FileSignature]:
    """Get file signature by extension"""
    return FILE_SIGNATURES.get(file_type.lower())


def identify_file_type(data: bytes, size_limit: int = 512) -> Optional[str]:
    """
    Identify file type from data header
    :param data: File data (at least first 512 bytes)
    :param size_limit: How many bytes to check
    :return: File extension or None
    """
    check_data = data[:size_limit]
    
    # Check each signature
    for ext, sig in FILE_SIGNATURES.items():
        if sig.header and check_data.startswith(sig.header):
            return ext
            
    # Check alternative headers
    for ext, headers in ALTERNATIVE_HEADERS.items():
        for header in headers:
            if check_data.startswith(header):
                return ext
                
    # Special case for text files (printable ASCII)
    if all(32 <= b < 127 or b in [9, 10, 13] for b in check_data[:100]):
        return 'txt'
        
    return None


def get_supported_types() -> List[str]:
    """Get list of supported file types for carving"""
    return list(FILE_SIGNATURES.keys())