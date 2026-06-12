"""
RAG 知识库 — 基于 ChromaDB
Collections: spots, food, traffic, tips
"""
import json
import os
from typing import List, Dict, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class TravelRAGStore:
    """旅游知识库 — ChromaDB 封装"""

    COLLECTIONS = {
        "spots": "景点攻略",
        "food": "美食推荐",
        "traffic": "交通指南",
        "tips": "旅行贴士"
    }

    def __init__(self, persist_path: str = None):
        if persist_path is None:
            persist_path = os.path.join(os.path.dirname(__file__), "chroma_db")

        self.persist_path = persist_path
        self._client = None
        self._embedder = None

    @property
    def client(self):
        if self._client is None:
            os.makedirs(self.persist_path, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self.persist_path,
                settings=Settings(anonymized_telemetry=False)
            )
        return self._client

    @property
    def embedder(self):
        if self._embedder is None:
            try:
                # 仅使用本地缓存（避免 HuggingFace 网络超时阻塞请求）
                # 设置 HF_HUB_OFFLINE=1 环境变量确保完全离线
                import os as _os
                _os.environ.setdefault("HF_HUB_OFFLINE", "1")
                self._embedder = SentenceTransformer(
                    'paraphrase-multilingual-MiniLM-L12-v2',
                    local_files_only=True
                )
            except Exception as e:
                print(f"[RAG] 警告: 无法加载本地 embedding 模型: {e}")
                print("[RAG] RAG 检索将不可用，Agent 仍可正常规划（依赖工具+LLM 知识）")
                self._embedder = False  # 用 False 标记失败，避免反复重试
        return self._embedder if self._embedder is not False else None

    def _get_or_create_collection(self, name: str):
        try:
            return self.client.get_collection(name)
        except Exception:
            return self.client.create_collection(name)

    def index_documents(self, collection_name: str, docs: List[Dict]):
        """批量入库文档"""
        if collection_name not in self.COLLECTIONS:
            raise ValueError(f"未知 Collection: {collection_name}")

        col = self._get_or_create_collection(collection_name)

        ids = [doc.get("id", str(hash(doc["text"]))) for doc in docs]
        texts = [doc["text"] for doc in docs]
        metadatas = [{k: str(v) for k, v in doc.items() if k != "text"} for doc in docs]
        embeddings = self.embedder.encode(texts).tolist()

        col.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        return len(docs)

    def search(self, query: str, n_results: int = 3, collection_name: str = None) -> List[Dict]:
        """跨 Collection 搜索，或指定单个 Collection"""
        # 模型未加载时直接返回空结果（RAG 不可用，降级到工具知识库）
        embedder = self.embedder
        if embedder is None:
            return []

        results = []

        collections = [collection_name] if collection_name else list(self.COLLECTIONS.keys())

        for col_name in collections:
            try:
                col = self.client.get_collection(col_name)
                query_embedding = self.embedder.encode([query]).tolist()
                col_results = col.query(query_embeddings=query_embedding, n_results=n_results)

                for i, doc in enumerate(col_results.get("documents", [[]])[0]):
                    meta = col_results.get("metadatas", [[]])[0][i] if col_results.get("metadatas") else {}
                    results.append({
                        "text": doc,
                        "collection": col_name,
                        "metadata": meta,
                        "score": col_results.get("distances", [[]])[0][i] if col_results.get("distances") else None
                    })
            except Exception:
                continue

        return results

    def get_stats(self) -> Dict:
        """获取知识库统计"""
        stats = {}
        for name in self.COLLECTIONS:
            try:
                col = self.client.get_collection(name)
                stats[name] = col.count()
            except Exception:
                stats[name] = 0
        return stats


# 全局单例
rag_store = TravelRAGStore()
