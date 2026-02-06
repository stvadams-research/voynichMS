import hashlib
import os
from pathlib import Path
from typing import List, Tuple, Optional
import re

from voynich.core.ids import FolioID, PageID
from voynich.storage.metadata import MetadataStore

class DatasetManager:
    def __init__(self, metadata_store: MetadataStore):
        self.store = metadata_store

    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read and update hash string value in blocks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def infer_folio_id(self, filename: str) -> Optional[str]:
        """
        Attempt to extract a FolioID from a filename.
        Expected patterns:
        - f1r.jpg
        - f102v1.png
        - 1006264_f1r.tif (Yale style)
        """
        # Simple regex for f-number-side
        match = re.search(r"(f\d+[rv]\d*)", filename)
        if match:
            try:
                # Validate it's a real FolioID
                fid = FolioID(match.group(1))
                return fid
            except ValueError:
                return None
        return None

    def register_dataset(self, name: str, path: Path) -> List[str]:
        """
        Register a dataset and its pages.
        Returns a list of registered PageIDs.
        """
        path = Path(path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Dataset path not found: {path}")

        # Register dataset record
        # For dataset checksum, we could hash the list of file checksums, but for now we'll leave it None or implement later
        self.store.add_dataset(dataset_id=name, path=str(path))

        registered_pages = []
        
        # Scan for images
        extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
        for root, _, files in os.walk(path):
            for file in files:
                if Path(file).suffix.lower() in extensions:
                    file_path = Path(root) / file
                    
                    folio_id = self.infer_folio_id(file)
                    if not folio_id:
                        print(f"Skipping {file}: Could not infer FolioID")
                        continue

                    page_id = str(PageID(folio=folio_id))
                    checksum = self.calculate_checksum(file_path)
                    
                    # We could get width/height here using Pillow if needed, 
                    # but for Level 1 speed we might skip or do it if requested.
                    # Let's do it if Pillow is available, as it's in dependencies.
                    width, height = None, None
                    try:
                        from PIL import Image
                        with Image.open(file_path) as img:
                            width, height = img.size
                    except Exception:
                        pass

                    self.store.add_page(
                        page_id=page_id,
                        dataset_id=name,
                        image_path=str(file_path),
                        checksum=checksum,
                        width=width,
                        height=height
                    )
                    registered_pages.append(page_id)

        return registered_pages
