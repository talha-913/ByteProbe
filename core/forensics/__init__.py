"""
forensics analysis modules
"""
from .file_signatures import FileSignature, FILE_SIGNATURES, get_signature, identify_file_type

__all__ = ['FileSignature', 'FILE_SIGNATURES', 'get_signature', 'identify_file_type']