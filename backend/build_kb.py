"""构建向量库（可选步骤）。

- 未配置 EMBEDDING_MODEL：直接跳过。应用运行时会用 retrieval.py 的本地关键词检索，
  知识库照样可用，不需要任何外部 embedding 服务。
- 配置了但构建失败（网关不支持 / 断网 / 额度不足）：只提示，不中断启动流程，
  避免评审现场因为一个可选依赖起不来。

用法：python build_kb.py
"""

import glob
import os
import shutil
import sys

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import EMBEDDING_API_KEY, EMBEDDING_BASE_URL, EMBEDDING_MODEL

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.join(BASE_DIR, "kb")
STORE_DIR = os.path.join(BASE_DIR, "vector_store")

if not EMBEDDING_MODEL:
    print("未配置 EMBEDDING_MODEL，跳过向量库构建。")
    print("运行时将使用本地关键词检索（BM25），无需任何外部依赖。")
    sys.exit(0)

if not EMBEDDING_API_KEY:
    print("未配置 EMBEDDING_API_KEY / LLM_API_KEY，无法调用向量模型，跳过构建。")
    print("运行时将使用本地关键词检索（BM25）。")
    sys.exit(0)

docs = []
for path in sorted(glob.glob(os.path.join(KB_DIR, "*.md"))):
    with open(path, encoding="utf-8") as f:
        docs.append(Document(page_content=f.read(), metadata={"source": path}))
if not docs:
    sys.exit(f"kb/ 目录里没有找到 .md 文件：{KB_DIR}")
print(f"加载知识文件：{len(docs)} 个")

splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=80)
chunks = splitter.split_documents(docs)
print(f"切片后知识片段：{len(chunks)} 个")

embeddings = OpenAIEmbeddings(
    model=EMBEDDING_MODEL,
    api_key=EMBEDDING_API_KEY,
    base_url=EMBEDDING_BASE_URL,
    check_embedding_ctx_length=False,
    chunk_size=10,
)

if os.path.isdir(STORE_DIR):
    shutil.rmtree(STORE_DIR, ignore_errors=True)
    print("已清空旧的向量库，开始重建")

try:
    vector_store = Chroma.from_documents(chunks, embeddings, persist_directory=STORE_DIR)
except Exception as exc:  # noqa: BLE001
    shutil.rmtree(STORE_DIR, ignore_errors=True)
    print(f"向量库构建失败：{exc}")
    print("不影响使用：应用运行时会自动退回本地关键词检索（BM25）。")
    sys.exit(0)

print(f"向量库已保存到：{STORE_DIR}（共 {vector_store._collection.count()} 条）")

print("\n自检：检索「做一个小程序需要什么技术」")
for d in vector_store.similarity_search("做一个小程序需要什么技术", k=3):
    source = os.path.basename(d.metadata.get("source", ""))
    preview = d.page_content[:40].replace("\n", " ")
    print(f"  - [{source}] {preview}...")
