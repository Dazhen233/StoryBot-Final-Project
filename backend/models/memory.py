from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryMemory
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.vectorstores import SQLite

# 配置 OpenAI 模型
llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 创建总结型对话内存
conversation_summary_memory = ConversationSummaryMemory(llm=llm, max_token_limit=1024)

# 创建 ConversationChain 实例
conversation_chain = ConversationChain(memory=conversation_summary_memory, llm=llm)

def get_summary_memory(user_id: str):
    """
    获取指定用户的对话摘要记忆
    """
    # 从数据库中提取该用户的记忆（假设你使用 SQLite 数据库）
    # TODO: 你可以直接从 SQLite 查询并加载该用户的记忆内容
    pass

def update_memory(user_id: str, user_message: str, bot_message: str):
    """
    更新对话内存
    """
    conversation_chain.add_user_message(user_message)
    conversation_chain.add_ai_message(bot_message)

    # 更新数据库中的记忆
    # TODO: 存储对话摘要到数据库
    pass
