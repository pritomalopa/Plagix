import os
import shutil
import zipfile
import hashlib
import re
from pathlib import Path
from typing import List, Tuple, Dict, Any
from fastapi import UploadFile, HTTPException, status
from pypdf import PdfReader
from docx import Document

# Limits
MAX_INDIVIDUAL_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_ZIP_SIZE = 250 * 1024 * 1024             # 250 MB
MAX_FILE_COUNT = 500
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".zip"}


def validate_file_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    return ext


def compute_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def derive_student_label(filename: str) -> Tuple[str, float]:
    """
    Derive provisional student label from filename.
    Examples:
      '12345_assignment.pdf' -> ('12345', 0.9)
      'student_one_answer.txt' -> ('student_one_answer', 0.7)
      'alice_homework.txt' -> ('alice_homework', 0.7)
    """
    clean_name = Path(filename).stem
    
    # If starts with student ID digits followed by underscore
    if re.match(r'^\d+_', clean_name):
        return clean_name.split("_")[0], 0.9
        
    return clean_name, 0.7


def safe_extract_zip(zip_path: Path, extract_to: Path) -> List[Path]:
    """
    Safely extract ZIP archive defending against path traversal, symlinks, and ZIP bombs.
    """
    extracted_files = []
    
    if zip_path.stat().st_size > MAX_ZIP_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ZIP archive exceeds 250 MB size limit."
        )

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            infolist = zf.infolist()
            if len(infolist) > MAX_FILE_COUNT:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"ZIP contains {len(infolist)} files, exceeding maximum of {MAX_FILE_COUNT}."
                )
                
            total_uncompressed = sum(info.file_size for info in infolist)
            if total_uncompressed > MAX_ZIP_SIZE * 3:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ZIP archive expansion ratio exceeds safe limits (potential ZIP bomb)."
                )

            for info in infolist:
                # Skip directories, symlinks
                if info.is_dir() or info.external_attr >> 16 == 0o120000:
                    continue
                    
                filename = Path(info.filename).name
                if not filename or filename.startswith('.'):
                    continue
                    
                ext = Path(filename).suffix.lower()
                if ext not in {".pdf", ".docx", ".txt"}:
                    continue
                    
                target_path = extract_to / filename
                # Path traversal defense
                if not target_path.resolve().is_relative_to(extract_to.resolve()):
                    continue
                    
                with zf.open(info) as src, open(target_path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
                    
                extracted_files.append(target_path)
    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or corrupted ZIP archive."
        )
        
    return extracted_files


def extract_text_from_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Extract text from PDF, DOCX, or TXT while preserving page, paragraph, and offset information.
    Returns a list of chunk dictionaries.
    """
    ext = file_path.suffix.lower()
    chunks = []
    
    if ext == ".pdf":
        try:
            reader = PdfReader(file_path)
            global_offset = 0
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                if not paragraphs and text.strip():
                    paragraphs = [text.strip()]
                    
                for para_idx, para_text in enumerate(paragraphs, start=1):
                    norm_text = re.sub(r'\s+', ' ', para_text.lower()).strip()
                    chunks.append({
                        "page": page_num,
                        "paragraph": para_idx,
                        "offset": global_offset,
                        "original_text": para_text,
                        "normalized_text": norm_text
                    })
                    global_offset += len(para_text)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse PDF file {file_path.name}: {str(e)}"
            )
            
    elif ext == ".docx":
        try:
            doc = Document(file_path)
            global_offset = 0
            for para_idx, para in enumerate(doc.paragraphs, start=1):
                text = para.text.strip()
                if not text:
                    continue
                norm_text = re.sub(r'\s+', ' ', text.lower()).strip()
                chunks.append({
                    "page": 1,
                    "paragraph": para_idx,
                    "offset": global_offset,
                    "original_text": text,
                    "normalized_text": norm_text
                })
                global_offset += len(text)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse DOCX file {file_path.name}: {str(e)}"
            )
            
    elif ext == ".txt":
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            if not paragraphs and content.strip():
                paragraphs = [content.strip()]
                
            global_offset = 0
            for para_idx, para_text in enumerate(paragraphs, start=1):
                norm_text = re.sub(r'\s+', ' ', para_text.lower()).strip()
                chunks.append({
                    "page": 1,
                    "paragraph": para_idx,
                    "offset": global_offset,
                    "original_text": para_text,
                    "normalized_text": norm_text
                })
                global_offset += len(para_text)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read TXT file {file_path.name}: {str(e)}"
            )
            
    return chunks
