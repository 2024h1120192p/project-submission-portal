"""Submission store with PostgreSQL backend using SQLAlchemy async."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, select
from libs.events.schemas import Submission
from config.settings import get_settings
from datetime import datetime

settings = get_settings()


# SQLAlchemy models
class Base(DeclarativeBase):
    pass


class SubmissionModel(Base):
    """SQLAlchemy model for Submission."""
    __tablename__ = "submissions"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    assignment_id: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    file_url: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class SubmissionStore:
    """Async PostgreSQL-backed submission store."""
    
    def __init__(self):
        self.engine = create_async_engine(settings.POSTGRES_URL, echo=False)
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self._initialized = False

    async def initialize(self):
        """Initialize database tables."""
        if not self._initialized:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self._initialized = True

    async def save(self, sub: Submission) -> Submission:
        """Save a submission to the database."""
        await self.initialize()
        async with self.async_session() as session:
            db_sub = SubmissionModel(
                id=sub.id,
                user_id=sub.user_id,
                assignment_id=sub.assignment_id,
                uploaded_at=sub.uploaded_at,
                file_url=sub.file_url,
                text=sub.text
            )
            session.add(db_sub)
            await session.commit()
            await session.refresh(db_sub)
            return Submission(
                id=db_sub.id,
                user_id=db_sub.user_id,
                assignment_id=db_sub.assignment_id,
                uploaded_at=db_sub.uploaded_at,
                file_url=db_sub.file_url,
                text=db_sub.text
            )

    async def get(self, sub_id: str) -> Optional[Submission]:
        """Get a submission by ID."""
        await self.initialize()
        async with self.async_session() as session:
            result = await session.execute(
                select(SubmissionModel).where(SubmissionModel.id == sub_id)
            )
            db_sub = result.scalar_one_or_none()
            if db_sub:
                return Submission(
                    id=db_sub.id,
                    user_id=db_sub.user_id,
                    assignment_id=db_sub.assignment_id,
                    uploaded_at=db_sub.uploaded_at,
                    file_url=db_sub.file_url,
                    text=db_sub.text
                )
            return None

    async def get_by_user(self, user_id: str) -> List[Submission]:
        """Get all submissions for a specific user."""
        await self.initialize()
        async with self.async_session() as session:
            result = await session.execute(
                select(SubmissionModel)
                .where(SubmissionModel.user_id == user_id)
                .order_by(SubmissionModel.uploaded_at.desc())
            )
            db_subs = result.scalars().all()
            return [
                Submission(
                    id=db_sub.id,
                    user_id=db_sub.user_id,
                    assignment_id=db_sub.assignment_id,
                    uploaded_at=db_sub.uploaded_at,
                    file_url=db_sub.file_url,
                    text=db_sub.text
                )
                for db_sub in db_subs
            ]
    
    async def get_all(self) -> List[Submission]:
        """Get all submissions."""
        await self.initialize()
        async with self.async_session() as session:
            result = await session.execute(
                select(SubmissionModel).order_by(SubmissionModel.uploaded_at.desc())
            )
            db_subs = result.scalars().all()
            return [
                Submission(
                    id=db_sub.id,
                    user_id=db_sub.user_id,
                    assignment_id=db_sub.assignment_id,
                    uploaded_at=db_sub.uploaded_at,
                    file_url=db_sub.file_url,
                    text=db_sub.text
                )
                for db_sub in db_subs
            ]
