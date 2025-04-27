"""allow_null_score

Revision ID: 1dc3b0f16b7f
Revises: 44220055549a
Create Date: 2025-04-25 11:33:51.403492

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1dc3b0f16b7f'
down_revision: Union[str, None] = '44220055549a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建新表
    op.create_table('evaluations_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paper_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )
    op.create_index(op.f('ix_evaluations_id'), 'evaluations_new', ['id'], unique=False)

    # 复制数据
    op.execute('INSERT INTO evaluations_new SELECT * FROM evaluations')

    # 删除旧表
    op.drop_table('evaluations')

    # 重命名新表
    op.rename_table('evaluations_new', 'evaluations')


def downgrade() -> None:
    # 创建新表
    op.create_table('evaluations_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paper_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

    # 复制数据（忽略 NULL 值）
    op.execute('INSERT INTO evaluations_new SELECT * FROM evaluations WHERE score IS NOT NULL')

    # 删除旧表
    op.drop_table('evaluations')

    # 重命名新表
    op.rename_table('evaluations_new', 'evaluations')

    # 重新创建索引
    op.create_index(op.f('ix_evaluations_id'), 'evaluations', ['id'], unique=False)
