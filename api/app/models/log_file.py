from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

    

class LogFile(Base):
    __tablename__ = "log_files"
 
    id            = Column(Integer,    primary_key=True, index=True)
    user_id       = Column(Integer,    ForeignKey("users.id"), nullable=False)
    original_name = Column(String,     nullable=False)
    stored_path   = Column(String,     nullable=False)
    file_size     = Column(BigInteger, default=0)
    mime_type     = Column(String,     default="text/plain")
 
    log_source    = Column(String(64),  default="")   # "linux_auth", "windows_event", "firewall", "pcap", ...
    log_format    = Column(String(64),  default="")   # "syslog", "json", "csv", "evtx", ...
 
    uploaded_at   = Column(DateTime, default=datetime.utcnow)
 
    owner    = relationship("User",     back_populates="log_files")
    analyses = relationship("Analysis", back_populates="log_file",
                            cascade="all, delete-orphan")    
    