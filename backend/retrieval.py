"""本地关键词检索（BM25），作为向量检索的零依赖兜底。

为什么需要：
1. 竞赛提供的模型网关不一定开放 embedding 接口；
2. 评审环境未必允许调用外部向量服务；
3. 只要 kb/*.md 还在，RAG 链路就一定能跑通，演示不会因为一个外部依赖挂掉。

中文没有空格，这里用「单字 + 二元切分」代替分词器，
不需要安装 jieba 之类的额外依赖，召回效果足够支撑本项目 12 篇知识文档。
"""

import glob
import math
import os
import re
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.join(BASE_DIR, "kb")

_LATIN = re.compile(r"[a-z0-9_]+")
_CJK_RUN = re.compile(r"[\u4e00-\u9fff]+")

K1 = 1.2
B = 0.75

# 高频虚词二元组会把「一个」「需要」这类无信息量的匹配算成高分，
# 这里做一层轻量停用词过滤，明显提升小语料下的排序准确度。
_STOPWORDS = {
    "一个", "一种", "一下", "一些", "这个", "那个", "这些", "那些",
    "需要", "可以", "可能", "应该", "如何", "怎么", "怎样", "什么",
    "多少", "大概", "一般", "主要", "就是", "不是", "没有", "因为",
    "所以", "但是", "如果", "以及", "还是", "或者", "我们", "你们",
    "他们", "自己", "时候", "现在", "已经", "进行", "通过", "对于",
}


def tokenize(text: str) -> list[str]:
    text = (text or "").lower()
    tokens = _LATIN.findall(text)
    for run in _CJK_RUN.findall(text):
        if len(run) == 1:
            tokens.append(run)
        else:
            tokens.extend(run[i : i + 2] for i in range(len(run) - 1))
    return [t for t in tokens if t not in _STOPWORDS]


def split_markdown(text: str, size: int = 400, overlap: int = 80) -> list[str]:
    """按空行分段，再拼成不超过 size 字的片段；超长段落做滑动切分。"""
    text = re.sub(r"\r\n?", "\n", text or "").strip()
    if not text:
        return []
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        if len(buf) + len(para) + 2 <= size:
            buf = f"{buf}\n\n{para}".strip()
            continue
        if buf:
            chunks.append(buf)
        while len(para) > size:
            chunks.append(para[:size])
            para = para[size - overlap :]
        buf = para
    if buf:
        chunks.append(buf)
    return chunks


class KeywordIndex:
    """极简 BM25 索引。"""

    def __init__(self, docs: list[dict]):
        self.docs = docs
        self.term_freqs = [Counter(tokenize(d["content"])) for d in docs]
        self.doc_freq: Counter = Counter()
        for tf in self.term_freqs:
            self.doc_freq.update(tf.keys())
        self.doc_count = len(docs)
        lengths = [sum(tf.values()) or 1 for tf in self.term_freqs]
        self.avg_len = sum(lengths) / len(lengths) if lengths else 1.0
        self.lengths = lengths
        # 标题命中做加权：文件名本身就是主题标签
        self.title_tokens = [
            set(tokenize(os.path.splitext(d["source"])[0])) for d in docs
        ]

    def search(self, query: str, k: int = 3) -> list[dict]:
        terms = tokenize(query)
        if not terms or not self.docs:
            return []
        scores: list[tuple[float, int]] = []
        for idx, tf in enumerate(self.term_freqs):
            norm = K1 * (1 - B + B * self.lengths[idx] / self.avg_len)
            score = 0.0
            for term in terms:
                freq = tf.get(term)
                if not freq:
                    continue
                df = self.doc_freq[term]
                idf = math.log(1 + (self.doc_count - df + 0.5) / (df + 0.5))
                score += idf * freq * (K1 + 1) / (freq + norm)
            if score > 0:
                title_hits = sum(1 for term in terms if term in self.title_tokens[idx])
                if title_hits:
                    score *= 1 + 0.2 * title_hits
                scores.append((score, idx))
        scores.sort(reverse=True)
        # 同一篇文档最多取 2 段，避免上下文被同一主题占满
        picked: list[dict] = []
        per_source: Counter = Counter()
        for _score, idx in scores:
            source = self.docs[idx]["source"]
            if per_source[source] >= 2:
                continue
            per_source[source] += 1
            picked.append(self.docs[idx])
            if len(picked) >= k:
                break
        return picked


_index: KeywordIndex | None = None


def _load_docs() -> list[dict]:
    docs: list[dict] = []
    for path in sorted(glob.glob(os.path.join(KB_DIR, "*.md"))):
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        for chunk in split_markdown(content):
            docs.append({"source": os.path.basename(path), "content": chunk})
    return docs


def get_index() -> KeywordIndex:
    global _index
    if _index is None:
        _index = KeywordIndex(_load_docs())
    return _index


def search(query: str, k: int = 3) -> list[dict]:
    """对外只暴露一个检索入口，内部按需建索引。"""
    return get_index().search(query, k)


def stats() -> dict:
    """返回切片数、文档数与当前检索模式，供 /api/health 展示。"""
    index = get_index()
    return {
        "chunks": index.doc_count,
        "sources": len({d["source"] for d in index.docs}),
        "mode": "keyword",
    }
