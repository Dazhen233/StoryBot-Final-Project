# core/memory/session_manager.py
import logging
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.schemas import UserSession, InteractionHistory

logger = logging.getLogger("session_manager")

class SessionManager:
    def __init__(self):
        self.db = SessionLocal()

    # ======================
    # 核心会话管理
    # ======================
    def create_session(self, user_id: str, age: int) -> UserSession:
        """创建新学习会话"""
        try:
            new_session = UserSession(
                user_id=user_id,
                age=age,
                start_time=datetime.now(),
                current_story="",
                vocabulary=[],
                interaction_count=0,
                error_count=0,
                difficulty_level=1
            )
            self.db.add(new_session)
            self.db.commit()
            return new_session
        except Exception as e:
            self.db.rollback()
            logger.error(f"Session creation failed: {str(e)}")
            raise

    def get_session(self, session_id: str) -> Optional[UserSession]:
        """获取会话完整状态"""
        return self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()

    def update_session(self, session_id: str, updates: Dict) -> bool:
        """更新会话状态"""
        try:
            rows_updated = self.db.query(UserSession).filter(
                UserSession.session_id == session_id
            ).update(updates)
            self.db.commit()
            return rows_updated > 0
        except Exception as e:
            self.db.rollback()
            logger.error(f"Session update failed: {str(e)}")
            return False

    def close_session(self, session_id: str) -> bool:
        """结束并归档会话"""
        session = self.get_session(session_id)
        if session:
            session.end_time = datetime.now()
            session.is_active = False
            self.db.commit()
            return True
        return False

    # ======================
    # 学习进度跟踪
    # ======================
    def record_interaction(self, session_id: str, interaction: Dict) -> bool:
        """记录互动历史"""
        try:
            new_record = InteractionHistory(
                session_id=session_id,
                timestamp=datetime.now(),
                input_type=interaction.get("type", "voice"),
                input_content=interaction.get("content", ""),
                response=interaction.get("response", ""),
                vocabulary=interaction.get("vocabulary", []),
                difficulty_level=interaction.get("difficulty", 1),
                success=interaction.get("success", True)
            )
            self.db.add(new_record)
            
            # 更新会话统计
            if not interaction.get("success", True):
                self._increment_error_count(session_id)
                
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Interaction recording failed: {str(e)}")
            return False

    def get_learning_progress(self, session_id: str) -> Dict:
        """获取学习进度报告"""
        session = self.get_session(session_id)
        if not session:
            return {}
            
        return {
            "session_duration": (datetime.now() - session.start_time).total_seconds(),
            "vocabulary_learned": len(session.vocabulary),
            "interaction_success_rate": self._calculate_success_rate(session),
            "current_difficulty": session.difficulty_level,
            "frequent_errors": self._analyze_errors(session_id)
        }

    # ======================
    # 核心业务逻辑
    # ======================
    def adjust_difficulty(self, session_id: str) -> int:
        """动态调整难度级别"""
        session = self.get_session(session_id)
        if not session:
            return 1
        
        base_level = session.difficulty_level
        success_rate = self._calculate_success_rate(session)
        
        if success_rate > 0.8:
            new_level = min(base_level + 1, 5)
        elif success_rate < 0.4:
            new_level = max(base_level - 1, 1)
        else:
            new_level = base_level
            
        self.update_session(session_id, {"difficulty_level": new_level})
        return new_level

    # ======================
    # 私有辅助方法
    # ======================
    def _calculate_success_rate(self, session: UserSession) -> float:
        """计算互动成功率"""
        if session.interaction_count == 0:
            return 0.0
        return 1 - (session.error_count / session.interaction_count)

    def _increment_error_count(self, session_id: str):
        """增加错误计数"""
        self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).update({
            "error_count": UserSession.error_count + 1,
            "interaction_count": UserSession.interaction_count + 1
        })

    def _analyze_errors(self, session_id: str) -> Dict:
        """分析常见错误模式"""
        errors = self.db.query(InteractionHistory).filter(
            InteractionHistory.session_id == session_id,
            InteractionHistory.success == False
        ).all()
        
        return {
            "common_word_errors": self._count_word_errors(errors),
            "sentence_structure_issues": self._count_structure_issues(errors)
        }

    def _count_word_errors(self, errors) -> Dict:
        """统计词汇错误"""
        word_errors = {}
        for error in errors:
            for word in error.vocabulary:
                if word not in word_errors:
                    word_errors[word] = 0
                word_errors[word] += 1
        return word_errors

    def _count_structure_issues(self, errors) -> int:
        """统计语法结构错误"""
        return sum(1 for e in errors if "structure" in e.response)

    # ======================
    # 生命周期管理
    # ======================
    def __del__(self):
        """确保释放数据库连接"""
        self.db.close()

# ======================
# 使用示例
# ======================
def example_usage():
    manager = SessionManager()
    
    # 创建新会话
    new_session = manager.create_session(
        user_id="child123",
        age=5
    )
    
    # 记录互动
    manager.record_interaction(
        session_id=new_session.session_id,
        interaction={
            "type": "voice",
            "content": "I want play snow!",
            "response": "Let's build a snowman!",
            "vocabulary": ["snowman"],
            "success": True
        }
    )
    
    # 获取进度报告
    progress = manager.get_learning_progress(new_session.session_id)
    print(f"Current success rate: {progress['interaction_success_rate']}")
    
    # 调整难度
    new_level = manager.adjust_difficulty(new_session.session_id)
    print(f"New difficulty level: {new_level}")