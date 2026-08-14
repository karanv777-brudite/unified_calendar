from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tokens import UserAccountToken

class TokenRepository:
    """
    Repository pattern for handling token persistence operations.
    Keeps database queries decoupled from business logic and controllers (SRP).
    """

    @staticmethod
    async def get_tokens_by_user(db: AsyncSession, user_id: str):
        """Fetches all stored token records for a specific user."""
        result = await db.execute(
            select(UserAccountToken).filter(UserAccountToken.user_id == user_id)
        )
        return result.scalars().all()

    @staticmethod
    async def save_or_update_token(
        db: AsyncSession,
        user_id: str,
        account_key: str,
        provider: str,
        email: str,
        access_token: str,
        refresh_token: str = None
    ):
        """Creates a new token entry or updates an existing one securely."""
        token_id = f"{user_id}_{account_key}"
        result = await db.execute(
            select(UserAccountToken).filter(UserAccountToken.id == token_id)
        )
        db_token = result.scalars().first()

        if not db_token:
            db_token = UserAccountToken(
                id=token_id,
                user_id=user_id,
                account_key=account_key,
                provider=provider,
                email=email
            )
            db.add(db_token)

        # Assigning tokens triggers the automatic encryption setters on the model
        db_token.access_token = access_token
        if refresh_token:
            db_token.refresh_token = refresh_token

        await db.commit()
        await db.refresh(db_token)
        return db_token

    @staticmethod
    async def delete_token(db: AsyncSession, user_id: str, account_key: str) -> bool:
        
        result = await db.execute(
            select(UserAccountToken).where(
                UserAccountToken.user_id == user_id,
                UserAccountToken.account_key == account_key
            )
        )
        token_record = result.scalar_one_or_none()
        if token_record:
            await db.delete(token_record)
            await db.commit()
            return True
        return False