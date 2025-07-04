"""
Report generation for forensic analysis results
"""
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
import hashlib


class ReportGenerator:
    """Generate comprehensive forensic analysis reports"""
    
    def __init__(self, case_path: str):
        self.case_path = case_path
        self.case_db_path = os.path.join(case_path, "case_metadata.db")
        
    def generate_case_report(self) -> Dict[str, Any]:
        """Generate a comprehensive case report"""
        report = {
            'case_info': self._get_case_info(),
            'data_sources': self._get_data_sources(),
            'analysis_summary': self._get_analysis_summary(),
            'timestamp': datetime.now().isoformat()
        }
        
        return report
        
    def _get_case_info(self) -> Dict[str, Any]:
        """Get case information from database"""
        conn = sqlite3.connect(self.case_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT case_name, case_number, case_type, description,
                   investigator_name, investigator_organization,
                   creation_timestamp, last_accessed_timestamp
            FROM case_details LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'case_name': row[0],
                'case_number': row[1],
                'case_type': row[2],
                'description': row[3],
                'investigator_name': row[4],
                'investigator_organization': row[5],
                'created': row[6],
                'last_accessed': row[7]
            }
        return {}
        
    def _get_data_sources(self) -> List[Dict[str, Any]]:
        """Get data sources from database"""
        conn = sqlite3.connect(self.case_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT source_type, path, name, description, added_timestamp
            FROM data_sources
            ORDER BY added_timestamp
        """)
        
        sources = []
        for row in cursor.fetchall():
            sources.append({
                'type': row[0],
                'path': row[1],
                'name': row[2],
                'description': row[3],
                'added': row[4]
            })
            
        conn.close()
        return sources
        
    def _get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of analysis performed"""
        summary = {
            'carved_files': self._count_carved_files(),
            'timestamp_analysis': self._check_timestamp_analysis(),
            'file_system_parsed': self._check_file_system_parsing()
        }
        return summary
        
    def _count_carved_files(self) -> int:
        """Count carved files in case directory"""
        carved_dir = os.path.join(self.case_path, "carved_files")
        if os.path.exists(carved_dir):
            return len([f for f in os.listdir(carved_dir) if os.path.isfile(os.path.join(carved_dir, f))])
        return 0
        
    def _check_timestamp_analysis(self) -> bool:
        """Check if timestamp analysis was performed"""
        # Check for timestamp analysis results file
        return os.path.exists(os.path.join(self.case_path, "timestamp_analysis.json"))
        
    def _check_file_system_parsing(self) -> bool:
        """Check if file system was parsed"""
        # Check for file listing export
        return os.path.exists(os.path.join(self.case_path, "file_list.csv"))
        
    def export_html_report(self, output_path: str, include_details: bool = True):
        """Export report as HTML"""
        report_data = self.generate_case_report()
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ByteProbe Forensic Report - {report_data['case_info'].get('case_name', 'Unknown Case')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 10px;
            margin: 20px 0;
        }}
        .label {{
            font-weight: bold;
            color: #555;
        }}
        .value {{
            color: #333;
        }}
        .data-source {{
            background-color: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #3498db;
        }}
        .summary-box {{
            background-color: #e8f4f8;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            color: #777;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>ByteProbe Forensic Analysis Report</h1>
        
        <h2>Case Information</h2>
        <div class="info-grid">
            <div class="label">Case Name:</div>
            <div class="value">{report_data['case_info'].get('case_name', 'N/A')}</div>
            
            <div class="label">Case Number:</div>
            <div class="value">{report_data['case_info'].get('case_number', 'N/A')}</div>
            
            <div class="label">Case Type:</div>
            <div class="value">{report_data['case_info'].get('case_type', 'N/A')}</div>
            
            <div class="label">Investigator:</div>
            <div class="value">{report_data['case_info'].get('investigator_name', 'N/A')}</div>
            
            <div class="label">Organization:</div>
            <div class="value">{report_data['case_info'].get('investigator_organization', 'N/A')}</div>
            
            <div class="label">Created:</div>
            <div class="value">{report_data['case_info'].get('created', 'N/A')}</div>
        </div>
        
        <h2>Data Sources</h2>
        """
        
        for source in report_data['data_sources']:
            html += f"""
        <div class="data-source">
            <strong>{source['name']}</strong> ({source['type']})<br>
            Path: {source['path']}<br>
            {f"Description: {source['description']}<br>" if source['description'] else ""}
            Added: {source['added']}
        </div>
            """
            
        summary = report_data['analysis_summary']
        html += f"""
        <h2>Analysis Summary</h2>
        <div class="summary-box">
            <p><strong>Carved Files:</strong> {summary['carved_files']}</p>
            <p><strong>File System Parsed:</strong> {'Yes' if summary['file_system_parsed'] else 'No'}</p>
            <p><strong>Timestamp Analysis:</strong> {'Performed' if summary['timestamp_analysis'] else 'Not performed'}</p>
        </div>
        
        <div class="footer">
            <p>Generated by ByteProbe on {report_data['timestamp']}</p>
        </div>
    </div>
</body>
</html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
            
    def export_text_report(self, output_path: str):
        """Export report as plain text"""
        report_data = self.generate_case_report()
        
        lines = []
        lines.append("=" * 60)
        lines.append("BYTEPROBE FORENSIC ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append("")
        
        # Case info
        lines.append("CASE INFORMATION")
        lines.append("-" * 30)
        info = report_data['case_info']
        lines.append(f"Case Name: {info.get('case_name', 'N/A')}")
        lines.append(f"Case Number: {info.get('case_number', 'N/A')}")
        lines.append(f"Case Type: {info.get('case_type', 'N/A')}")
        lines.append(f"Investigator: {info.get('investigator_name', 'N/A')}")
        lines.append(f"Organization: {info.get('investigator_organization', 'N/A')}")
        lines.append(f"Created: {info.get('created', 'N/A')}")
        lines.append(f"Last Accessed: {info.get('last_accessed', 'N/A')}")
        lines.append("")
        
        # Data sources
        lines.append("DATA SOURCES")
        lines.append("-" * 30)
        for i, source in enumerate(report_data['data_sources'], 1):
            lines.append(f"{i}. {source['name']} ({source['type']})")
            lines.append(f"   Path: {source['path']}")
            if source['description']:
                lines.append(f"   Description: {source['description']}")
            lines.append(f"   Added: {source['added']}")
            lines.append("")
            
        # Analysis summary
        lines.append("ANALYSIS SUMMARY")
        lines.append("-" * 30)
        summary = report_data['analysis_summary']
        lines.append(f"Carved Files: {summary['carved_files']}")
        lines.append(f"File System Parsed: {'Yes' if summary['file_system_parsed'] else 'No'}")
        lines.append(f"Timestamp Analysis: {'Performed' if summary['timestamp_analysis'] else 'Not performed'}")
        lines.append("")
        
        lines.append("=" * 60)
        lines.append(f"Report generated on {report_data['timestamp']}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))