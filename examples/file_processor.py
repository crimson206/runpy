#!/usr/bin/env python3
"""
File Processor Example - File Operations with Runpy

This example demonstrates file operations, path handling, and complex
return types with Runpy.
"""

from runpycli import Runpy
from pydantic import BaseModel, Field
from pathlib import Path
from typing import List, Dict, Optional, Any
import json
import hashlib
import mimetypes
from datetime import datetime

# Create Runpy instance
cli = Runpy(name="fileproc", version="1.0.0")

class FileInfo(BaseModel):
    """File information model"""
    path: str = Field(..., description="File path")
    size_bytes: int = Field(..., description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    created: Optional[str] = Field(None, description="Creation time")
    modified: Optional[str] = Field(None, description="Last modification time")

class ProcessingOptions(BaseModel):
    """File processing options"""
    calculate_hash: bool = Field(False, description="Calculate file hash")
    hash_algorithm: str = Field("sha256", description="Hash algorithm (md5, sha1, sha256)")
    include_content: bool = Field(False, description="Include file content in output")
    max_content_size: int = Field(1024*1024, description="Max file size to include content (bytes)")

@cli.register
def analyze_file(file_path: str, options: Optional[ProcessingOptions] = None) -> dict:
    """Analyze a single file and return detailed information
    
    Examines a file and returns comprehensive metadata including size, type,
    timestamps, permissions, and optionally file content and hash.
    
    Args:
        file_path: Path to the file to analyze
        options: Processing options for hash calculation and content inclusion
        
    Returns:
        Dictionary containing file analysis results and metadata
        
    Example:
        fileproc analyze-file --file-path "/path/to/file.txt"
        fileproc analyze-file --file-path "/path/to/file.txt" --options '{"calculate_hash": true}'
    """
    path = Path(file_path)
    
    if not path.exists():
        return {
            "status": "error",
            "message": f"File not found: {file_path}"
        }
    
    if not path.is_file():
        return {
            "status": "error",
            "message": f"Path is not a file: {file_path}"
        }
    
    # Default options
    if options is None:
        options = ProcessingOptions()
    
    # Get file stats
    stat = path.stat()
    
    # Build file info
    file_info = {
        "path": str(path.absolute()),
        "name": path.name,
        "extension": path.suffix,
        "size_bytes": stat.st_size,
        "size_human": _format_size(stat.st_size),
        "mime_type": mimetypes.guess_type(str(path))[0],
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "is_readable": path.readable(),
        "is_writable": path.writable(),
    }
    
    # Calculate hash if requested
    if options.calculate_hash:
        try:
            file_info["hash"] = _calculate_hash(path, options.hash_algorithm)
        except Exception as e:
            file_info["hash_error"] = str(e)
    
    # Include content if requested and file is small enough
    if options.include_content and stat.st_size <= options.max_content_size:
        try:
            if file_info["mime_type"] and file_info["mime_type"].startswith("text/"):
                with open(path, 'r', encoding='utf-8') as f:
                    file_info["content"] = f.read()
            else:
                file_info["content"] = "<binary file>"
        except Exception as e:
            file_info["content_error"] = str(e)
    
    return {
        "status": "success",
        "file_info": file_info
    }

@cli.register
def analyze_directory(dir_path: str, recursive: bool = False, pattern: str = "*") -> dict:
    """Analyze all files in a directory"""
    path = Path(dir_path)
    
    if not path.exists():
        return {
            "status": "error",
            "message": f"Directory not found: {dir_path}"
        }
    
    if not path.is_dir():
        return {
            "status": "error",
            "message": f"Path is not a directory: {dir_path}"
        }
    
    files = []
    total_size = 0
    
    # Get files based on recursive flag
    if recursive:
        file_paths = path.rglob(pattern)
    else:
        file_paths = path.glob(pattern)
    
    # Analyze each file
    for file_path in file_paths:
        if file_path.is_file():
            stat = file_path.stat()
            files.append({
                "path": str(file_path.relative_to(path)),
                "absolute_path": str(file_path.absolute()),
                "size_bytes": stat.st_size,
                "size_human": _format_size(stat.st_size),
                "extension": file_path.suffix,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
            total_size += stat.st_size
    
    # Sort by size (largest first)
    files.sort(key=lambda x: x["size_bytes"], reverse=True)
    
    # Get extension statistics
    ext_stats = {}
    for file_info in files:
        ext = file_info["extension"] or "(no extension)"
        if ext not in ext_stats:
            ext_stats[ext] = {"count": 0, "total_size": 0}
        ext_stats[ext]["count"] += 1
        ext_stats[ext]["total_size"] += file_info["size_bytes"]
    
    return {
        "status": "success",
        "directory": str(path.absolute()),
        "total_files": len(files),
        "total_size_bytes": total_size,
        "total_size_human": _format_size(total_size),
        "files": files,
        "extension_stats": ext_stats
    }

@cli.register
def find_duplicates(dir_path: str, recursive: bool = True) -> dict:
    """Find duplicate files based on content hash"""
    path = Path(dir_path)
    
    if not path.exists() or not path.is_dir():
        return {
            "status": "error",
            "message": f"Invalid directory: {dir_path}"
        }
    
    # Get all files
    if recursive:
        file_paths = [p for p in path.rglob("*") if p.is_file()]
    else:
        file_paths = [p for p in path.glob("*") if p.is_file()]
    
    # Calculate hashes
    hash_to_files = {}
    processed = 0
    
    for file_path in file_paths:
        try:
            file_hash = _calculate_hash(file_path, "sha256")
            if file_hash not in hash_to_files:
                hash_to_files[file_hash] = []
            hash_to_files[file_hash].append({
                "path": str(file_path.relative_to(path)),
                "absolute_path": str(file_path.absolute()),
                "size_bytes": file_path.stat().st_size,
                "size_human": _format_size(file_path.stat().st_size)
            })
            processed += 1
        except Exception as e:
            continue  # Skip files we can't read
    
    # Find duplicates
    duplicates = {}
    total_duplicate_size = 0
    
    for file_hash, files in hash_to_files.items():
        if len(files) > 1:
            duplicates[file_hash] = files
            # Calculate wasted space (all copies except one)
            file_size = files[0]["size_bytes"]
            total_duplicate_size += file_size * (len(files) - 1)
    
    return {
        "status": "success",
        "directory": str(path.absolute()),
        "total_files_processed": processed,
        "duplicate_groups": len(duplicates),
        "total_duplicates": sum(len(files) - 1 for files in duplicates.values()),
        "wasted_space_bytes": total_duplicate_size,
        "wasted_space_human": _format_size(total_duplicate_size),
        "duplicates": duplicates
    }

@cli.register
def create_manifest(dir_path: str, output_file: Optional[str] = None) -> dict:
    """Create a manifest file listing all files with their hashes"""
    path = Path(dir_path)
    
    if not path.exists() or not path.is_dir():
        return {
            "status": "error",
            "message": f"Invalid directory: {dir_path}"
        }
    
    manifest = []
    file_paths = [p for p in path.rglob("*") if p.is_file()]
    
    for file_path in file_paths:
        try:
            stat = file_path.stat()
            manifest.append({
                "path": str(file_path.relative_to(path)),
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "sha256": _calculate_hash(file_path, "sha256")
            })
        except Exception:
            continue  # Skip files we can't process
    
    # Save manifest if output file specified
    if output_file:
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False, separators=(',', ': '))
    
    return {
        "status": "success",
        "directory": str(path.absolute()),
        "total_files": len(manifest),
        "manifest_file": output_file,
        "manifest": manifest
    }

def _format_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def _calculate_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculate hash of a file"""
    hash_func = getattr(hashlib, algorithm.lower())()
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

if __name__ == "__main__":
    cli.app()