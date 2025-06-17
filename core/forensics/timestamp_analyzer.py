"""
Timestamp analysis for detecting manipulation
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics

from ..interfaces.image_parser import ITimestampAnalyzer, FileEntry


class NTFSTimestampAnalyzer(ITimestampAnalyzer):
    """Analyzes NTFS timestamps for signs of manipulation"""
    
    def __init__(self):
        self.anomalies = []
        
    def analyze_timestamps(self, file_entry: FileEntry) -> Dict[str, Any]:
        """
        Analyze timestamps for manipulation
        
        NTFS has two sets of timestamps:
        - $STANDARD_INFORMATION (SI): Can be easily modified by users
        - $FILE_NAME (FN): More difficult to modify, updated by system
        
        Signs of manipulation:
        1. SI timestamps newer than FN timestamps
        2. Identical timestamps (especially to the second)
        3. Timestamps outside expected range
        4. Inconsistent timestamp patterns
        """
        
        result = {
            'file_path': file_entry.path,
            'anomalies': [],
            'confidence': 0.0,
            'details': {}
        }
        
        # Check for basic timestamp presence
        if not all([file_entry.created_time, file_entry.modified_time, file_entry.accessed_time]):
            result['anomalies'].append({
                'type': 'missing_timestamps',
                'description': 'One or more timestamps are missing',
                'severity': 'low'
            })
            return result
            
        # Check for identical timestamps
        if self._check_identical_timestamps(file_entry):
            result['anomalies'].append({
                'type': 'identical_timestamps',
                'description': 'All timestamps are identical (possible timestomping)',
                'severity': 'high'
            })
            result['confidence'] += 0.4
            
        # Check for timestamp order anomalies
        order_anomaly = self._check_timestamp_order(file_entry)
        if order_anomaly:
            result['anomalies'].append(order_anomaly)
            result['confidence'] += 0.3
            
        # Check for precision anomalies
        precision_anomaly = self._check_timestamp_precision(file_entry)
        if precision_anomaly:
            result['anomalies'].append(precision_anomaly)
            result['confidence'] += 0.2
            
        # Check for future timestamps
        future_anomaly = self._check_future_timestamps(file_entry)
        if future_anomaly:
            result['anomalies'].append(future_anomaly)
            result['confidence'] += 0.5
            
        # Calculate final confidence score
        result['confidence'] = min(result['confidence'], 1.0)
        
        # Add timestamp details
        result['details'] = {
            'created': file_entry.created_time.isoformat() if file_entry.created_time else None,
            'modified': file_entry.modified_time.isoformat() if file_entry.modified_time else None,
            'accessed': file_entry.accessed_time.isoformat() if file_entry.accessed_time else None,
            'mft_entry': file_entry.mft_entry
        }
        
        return result
        
    def _check_identical_timestamps(self, entry: FileEntry) -> bool:
        """Check if all timestamps are identical"""
        timestamps = [entry.created_time, entry.modified_time, entry.accessed_time]
        timestamps = [ts for ts in timestamps if ts]  # Filter None values
        
        if len(timestamps) < 2:
            return False
            
        # Check if all timestamps are the same to the second
        first_ts = timestamps[0].replace(microsecond=0)
        return all(ts.replace(microsecond=0) == first_ts for ts in timestamps[1:])
        
    def _check_timestamp_order(self, entry: FileEntry) -> Optional[Dict[str, Any]]:
        """Check for logical timestamp order"""
        # Normal order: created <= modified <= accessed
        # But accessed can be disabled in NTFS
        
        if entry.created_time and entry.modified_time:
            if entry.created_time > entry.modified_time:
                return {
                    'type': 'illogical_order',
                    'description': 'Created time is after modified time',
                    'severity': 'medium'
                }
                
        return None
        
    def _check_timestamp_precision(self, entry: FileEntry) -> Optional[Dict[str, Any]]:
        """Check timestamp precision patterns"""
        # NTFS timestamps have 100-nanosecond precision
        # Many timestomping tools only set to second precision
        
        timestamps = [entry.created_time, entry.modified_time, entry.accessed_time]
        timestamps = [ts for ts in timestamps if ts]
        
        # Check if all timestamps have zero microseconds
        zero_microseconds = all(ts.microsecond == 0 for ts in timestamps)
        
        if zero_microseconds and len(timestamps) >= 2:
            return {
                'type': 'zero_precision',
                'description': 'All timestamps have zero microseconds (possible tool usage)',
                'severity': 'medium'
            }
            
        return None
        
    def _check_future_timestamps(self, entry: FileEntry) -> Optional[Dict[str, Any]]:
        """Check for timestamps in the future"""
        current_time = datetime.now()
        future_threshold = current_time + timedelta(days=1)  # Allow 1 day tolerance
        
        timestamps = [
            ('created', entry.created_time),
            ('modified', entry.modified_time),
            ('accessed', entry.accessed_time)
        ]
        
        future_timestamps = [(name, ts) for name, ts in timestamps 
                            if ts and ts > future_threshold]
        
        if future_timestamps:
            return {
                'type': 'future_timestamp',
                'description': f'Timestamp(s) in the future: {", ".join(name for name, _ in future_timestamps)}',
                'severity': 'high'
            }
            
        return None
        
    def analyze_directory(self, entries: List[FileEntry]) -> Dict[str, Any]:
        """Analyze timestamps across multiple files for patterns"""
        results = {
            'total_files': len(entries),
            'suspicious_files': [],
            'patterns': [],
            'statistics': {}
        }
        
        # Analyze each file
        file_results = []
        for entry in entries:
            if not entry.is_directory:
                analysis = self.analyze_timestamps(entry)
                if analysis['anomalies']:
                    results['suspicious_files'].append(analysis)
                file_results.append(analysis)
                
        # Look for patterns across files
        patterns = self._find_timestamp_patterns(entries)
        results['patterns'] = patterns
        
        # Calculate statistics
        if file_results:
            confidence_scores = [r['confidence'] for r in file_results]
            results['statistics'] = {
                'average_confidence': statistics.mean(confidence_scores) if confidence_scores else 0,
                'max_confidence': max(confidence_scores) if confidence_scores else 0,
                'files_with_anomalies': len(results['suspicious_files'])
            }
            
        return results
        
    def _find_timestamp_patterns(self, entries: List[FileEntry]) -> List[Dict[str, Any]]:
        """Find suspicious patterns across multiple files"""
        patterns = []
        
        # Group files by identical timestamps
        timestamp_groups = {}
        for entry in entries:
            if entry.modified_time:
                ts_key = entry.modified_time.replace(microsecond=0).isoformat()
                if ts_key not in timestamp_groups:
                    timestamp_groups[ts_key] = []
                timestamp_groups[ts_key].append(entry.path)
                
        # Find groups with multiple files
        for ts_key, files in timestamp_groups.items():
            if len(files) > 3:  # More than 3 files with same timestamp
                patterns.append({
                    'type': 'mass_timestamp',
                    'description': f'{len(files)} files have identical modification time',
                    'timestamp': ts_key,
                    'file_count': len(files),
                    'sample_files': files[:5]  # Show first 5
                })
                
        return patterns


class TimestampReport:
    """Generate timestamp analysis reports"""
    
    @staticmethod
    def generate_summary(analysis_results: Dict[str, Any]) -> str:
        """Generate a summary report of timestamp analysis"""
        lines = []
        lines.append("=== Timestamp Analysis Report ===\n")
        
        lines.append(f"Total Files Analyzed: {analysis_results['total_files']}")
        lines.append(f"Suspicious Files Found: {len(analysis_results['suspicious_files'])}")
        
        if analysis_results['statistics']:
            stats = analysis_results['statistics']
            lines.append(f"\nSuspicion Statistics:")
            lines.append(f"  Average Confidence: {stats['average_confidence']:.2%}")
            lines.append(f"  Maximum Confidence: {stats['max_confidence']:.2%}")
            
        if analysis_results['patterns']:
            lines.append(f"\nSuspicious Patterns Found:")
            for pattern in analysis_results['patterns']:
                lines.append(f"  - {pattern['description']}")
                
        if analysis_results['suspicious_files']:
            lines.append(f"\nTop Suspicious Files:")
            # Sort by confidence
            sorted_files = sorted(analysis_results['suspicious_files'], 
                                key=lambda x: x['confidence'], reverse=True)
            
            for i, file_result in enumerate(sorted_files[:10]):
                lines.append(f"\n{i+1}. {file_result['file_path']}")
                lines.append(f"   Confidence: {file_result['confidence']:.2%}")
                lines.append(f"   Anomalies:")
                for anomaly in file_result['anomalies']:
                    lines.append(f"     - {anomaly['description']} ({anomaly['severity']})")
                    
        return '\n'.join(lines)