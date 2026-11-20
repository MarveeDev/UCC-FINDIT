"""add google auth exchange

Revision ID: 7fa22af16a2e
Revises: f0fd5f6a3d17
Create Date: 2026-11-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7fa22af16a2e'
down_revision = 'f0fd5f6a3d17'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('auth_exchanges',
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('consumed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('code')
    )
    op.create_index(op.f('ix_auth_exchanges_user_id'), 'auth_exchanges', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_auth_exchanges_user_id'), table_name='auth_exchanges')
    op.drop_table('auth_exchanges')
