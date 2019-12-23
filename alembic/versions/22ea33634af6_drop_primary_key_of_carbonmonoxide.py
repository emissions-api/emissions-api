"""Drop primary key of carbonmonoxide

Revision ID: 22ea33634af6
Revises: f781a3528157
Create Date: 2019-12-23 09:58:44.978470+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import Sequence, CreateSequence


# revision identifiers, used by Alembic.
revision = '22ea33634af6'
down_revision = 'f781a3528157'
branch_labels = None
depends_on = None


def upgrade():
    # Drop id as primary key
    op.drop_column('carbonmonoxide', 'id')

    # Drop index on timestamp
    op.drop_index('ix_carbonmonoxide_timestamp')

    # Use ('timestamp', 'geom') as the new primary key
    op.create_primary_key('carbonmonoxide_pkey',
                          'carbonmonoxide', ['timestamp', 'geom'])


def downgrade():
    # Create new column 'id' and autoincrement its value
    op.execute(CreateSequence(Sequence("carbonmonoxide_id_seq")))
    op.add_column('carbonmonoxide', sa.Column(
        'id', sa.INTEGER(), nullable=False,
        server_default=sa.text("nextval('carbonmonoxide_id_seq'::regclass)")))

    # Drop primary key
    op.drop_constraint('carbonmonoxide_pkey',
                       'carbonmonoxide', type_='primary')

    # Use 'id' as the new primary key
    op.create_primary_key('carbonmonoxide_pkey', 'carbonmonoxide', ['id'])
