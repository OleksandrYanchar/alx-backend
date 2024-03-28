"""empty message

Revision ID: 23fa14e3ff70
Revises: 175edb69b15b
Create Date: 2024-03-28 20:43:20.405425

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23fa14e3ff70'
down_revision = '175edb69b15b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('bugreportcomments_author_fkey', 'bugreportcomments', type_='foreignkey')
    op.drop_column('bugreportcomments', 'author')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bugreportcomments', sa.Column('author', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.create_foreign_key('bugreportcomments_author_fkey', 'bugreportcomments', 'users', ['author'], ['username'], ondelete='CASCADE')
    # ### end Alembic commands ###