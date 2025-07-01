"""create image table

Revision ID: a3443c7b63ec
Revises: 
Create Date: 2025-06-29 18:43:54.873150

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3443c7b63ec'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('images',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('location', sa.String(), nullable=False),
                    sa.Column('hash', sa.String(32), nullable=False),
                    sa.Column('description', sa.Unicode(256), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    os.drop_table('images')
