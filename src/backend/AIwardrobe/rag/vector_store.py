from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from AIwardrobe.model.factory import embed_model
from AIwardrobe.utils.config_handler import chroma_conf
from AIwardrobe.utils.path_tool import get_abs_path
from AIwardrobe.utils.file_handler import pdf_loader, txt_loader, listdir_with_allowed_type, get_file_md5_hex
from AIwardrobe.utils.logger_handler import logger

import os


class VectorStoreService:
    def __init__(self):
        self.vector_store = Chroma(
            collection_name=chroma_conf["collection_name"],
            embedding_function=embed_model,
            persist_directory=chroma_conf["persist_directory"],
        )
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size= chroma_conf["chunk_size"],
            chunk_overlap=chroma_conf["chunk_overlap"],
            separators=chroma_conf["separators"],
            length_function=len,
        )

    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k": chroma_conf["k"]})

    def load_document(self):
        """
        Read knowledge files from the data directory, chunk, embed, and upsert into Chroma.
        Uses per-file MD5 to skip already-ingested paths.
        """
        def check_md5_hex(md5_for_check: str):
            if not os.path.exists(get_abs_path(chroma_conf["md5_hex_store"])):
                open(get_abs_path(chroma_conf["md5_hex_store"]),"w",encoding="utf-8").close()
                return False                # MD5 store missing or empty → not seen

            with open(get_abs_path(chroma_conf["md5_hex_store"]),"r",encoding="utf-8") as f:
                for line in f.readlines():
                    line = line.strip()
                    if line == md5_for_check:
                        return True         # already ingested

                return False                # MD5 not in store

        def save_md5_hex(md5_for_check: str):
            with open(get_abs_path(chroma_conf["md5_hex_store"]), "a", encoding="utf-8") as f:
                f.write(md5_for_check + "\n")


        def get_file_documents(read_path):
            if read_path.endswith("txt"):
                return txt_loader(read_path)

            if read_path.endswith("pdf"):
                return pdf_loader(read_path)

            return []

        allowed_files_path = listdir_with_allowed_type(
            get_abs_path(chroma_conf["data_path"]),
            tuple(chroma_conf["allow_knowledge_file_type"]),
        )

        for path in allowed_files_path:
            # File content MD5 for deduplication
            md5_hex = get_file_md5_hex(path)

            if check_md5_hex(md5_hex):
                logger.info(f"[vector_store] skip (already ingested): {path}")
                continue

            try:
                documents: list[Document] = get_file_documents(path)

                if not documents:
                    logger.warning(f"[vector_store] no text content, skip: {path}")
                    continue

                split_document:list[Document] = self.spliter.split_documents(documents)

                if not split_document:
                    logger.warning(f"[vector_store] empty after split, skip: {path}")
                    continue

                # Upsert chunks into the vector store
                self.vector_store.add_documents(split_document)

                # Persist MD5 so we skip this file on the next run
                save_md5_hex(md5_hex)

                logger.info(f"[vector_store] ingested: {path}")

            except Exception as e:
                # exc_info=True logs full traceback; False logs message only
                logger.error(f"[vector_store] ingest failed: {path}: {e}", exc_info=True)
                continue


if __name__ == "__main__":
    vs = VectorStoreService()
    vs.load_document()
    retriever = vs.get_retriever()
    res = retriever.invoke("lost")

    for r in res:
        print(r.page_content)
        print("="*20)
