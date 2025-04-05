from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class ChatbotResponse(db.Model):
    """
    Model for storing predefined chatbot responses and their patterns
    """
    __tablename__ = 'chatbot_responses'
    
    id = Column(Integer, primary_key=True)
    pattern = Column(String(255), nullable=False)
    response = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<ChatbotResponse(id={self.id}, pattern='{self.pattern[:20]}...', category='{self.category}')>"

class UserQuery(db.Model):
    """
    Model for logging user queries and the chatbot's responses
    """
    __tablename__ = 'user_queries'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<UserQuery(id={self.id}, query='{self.query[:20]}...', session_id='{self.session_id}')>"

class KnowledgeBase(db.Model):
    """
    Model for storing knowledge base items for the chatbot
    """
    __tablename__ = 'knowledge_base'
    
    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, question='{self.question[:20]}...', category='{self.category}')>"