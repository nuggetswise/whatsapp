import os
import tempfile
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import shutil

class ResumeStorage:
    def __init__(self, storage_type: str = "local", config: Dict[str, Any] = None):
        """
        Initialize resume storage.
        
        Args:
            storage_type: "local" or "cloud" (S3, GCS, etc.)
            config: Configuration for cloud storage
        """
        self.storage_type = storage_type
        self.config = config or {}
        
        if storage_type == "local":
            self.storage_dir = "uploads"
            os.makedirs(self.storage_dir, exist_ok=True)
    
    def store_resume(self, file_content: bytes, filename: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Store a resume file.
        
        Args:
            file_content: The file content as bytes
            filename: Original filename (optional)
            metadata: Additional metadata
        
        Returns:
            Dict with storage info
        """
        if self.storage_type == "local":
            return self._store_local(file_content, filename, metadata)
        else:
            return self._store_cloud(file_content, filename, metadata)
    
    def _store_local(self, file_content: bytes, filename: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Store file locally."""
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        
        if filename:
            # Extract extension
            _, ext = os.path.splitext(filename)
            if not ext:
                ext = ".pdf"  # Default to PDF
        else:
            ext = ".pdf"
        
        storage_filename = f"resume_{timestamp}_{unique_id}{ext}"
        filepath = os.path.join(self.storage_dir, storage_filename)
        
        # Write file
        with open(filepath, 'wb') as f:
            f.write(file_content)
        
        # Store metadata
        metadata_file = filepath + ".meta"
        file_metadata = {
            "original_filename": filename,
            "storage_filename": storage_filename,
            "file_size": len(file_content),
            "upload_time": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        with open(metadata_file, 'w') as f:
            import json
            json.dump(file_metadata, f, indent=2)
        
        return {
            "success": True,
            "filepath": filepath,
            "filename": storage_filename,
            "size_bytes": len(file_content),
            "size_mb": round(len(file_content) / (1024 * 1024), 2),
            "metadata": file_metadata
        }
    
    def _store_cloud(self, file_content: bytes, filename: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Store file in cloud storage (placeholder for future implementation)."""
        # This would integrate with AWS S3, Google Cloud Storage, etc.
        # For now, fall back to local storage
        return self._store_local(file_content, filename, metadata)
    
    def get_resume(self, filename: str) -> Optional[bytes]:
        """Retrieve a stored resume."""
        if self.storage_type == "local":
            filepath = os.path.join(self.storage_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    return f.read()
        return None
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old files to save storage."""
        if self.storage_type == "local":
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            for filename in os.listdir(self.storage_dir):
                filepath = os.path.join(self.storage_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                
                if file_time < cutoff_time:
                    try:
                        os.remove(filepath)
                        # Also remove metadata file if it exists
                        meta_file = filepath + ".meta"
                        if os.path.exists(meta_file):
                            os.remove(meta_file)
                        print(f"Cleaned up old file: {filename}")
                    except Exception as e:
                        print(f"Error cleaning up {filename}: {e}")

# Convenience function
def store_resume_file(file_content: bytes, filename: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Store a resume file using the default storage method."""
    storage = ResumeStorage()
    return storage.store_resume(file_content, filename, metadata) 