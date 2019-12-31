"""drop carbonmonoxide id

Revision ID: b3ae57ee07d4
Revises: f781a3528157
Create Date: 2019-12-31 17:30:56.008352+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import Sequence, CreateSequence


# revision identifiers, used by Alembic.
revision = 'b3ae57ee07d4'
down_revision = 'f781a3528157'
branch_labels = None
depends_on = None


def upgrade():
    # Drop id as primary key
    op.drop_column('carbonmonoxide', 'id')


def downgrade():
    # Create new column 'id' and autoincrement its value
    op.execute(CreateSequence(Sequence("carbonmonoxide_id_seq")))
    op.add_column('carbonmonoxide', sa.Column(
        'id', sa.INTEGER(), nullable=False,
        server_default=sa.text("nextval('carbonmonoxide_id_seq'::regclass)")))

    # Use 'id' as the new primary key
    op.create_primary_key('carbonmonoxide_pkey', 'carbonmonoxide', ['id'])
