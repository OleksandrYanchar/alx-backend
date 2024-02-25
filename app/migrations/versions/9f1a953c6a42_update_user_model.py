"""UPDATE user model

Revision ID: 9f1a953c6a42
Revises: 
Create Date: 2024-02-24 06:31:36.434991

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9f1a953c6a42"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "blacklisted_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("blacklisted_on", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("username", sa.String(length=32), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("first_name", sa.String(length=64), nullable=False),
        sa.Column("last_name", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=64), nullable=False),
        sa.Column("joined_at", sa.Date(), nullable=False),
        sa.Column("is_activated", sa.Boolean(), nullable=False),
        sa.Column("is_vip", sa.Boolean(), nullable=False),
        sa.Column("is_staff", sa.Boolean(), nullable=False),
        sa.Column("image", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("users")
    op.drop_table("blacklisted_tokens")
    # ### end Alembic commands ###