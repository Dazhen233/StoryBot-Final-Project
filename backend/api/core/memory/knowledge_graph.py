# core/memory/knowledge_graph.py
import logging
from typing import Dict, List, Optional
from datetime import datetime
import networkx as nx
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.schemas import InteractionHistory, UserSession

logger = logging.getLogger("knowledge_graph")

class KnowledgeGraph:
    def __init__(self):
        self.db = SessionLocal()
        self.graph = nx.DiGraph()
        self._initialize_graph()

    # ======================
    # 知识图谱构建
    # ======================
    def _initialize_graph(self):
        """初始化基础教学知识图谱"""
        # 从预设文件加载基础结构
        self._load_base_structure()
        
        # 从数据库加载历史数据
        self._load_historical_data()

    def _load_base_structure(self):
        """加载预设教学框架"""
        # 基础词汇图谱
        base_vocab = {
            "animals": ["dog", "cat", "rabbit"],
            "actions": ["run", "jump", "eat"],
            "objects": ["ball", "book", "apple"]
        }
        
        # 构建分类关系
        for category, words in base_vocab.items():
            self.graph.add_node(category, type="category")
            for word in words:
                self.graph.add_node(word, type="word")
                self.graph.add_edge(category, word, relation="contains")

        # 添加词性关联
        self._add_relations([
            ("dog", "animal", "is_a"),
            ("run", "action", "is_a"),
            ("ball", "toy", "is_a")
        ])

    def _load_historical_data(self):
        """从历史互动数据中学习关联"""
        interactions = self.db.query(InteractionHistory).all()
        
        for record in interactions:
            self._process_interaction(record.input_content, record.response)

    def _process_interaction(self, question: str, answer: str):
        """从单条互动中提取知识关联"""
        # 此处应接入NLP处理流水线（示例使用简单规则）
        key_words = self._extract_keywords(question + " " + answer)
        for i in range(len(key_words)-1):
            self.graph.add_edge(key_words[i], key_words[i+1], weight=1)

    # ======================
    # 核心功能接口
    # ======================
    def recommend_content(self, session_id: str) -> Dict:
        """根据当前状态推荐教学内容"""
        session = self.db.query(UserSession).get(session_id)
        if not session:
            return {}
            
        # 获取相关知识点
        recent_words = session.vocabulary[-3:]  # 最近学习的3个词汇
        paths = self._find_related_paths(recent_words)
        
        return {
            "next_topics": self._select_topics(paths),
            "related_words": self._get_related_words(recent_words),
            "difficulty_level": session.difficulty_level
        }

    def analyze_progress(self, session_id: str) -> Dict:
        """生成学习路径分析报告"""
        session = self.db.query(UserSession).get(session_id)
        if not session:
            return {}
            
        return {
            "knowledge_coverage": self._calculate_coverage(session.vocabulary),
            "learning_path": self._visualize_path(session.vocabulary),
            "weak_areas": self._detect_weak_points(session)
        }

    # ======================
    # 图谱分析算法
    # ======================
    def _find_related_paths(self, words: List[str], depth=2) -> List:
        """查找相关知识点路径"""
        related = set()
        for word in words:
            for _, neighbor in nx.bfs_edges(self.graph, word, depth_limit=depth):
                related.add(neighbor)
        return list(related)

    def _calculate_coverage(self, learned: List[str]) -> float:
        """计算知识覆盖度"""
        all_nodes = set(self.graph.nodes())
        learned_set = set(learned)
        return len(learned_set & all_nodes) / len(all_nodes) if all_nodes else 0

    def _detect_weak_points(self, session: UserSession) -> List:
        """检测知识薄弱环节"""
        error_records = self.db.query(InteractionHistory).filter(
            InteractionHistory.session_id == session.session_id,
            InteractionHistory.success == False
        ).all()
        
        weak_nodes = set()
        for record in error_records:
            weak_nodes.update(self._find_related_nodes(record.input_content))
            
        return [
            node for node in weak_nodes
            if node in session.vocabulary
        ]

    # ======================
    # 教学逻辑引擎
    # ======================
    def _select_topics(self, candidates: List[str]) -> List:
        """根据图谱权重选择推荐主题"""
        scored = []
        for node in candidates:
            predecessors = list(self.graph.predecessors(node))
            score = len(predecessors) * 0.5 + self.graph.degree(node) * 0.3
            scored.append((node, score))
            
        return [item[0] for item in sorted(scored, key=lambda x: -x[1])[:3]]

    def _get_related_words(self, base_words: List[str]) -> Dict:
        """获取关联词汇网络"""
        related = {}
        for word in base_words:
            related[word] = {
                "synonyms": self._find_relations(word, "synonym"),
                "antonyms": self._find_relations(word, "antonym"),
                "categories": self._find_categories(word)
            }
        return related

    # ======================
    # NLP处理工具（示意实现）
    # ======================
    def _extract_keywords(self, text: str) -> List[str]:
        """关键词提取（示例使用简单分词）"""
        # 实际应接入spaCy/NLTK等库
        return list(set(text.lower().split()[:5]))

    def _find_relations(self, word: str, rel_type: str) -> List[str]:
        """查找特定类型的关系节点"""
        return [
            target for _, target, data 
            in self.graph.edges(word, data=True)
            if data.get('relation') == rel_type
        ]

    def _find_categories(self, word: str) -> List[str]:
        """查找词所属的分类"""
        return [
            source for source, _, data 
            in self.graph.in_edges(word, data=True)
            if data.get('relation') == "contains"
        ]

    # ======================
    # 可视化工具
    # ======================
    def _visualize_path(self, learned: List[str]) -> Dict:
        """生成学习路径可视化数据"""
        subgraph = self.graph.subgraph(learned)
        return {
            "nodes": list(subgraph.nodes()),
            "edges": [
                {"source": u, "target": v, **data} 
                for u, v, data in subgraph.edges(data=True)
            ]
        }

    # ======================
    # 生命周期管理
    # ======================
    def refresh_graph(self):
        """刷新图谱数据"""
        self.graph.clear()
        self._initialize_graph()

    def __del__(self):
        """资源清理"""
        self.db.close()

# ======================
# 使用示例
# ======================
def example_usage():
    kg = KnowledgeGraph()
    
    # 获取推荐内容
    recommendation = kg.recommend_content("session_123")
    print(f"推荐教学主题: {recommendation['next_topics']}")
    
    # 生成学习报告
    report = kg.analyze_progress("session_123")
    print(f"知识覆盖度: {report['knowledge_coverage']*100:.1f}%")
    
    # 可视化路径
    print("学习路径可视化:", report['learning_path'])