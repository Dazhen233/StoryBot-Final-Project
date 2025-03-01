# models/database.py
class UserSession(Base):
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(36), unique=True)
    character = Column(JSON)  # 存储角色特征向量
    story_graph = Column(JSON)  # 故事线图谱结构
    vocabulary = Column(JSON)  # 词频统计和掌握程度
    interaction_log = Column(JSON) # 交互行为日志