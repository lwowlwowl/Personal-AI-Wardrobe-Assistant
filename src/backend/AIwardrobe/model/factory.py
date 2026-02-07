from abc import ABC, abstractmethod
import os
from typing import Optional

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from utils.config_handler import rag_conf

class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        pass


class ChatModelFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return ChatOpenAI(
            base_url=rag_conf["base_url"],
            api_key=rag_conf["api_key"],
            model=rag_conf["chat_model_name"],
        )

class EmbeddingsFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
        if not dashscope_api_key:
            raise ValueError("未配置DASHSCOPE_API_KEY，无法初始化DashScopeEmbeddings")
        return DashScopeEmbeddings(
            model=rag_conf["embedding_model_name"],
            dashscope_api_key=dashscope_api_key
        )

chat_model = ChatModelFactory().generator()
embed_model = EmbeddingsFactory().generator()