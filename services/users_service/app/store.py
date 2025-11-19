"""User store with PostgreSQL backend using SQLAlchemy async."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, select
from libs.events.schemas import User
from config.settings import get_settings
import asyncio

settings = get_settings()


# SQLAlchemy models
class Base(DeclarativeBase):
    pass


class UserModel(Base):
    """SQLAlchemy model for User."""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)


class UserStore:
    """Async PostgreSQL-backed user store."""
    
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

    async def create(self, user: User) -> User:
        """Create a new user."""
        await self.initialize()
        async with self.async_session() as session:
            db_user = UserModel(
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role
            )
            session.add(db_user)
            await session.commit()
            await session.refresh(db_user)
            return User(
                id=db_user.id,
                name=db_user.name,
                email=db_user.email,
                role=db_user.role
            )

    async def get(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        await self.initialize()
        async with self.async_session() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            db_user = result.scalar_one_or_none()
            if db_user:
                return User(
                    id=db_user.id,
                    name=db_user.name,
                    email=db_user.email,
                    role=db_user.role
                )
            return None

    async def list(self) -> List[User]:
        """List all users."""
        await self.initialize()
        async with self.async_session() as session:
            result = await session.execute(select(UserModel))
            db_users = result.scalars().all()
            return [
                User(
                    id=db_user.id,
                    name=db_user.name,
                    email=db_user.email,
                    role=db_user.role
                )
                for db_user in db_users
            ]

    async def update(self, user_id: str, user: User) -> User:
        """Update a user."""
        await self.initialize()
        async with self.async_session() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            db_user = result.scalar_one_or_none()
            if db_user:
                db_user.name = user.name
                db_user.email = user.email
                db_user.role = user.role
                await session.commit()
                await session.refresh(db_user)
                return User(
                    id=db_user.id,
                    name=db_user.name,
                    email=db_user.email,
                    role=db_user.role
                )
            return None

    async def delete(self, user_id: str) -> Optional[User]:
        """Delete a user."""
        await self.initialize()
        async with self.async_session() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            db_user = result.scalar_one_or_none()
            if db_user:
                user = User(
                    id=db_user.id,
                    name=db_user.name,
                    email=db_user.email,
                    role=db_user.role
                )
                await session.delete(db_user)
                await session.commit()
                return user
            return None


store = UserStore()
