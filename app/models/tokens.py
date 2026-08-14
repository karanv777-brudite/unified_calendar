from sqlalchemy import Column, String, DateTime, Text, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.services.security import TokenEncryptor

class UserAccountToken(Base):
    __tablename__ = "user_tokens"

    id = Column(String, primary_key=True, index=True) 
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    account_key = Column(String, nullable=False) 
    provider = Column(String, nullable=False) 
    email = Column(String, nullable=False)
    
    # Encrypted fields stored securely as Text
    encrypted_access_token = Column(Text, nullable=False)
    encrypted_refresh_token = Column(Text, nullable=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'account_key', name='_user_account_uc'),
    )

    # Relationship back to User
    user = relationship("User", back_populates="tokens")

    # Transparent encryption/decryption properties (DRY)
    @property
    def access_token(self) -> str:
        return TokenEncryptor.decrypt(self.encrypted_access_token)

    @access_token.setter
    def access_token(self, value: str):
        self.encrypted_access_token = TokenEncryptor.encrypt(value)

    @property
    def refresh_token(self) -> str:
        return TokenEncryptor.decrypt(self.encrypted_refresh_token)

    @refresh_token.setter
    def refresh_token(self, value: str):
        self.encrypted_refresh_token = TokenEncryptor.encrypt(value)