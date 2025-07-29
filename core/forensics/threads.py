"""
Thread classes for forensic operations
"""
from PyQt6.QtCore import QThread, pyqtSignal
from typing import List, Dict, Any

from ..parsers.pytsk_parser import get_parser
from .file_carver import SmartFileCarver
from .timestamp_analyzer import NTFSTimestampAnalyzer


class FileCarverThread(QThread):
    """Thread for file carving operation"""
    
    progress = pyqtSignal(int, str)
    file_carved = pyqtSignal(dict)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, image_path: str, output_dir: str, file_types: List[str]):
        super().__init__()
        self.image_path = image_path
        self.output_dir = output_dir
        self.file_types = file_types
        self.carver = None
        
    def run(self):
        """Run the carving process"""
        try:
            parser = get_parser()
            self.carver = SmartFileCarver(parser)
            
            def progress_callback(percent, message):
                self.progress.emit(percent, message)
                
            # Carve files
            carved_files = self.carver.carve_files(
                self.image_path,
                self.output_dir,
                self.file_types,
                progress_callback
            )
            
            # Emit each carved file
            for file_info in carved_files:
                self.file_carved.emit(file_info)
                
            self.finished.emit(True, f"Successfully carved {len(carved_files)} files")
            
        except Exception as e:
            self.finished.emit(False, str(e))
            
    def stop(self):
        """Stop the carving process"""
        if self.carver:
            self.carver.stop_carving()


class TimestampAnalysisThread(QThread):
    """Thread for timestamp analysis"""
    
    progress = pyqtSignal(int, str)
    file_analyzed = pyqtSignal(dict)
    finished = pyqtSignal(dict)
    
    def __init__(self, image_path: str, target_path: str = "/"):
        super().__init__()
        self.image_path = image_path
        self.target_path = target_path
        self.analyzer = NTFSTimestampAnalyzer()
        
    def run(self):
        """Run the analysis"""
        try:
            parser = get_parser()
            
            self.progress.emit(10, "Opening disk image...")
            if not parser.open_image(self.image_path):
                raise Exception("Failed to open disk image")
                
            self.progress.emit(20, "Opening file system...")
            if not parser.open_file_system():
                raise Exception("Failed to open file system")
                
            self.progress.emit(30, "Collecting files...")
            
            # Collect all files
            all_files = []
            file_count = 0
            
            for entry in parser.walk_file_system():
                all_files.append(entry)
                file_count += 1
                
                if file_count % 100 == 0:
                    self.progress.emit(
                        min(30 + (file_count // 10), 70),
                        f"Found {file_count} files..."
                    )
                    
            # Analyze files
            self.progress.emit(70, "Analyzing timestamps...")
            results = self.analyzer.analyze_directory(all_files)
            
            # Emit individual suspicious files
            for suspicious_file in results['suspicious_files']:
                self.file_analyzed.emit(suspicious_file)
                
            self.progress.emit(100, "Analysis complete!")
            self.finished.emit(results)
            
        except Exception as e:
            self.finished.emit({'error': str(e)})
        finally:
            parser.close()