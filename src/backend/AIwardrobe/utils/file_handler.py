import os, hashlib
from AIwardrobe.utils.logger_handler import logger
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader

def get_file_md5_hex(filepath: str):    # Return MD5 hex digest of file contents
    if not os.path.exists(filepath):
        logger.error(f"[md5] file not found: {filepath}")
        return

    if not os.path.isfile(filepath):
        logger.error(f"[md5] path is not a file: {filepath}")
        return

    md5_obj = hashlib.md5()

    chunk_size = 4096     # 4KB reads to bound memory on large files
    try:
        with open(filepath, "rb") as f:     # Binary mode required for hashing
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)

            md5_hex = md5_obj.hexdigest()
            return md5_hex

    except Exception as e:
        logger.error(f"[md5] failed for {filepath}: {e}")
        return None

def listdir_with_allowed_type(path: str, allowed_types: tuple[str]):   # List files under path matching suffix tuple
    files = []

    if not os.path.isdir(path):
        logger.error(f"[listdir_with_allowed_type] not a directory: {path}")
        return allowed_types

    for f in os.listdir(path):
        if f.endswith(allowed_types):
            files.append(os.path.join(path, f))

    return tuple(files)



def pdf_loader(filepath: str, passwd=None):
    return PyPDFLoader(filepath, passwd).load()


def txt_loader(filepath: str) -> list[Document]:
    return TextLoader(filepath, encoding="utf-8").load()
