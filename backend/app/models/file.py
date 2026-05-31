from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)   # имя до шифрования
    file_size = Column(BigInteger, default=0)
    mime_type = Column(String, nullable=True)
    storage_path = Column(String, nullable=False)    # путь на диске
    is_encrypted = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="files")