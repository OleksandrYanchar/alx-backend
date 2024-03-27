"""empty message

Revision ID: 0a1ccc575eba
Revises: 75c21b36e510
Create Date: 2024-03-27 11:42:28.771741

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0a1ccc575eba"
down_revision = "75c21b36e510"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("bugreports_title_key", "bugreports", type_="unique")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint("bugreports_title_key", "bugreports", ["title"])
    # ### end Alembic commands ###