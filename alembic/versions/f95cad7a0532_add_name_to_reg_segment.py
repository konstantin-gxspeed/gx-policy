"""add name to reg segment

Revision ID: f95cad7a0532
Revises: fce61c6bb741
Create Date: 2024-10-07 16:19:14.645637

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f95cad7a0532'
down_revision: Union[str, None] = 'fce61c6bb741'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('setups',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('title', sa.Integer(), nullable=False),
                    sa.Column('parts', sa.JSON(), nullable=False),

                    sa.PrimaryKeyConstraint('id')
                    )

    op.alter_column('sop_segment_on_regulation_segment', 'similarity',
                    existing_type=sa.REAL(),
                    type_=sa.Float(precision=2),
                    existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('sop_segment_on_regulation_segment', 'similarity',
                    existing_type=sa.Float(precision=2),
                    type_=sa.REAL(),
                    existing_nullable=True)
    op.drop_column('setups', 'parts')
    op.drop_column('setups', 'title')
    # ### end Alembic commands ###
