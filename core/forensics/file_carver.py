"""
File carving implementation for recovering deleted files
"""
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib

from ..interfaces.image_parser import IFileCarver, IImageParser
from .file_signatures import FILE_SIGNATURES, identify_file_type, get_signature


class BasicFileCarver(IFileCarver):
    """Basic file carving implementation using header/footer signatures"""
    
    def __init__(self, parser: IImageParser):
        self.parser = parser
        self.carved_files = []
        self._stop_carving = False
        
    def carve_files(self, image_path: str, output_dir: str, 
                   file_types: Optional[List[str]] = None,
                   progress_callback=None) -> List[Dict[str, Any]]:
        """
        Carve files from disk image
        :param image_path: Path to disk image
        :param output_dir: Directory to save carved files
        :param file_types: List of file types to carve (None = all)
        :param progress_callback: Callback function for progress updates
        :return: List of carved file information
        """
        self.carved_files = []
        self._stop_carving = False
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Get signatures to search for
        if file_types:
            signatures = {ft: FILE_SIGNATURES[ft] for ft in file_types 
                         if ft in FILE_SIGNATURES}
        else:
            signatures = FILE_SIGNATURES
            
        if not signatures:
            logging.warning("No valid file signatures to search for")
            return []
            
        try:
            # Open image
            if not self.parser.open_image(image_path):
                raise Exception("Failed to open disk image")
                
            # Get image size
            if hasattr(self.parser, 'img_info'):
                image_size = self.parser.img_info.get_size()
            else:
                # Fallback for mock parser
                image_size = 1024 * 1024 * 100  # 100MB default
                
            # Read image in chunks
            chunk_size = 1024 * 1024  # 1MB chunks
            offset = 0
            
            # Buffer to handle signatures spanning chunks
            buffer = b""
            buffer_offset = 0
            
            while offset < image_size and not self._stop_carving:
                # Read chunk
                if hasattr(self.parser, 'img_info'):
                    chunk = self.parser.img_info.read(offset, chunk_size)
                else:
                    # Mock implementation
                    chunk = b'\x00' * min(chunk_size, image_size - offset)
                    
                if not chunk:
                    break
                    
                # Add to buffer
                buffer = buffer[-1024:] + chunk  # Keep last 1KB from previous chunk
                
                # Search for headers in buffer
                for ext, sig in signatures.items():
                    if not sig.header:
                        continue
                        
                    # Find all occurrences of header
                    header_pos = 0
                    while True:
                        header_pos = buffer.find(sig.header, header_pos)
                        if header_pos == -1:
                            break
                            
                        # Calculate actual file offset
                        file_offset = offset + header_pos - (len(buffer) - len(chunk))
                        
                        # Try to carve file
                        carved_file = self._carve_single_file(
                            sig, file_offset, image_size, output_dir
                        )
                        
                        if carved_file:
                            self.carved_files.append(carved_file)
                            
                        header_pos += 1
                        
                # Update progress
                if progress_callback:
                    progress = int((offset / image_size) * 100)
                    progress_callback(progress, f"Scanning: {offset // (1024*1024)}MB / {image_size // (1024*1024)}MB")
                    
                offset += chunk_size
                
        except Exception as e:
            logging.error(f"Error during file carving: {e}")
            
        finally:
            self.parser.close()
            
        return self.carved_files
        
    def _carve_single_file(self, signature, start_offset: int, 
                          max_offset: int, output_dir: str) -> Optional[Dict[str, Any]]:
        """Carve a single file starting at given offset"""
        try:
            # Read file data
            file_data = b""
            current_offset = start_offset
            found_footer = False
            
            # Read until footer found or max size reached
            while current_offset < max_offset and len(file_data) < signature.max_size:
                # Read in chunks
                chunk_size = min(1024 * 1024, signature.max_size - len(file_data))
                
                if hasattr(self.parser, 'img_info'):
                    chunk = self.parser.img_info.read(current_offset, chunk_size)
                else:
                    # Mock data
                    chunk = b'\x00' * chunk_size
                    
                if not chunk:
                    break
                    
                file_data += chunk
                
                # Check for footer
                if signature.footer:
                    footer_pos = file_data.find(signature.footer)
                    if footer_pos != -1:
                        file_data = file_data[:footer_pos + len(signature.footer)]
                        found_footer = True
                        break
                        
                current_offset += chunk_size
                
            # Validate carved file
            if len(file_data) < 512:  # Too small
                return None
                
            if signature.footer and not found_footer:
                # No footer found, might be incomplete
                pass
                
            # Generate filename
            file_hash = hashlib.md5(file_data[:1024]).hexdigest()[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"carved_{timestamp}_{file_hash}.{signature.extension}"
            filepath = os.path.join(output_dir, filename)
            
            # Save file
            with open(filepath, 'wb') as f:
                f.write(file_data)
                
            # Return carved file info
            return {
                'filename': filename,
                'path': filepath,
                'type': signature.extension,
                'size': len(file_data),
                'offset': start_offset,
                'footer_found': found_footer,
                'hash_md5': hashlib.md5(file_data).hexdigest(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error carving file at offset {start_offset}: {e}")
            return None
            
    def stop_carving(self):
        """Stop the carving process"""
        self._stop_carving = True


class SmartFileCarver(BasicFileCarver):
    """Enhanced file carver with validation and optimization"""
    
    def _carve_single_file(self, signature, start_offset: int, 
                          max_offset: int, output_dir: str) -> Optional[Dict[str, Any]]:
        """Enhanced carving with file validation"""
        result = super()._carve_single_file(signature, start_offset, max_offset, output_dir)
        
        if result:
            # Additional validation based on file type
            if signature.extension in ['jpg', 'jpeg']:
                # Validate JPEG structure
                if not self._validate_jpeg(result['path']):
                    os.remove(result['path'])
                    return None
                    
            elif signature.extension == 'pdf':
                # Validate PDF structure
                if not self._validate_pdf(result['path']):
                    os.remove(result['path'])
                    return None
                    
        return result
        
    def _validate_jpeg(self, filepath: str) -> bool:
        """Basic JPEG validation"""
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
                # Check for proper JPEG markers
                if not data.startswith(b'\xFF\xD8'):
                    return False
                if not data.endswith(b'\xFF\xD9'):
                    return False
                # Could add more validation here
                return True
        except:
            return False
            
    def _validate_pdf(self, filepath: str) -> bool:
        """Basic PDF validation"""
        try:
            with open(filepath, 'rb') as f:
                data = f.read(1024)
                # Check PDF header
                if not data.startswith(b'%PDF'):
                    return False
                # Could check for xref table, etc.
                return True
        except:
            return False