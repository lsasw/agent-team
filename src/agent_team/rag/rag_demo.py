"""
RAG (检索增强生成) 学习 Demo — 基于 LangChain + ChromaDB + DeepSeek

架构流程:
  1. 加载文档（docs/ 目录下的 .md 文件 + 项目源码）
  2. 文本分块（RecursiveCharacterTextSplitter）
  3. 向量化（本地 Embedding 模型，免费/离线/无需 API）
  4. 存入本地向量库（ChromaDB，持久化到磁盘）
  5. 检索 + 生成（LangChain 链式调用 + DeepSeek LLM）

两个阶段各用各的模型：
  - Embedding: 本地 sentence-transformers（把文本→向量，免费）
  - 生成:     DeepSeek API（根据检索结果回答问题）

用法:
  python rag_demo.py                     # 交互式模式
  python rag_demo.py -q "什么是 ReAct？"  # 单次查询
  python rag_demo.py -s "ReAct"          # 只看检索到哪些文档
  python rag_demo.py --rebuild           # 重建向量库
"""

import os
import argparse
from dotenv import load_dotenv

# ── LangChain 组件 ──────────────────────────────────────────
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ── 文档处理 ────────────────────────────────────────────────
from langchain_community.document_loaders import (
    TextLoader,
    DirectoryLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ── 向量库 ──────────────────────────────────────────────────
from langchain_chroma import Chroma

# ── 本地 Embedding 模型（免费、离线、无需 API Key）────────
from langchain_huggingface import HuggingFaceEmbeddings


# ═══════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════

load_dotenv()
# src/agent_team/rag/ → 向上 3 级到项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_db")       # 向量库存放位置

# LLM（生成阶段）— DeepSeek
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# Embedding（向量化阶段）— 本地模型，首次使用会自动下载
# BGE 是 BAAI 开源的 Embedding 模型，中文效果优秀
EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"


# ═══════════════════════════════════════════════════════════════
# 第 1 步：加载文档
# ═══════════════════════════════════════════════════════════════

def load_documents() -> list:
    """
    加载项目中的文档，支持多种文件类型。

    LangChain 的 Document Loader 负责：
    - 读取文件内容
    - 标记元数据（来源文件路径等）
    - 返回 Document 对象列表
    """
    docs = []

    # ① 加载 docs/ 目录下的 Markdown 设计文档
    docs_dir = os.path.join(BASE_DIR, "docs")
    if os.path.exists(docs_dir):
        md_loader = DirectoryLoader(
            docs_dir,
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        )
        md_docs = md_loader.load()
        print(f"  ✓ 加载 Markdown 文档: {len(md_docs)} 篇")
        docs.extend(md_docs)

    # ② 加载项目源码（.py 文件）—— 展示多类型文档混合检索
    py_loader = DirectoryLoader(
        BASE_DIR,
        glob="*.py",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        # 排除自身，避免递归
        silent_errors=True,
    )
    py_docs = py_loader.load()
    # 过滤掉 rag_demo.py 自身
    py_docs = [d for d in py_docs if "rag_demo.py" not in d.metadata.get("source", "")]
    print(f"  ✓ 加载 Python 源码: {len(py_docs)} 篇")
    docs.extend(py_docs)

    return docs


# ═══════════════════════════════════════════════════════════════
# 第 2 步：文本分块
# ═══════════════════════════════════════════════════════════════

def split_documents(docs: list) -> list:
    """
    将长文档切分成小块。

    为什么要分块？
    - Embedding 模型有 token 限制
    - 小块检索更精准（不会把无关内容拉进来）
    - chunk_overlap：块之间重叠 100 字符，防止信息在边界处断裂

    RecursiveCharacterTextSplitter 智能切分策略:
    先按「段落」切 → 不够再按「句子」→ 还不够按「字符」
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,         # 每块最多 500 字符
        chunk_overlap=100,      # 相邻块重叠 100 字符
        separators=["\n\n", "\n", "。", ".", " ", ""],  # 按优先级切分
        #            ↑ 优先在段落边界切，保持语义完整
    )
    chunks = splitter.split_documents(docs)
    print(f"  ✓ 分块完成: {len(docs)} 篇文档 → {len(chunks)} 个块")
    return chunks


# ═══════════════════════════════════════════════════════════════
# 第 3 步：创建向量库（Embedding + 存储）
# ═══════════════════════════════════════════════════════════════

def _get_embeddings():
    """
    获取本地 Embedding 模型实例。

    用的是 BAAI/bge-small-zh-v1.5：
    - 开源、免费、本地运行，无需任何 API Key
    - 384 维向量（维度小 = 存储省空间、检索快）
    - 中英文混合训练，中文效果优秀
    - 首次使用自动从 HuggingFace 下载（约 95MB）
    - 下载一次后缓存到本地，之后即时加载

    ┌───────────── 对比 ─────────────┐
    │ API 方案        本地方案        │
    │ 要联网          完全离线        │
    │ 要付费          免费            │
    │ 有延迟(网络)    毫秒级响应       │
    │ 受限频          无限制           │
    └────────────────────────────────┘
    """
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": "cpu"},  # 改成 "mps" 可用 Apple Silicon GPU 加速
        encode_kwargs={
            "normalize_embeddings": True,  # 归一化，让向量比较用余弦相似度
        },
    )


def create_vectorstore(chunks: list) -> Chroma:
    """
    将文本块转成向量并存入 ChromaDB。

    完整流程：
    1. 加载本地 Embedding 模型
    2. 对每个文本块 → 模型.encode() → 384 维向量
    3. 「文本块 + 向量 + 元数据」→ 存入 ChromaDB（磁盘持久化）
    4. ChromaDB 自动为向量建立索引（默认 HNSW 图索引）

    之后查询时：
      用户问题 → 模型.encode() → 向量 Q
      ChromaDB 拿 Q 和库中所有向量算距离 → 返回最接近的 k 个文本块
    """
    embeddings = _get_embeddings()

    # 如果向量库已存在，先清空（全量重建）
    if os.path.exists(CHROMA_DB_DIR):
        import shutil
        shutil.rmtree(CHROMA_DB_DIR)
        print("  ✓ 已清空旧向量库")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR,    # 持久化到磁盘
        collection_name="agent-team-docs",  # 集合名称
    )
    print(f"  ✓ 向量库创建完成，存储位置: {CHROMA_DB_DIR}")
    return vectorstore


def load_vectorstore() -> Chroma | None:
    """加载已有的向量库（不用重建）"""
    if not os.path.exists(CHROMA_DB_DIR):
        return None

    embeddings = _get_embeddings()
    return Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings,
        collection_name="agent-team-docs",
    )


# ═══════════════════════════════════════════════════════════════
# 第 4 步：构建 RAG 链
# ═══════════════════════════════════════════════════════════════

def build_rag_chain(vectorstore: Chroma):
    """
    用 LangChain 的 LCEL（LangChain Expression Language）构建 RAG 链。

    链的结构:
      用户问题
        │
        ├─→ retriever（检索器）──→ 从向量库找相关文档
        │
        └─→ 两个一起传给 prompt 模板
              │
              └─→ LLM 生成回答

    LCEL 使用 | (管道符) 连接组件，类似 Unix 管道:
     上一个的输出 → 下一个的输入
    """
    # ① 检索器 — 将用户问题向量化后在 ChromaDB 中搜索
    retriever = vectorstore.as_retriever(
        search_type="similarity",   # 相似度搜索
        search_kwargs={"k": 3},     # 返回最相关的 3 个文档块
    )

    # ② Prompt 模板 — 告诉 LLM 怎么利用检索到的文档
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个代码库问答助手。请根据以下上下文回答问题。

## 规则
- 只根据提供的上下文回答，不要编造信息
- 如果上下文中没有相关信息，直接说"文档中未找到相关内容"
- 回答要简洁、准确，引用相关代码片段

## 上下文
{context}"""),
        ("human", "{question}"),
    ])

    # ③ LLM
    llm = ChatOpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=MODEL,
        temperature=0.3,
    )

    # ④ 输出解析器 — 只取 LLM 响应的文本内容
    parser = StrOutputParser()

    # ── 组装链 ────────────────────────────────────────
    #  这是 LangChain 的核心魔法 — 用 | 管道符串联所有步骤
    #
    #  RunnablePassthrough 的作用：把用户问题原样传给 prompt 的 {question}
    #  同时 retriever 把检索结果传给 prompt 的 {context}
    #
    def format_docs(docs):
        """把检索到的文档列表拼成一个大文本块"""
        return "\n\n---\n\n".join(
            f"[来源: {d.metadata.get('source', '未知')}]\n{d.page_content}"
            for d in docs
        )

    rag_chain = (
        {
            "context": retriever | format_docs,   # 检索 → 格式化
            "question": RunnablePassthrough(),     # 用户问题原样传递
        }
        | prompt       # 填入模板
        | llm          # 调用 LLM
        | parser       # 提取文本
    )

    return rag_chain


# ═══════════════════════════════════════════════════════════════
# 第 5 步：查询
# ═══════════════════════════════════════════════════════════════

def query(chain, question: str) -> str:
    """使用 RAG 链回答问题"""
    print(f"\n{'='*60}")
    print(f"🔍 问题: {question}")
    print(f"{'='*60}")

    # invoke() 是 LangChain 链的统一调用入口
    answer = chain.invoke(question)
    print(f"\n🤖 回答:\n{answer}")
    return answer


# ═══════════════════════════════════════════════════════════════
# 交互模式
# ═══════════════════════════════════════════════════════════════

def interactive_mode(chain):
    """交互式问答循环"""
    print("\n" + "=" * 60)
    print("💬 RAG 交互模式 (输入 'quit' 退出, 'source' 查看检索来源)")
    print("=" * 60)

    while True:
        try:
            q = input("\n🧑 你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见!")
            break

        if not q:
            continue
        if q.lower() == "quit":
            print("👋 再见!")
            break

        # 原始检索（展示"检索 + 生成"两个阶段的分离）
        if q.lower() == "source":
            print("（请输入要查看来源的问题）")
            continue

        query(chain, q)


# ═══════════════════════════════════════════════════════════════
# 展示检索结果（调试用）
# ═══════════════════════════════════════════════════════════════

def show_retrieval(vectorstore: Chroma, question: str):
    """查看检索到的文档块（不经过 LLM）"""
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3},
    )
    docs = retriever.invoke(question)
    print(f"\n📚 检索到 {len(docs)} 个相关文档块:")
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "未知")
        print(f"\n  [{i}] 来源: {source}")
        print(f"      内容: {doc.page_content[:200]}...")


# ═══════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="RAG 学习 Demo")
    parser.add_argument("--query", "-q", type=str, help="单次查询")
    parser.add_argument("--rebuild", "-r", action="store_true", help="重建向量库")
    parser.add_argument("--source", "-s", type=str, help="仅查看检索结果（不生成）")
    args = parser.parse_args()

    # ── 准备向量库 ────────────────────────────────────
    vectorstore = load_vectorstore()

    if vectorstore is None or args.rebuild:
        print("\n📦 构建向量库...")
        docs = load_documents()
        if not docs:
            print("❌ 没有找到任何文档，请确保 docs/ 目录下有 .md 文件")
            return
        chunks = split_documents(docs)
        vectorstore = create_vectorstore(chunks)

    # ── 构建 RAG 链 ────────────────────────────────────
    print("\n🔗 构建 RAG 链...")
    chain = build_rag_chain(vectorstore)
    print("  ✓ RAG 链就绪")

    # ── 查看检索结果 ──────────────────────────────────
    if args.source:
        show_retrieval(vectorstore, args.source)
        return

    # ── 单次查询 ──────────────────────────────────────
    if args.query:
        query(chain, args.query)
        return

    # ── 交互模式 ──────────────────────────────────────
    interactive_mode(chain)


if __name__ == "__main__":
    main()
