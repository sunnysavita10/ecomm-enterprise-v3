import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

class Base(DeclarativeBase):
    pass

class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ChatMessage(Base):
    __tablename__ = "messages"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (Index("ix_messages_conversation_time", "conversation_id", "created_at"),)

class Database:
    def __init__(self, url: str):
        self.engine = create_async_engine(url, pool_pre_ping=True, pool_size=10, max_overflow=20)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def is_ready(self):
        from sqlalchemy import text
        async with self.engine.connect() as c:
            await c.execute(text("SELECT 1"))

    async def close(self):
        await self.engine.dispose()

async def ensure_conversation(s: AsyncSession, conversation_id: uuid.UUID | None, owner_id: str) -> uuid.UUID:
    if conversation_id:
        obj = await s.get(Conversation, conversation_id)
        if obj is None or obj.owner_id != owner_id:
            raise LookupError("Conversation not found")
        return obj.id
    obj = Conversation(owner_id=owner_id)
    s.add(obj)
    await s.flush()
    return obj.id

async def load_history(s: AsyncSession, cid: uuid.UUID, limit: int) -> list[ChatMessage]:
    q = select(ChatMessage).where(ChatMessage.conversation_id == cid).order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc()).limit(limit)
    result = await s.execute(q)
    return list(reversed(result.scalars().all()))
