"""initial

Revision ID: 1177f89ef9c8
Revises:
Create Date: 2026-04-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1177f89ef9c8'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('role', sa.Enum('USER', 'ADMIN', name='roleenum'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table(
        'vehicles',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('brand', sa.String(length=100), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('color', sa.String(length=50), nullable=False),
        sa.Column('license_plate', sa.String(length=10), nullable=False),
        sa.Column('price_usd', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_vehicles_license_plate'), 'vehicles', ['license_plate'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_vehicles_license_plate'), table_name='vehicles')
    op.drop_table('vehicles')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
