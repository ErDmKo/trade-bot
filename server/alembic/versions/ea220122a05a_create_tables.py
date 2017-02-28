"""create tables

Revision ID: ea220122a05a
Revises: 
Create Date: 2017-02-28 23:32:18.425100

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'ea220122a05a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('order', sa.Column('extra', JSONB))


def downgrade():
    op.drop_column('order', '')
