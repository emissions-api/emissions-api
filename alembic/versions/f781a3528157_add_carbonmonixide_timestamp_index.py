"""add carbonmonoxide.timestamp index

Revision ID: f781a3528157
Revises:
Create Date: 2019-11-17 14:26:01.702418+00:00

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'f781a3528157'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(op.f('ix_carbonmonoxide_timestamp'),
                    'carbonmonoxide', ['timestamp'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_carbonmonoxide_timestamp'),
                  table_name='carbonmonoxide')
