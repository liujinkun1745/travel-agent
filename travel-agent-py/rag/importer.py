"""
知识库导入脚本 — 将 MD 文档批量导入 ChromaDB
"""
import os
import re
from chroma_store import rag_store


def import_knowledge():
    """从 rag/knowledge/ 目录导入所有 Markdown 文档到 ChromaDB"""

    knowledge_dir = os.path.dirname(__file__) + "/knowledge"

    # 解析 Markdown 文档，按 ## 标题拆分为独立文档块
    collections_map = {
        "spots": "spots.md",
        "food": "food.md",
        "traffic": "traffic.md",
        "tips": "tips.md"
    }

    total_imported = 0

    for collection_name, filename in collections_map.items():
        filepath = os.path.join(knowledge_dir, filename)
        if not os.path.exists(filepath):
            print(f"  [跳过] {filename} 不存在")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 按 ### 标题拆分文档块
        blocks = re.split(r'\n### ', content)

        docs = []
        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # 提取标题（第一行）
            lines = block.split('\n')
            title = lines[0].lstrip('#').strip() if lines else "未知"
            text = '\n'.join(lines)  # 完整文本用于检索

            docs.append({
                "id": f"{collection_name}_{hash(text) % 100000}",
                "text": text,
                "title": title,
                "source": filename
            })

        if docs:
            count = rag_store.index_documents(collection_name, docs)
            total_imported += count
            print(f"  [{collection_name}] 导入 {count} 条文档")

    print(f"\n总共导入 {total_imported} 条文档")
    stats = rag_store.get_stats()
    print(f"知识库统计: {stats}")


if __name__ == "__main__":
    print("开始导入旅游知识库...")
    import_knowledge()
    print("导入完成！")
