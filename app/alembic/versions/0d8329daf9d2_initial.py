"""initial

Revision ID: 0d8329daf9d2
Revises:
Create Date: 2018-09-19 13:11:46.537907

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0d8329daf9d2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
  op.create_table('group',
    sa.Column('id', sa.BigInteger, primary_key=True),
    sa.Column('name', sa.String(250), nullable=False),
    sa.Column('org_id', sa.BigInteger, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
    sa.Column('last_modified_at', sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False)
  )

  op.create_table('email',
    sa.Column('id', sa.BigInteger, primary_key=True),
    sa.Column('email', sa.String(250), nullable=False),
    sa.Column('org_id', sa.BigInteger, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
    sa.Column('last_modified_at', sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False)
  )

  op.create_table('group_email',
    sa.Column('id', sa.BigInteger, primary_key=True),
    sa.Column('group_id', sa.BigInteger, sa.ForeignKey('group.id'), nullable=False),
    sa.Column('email_id', sa.BigInteger, sa.ForeignKey('email.id'), nullable=False),
    sa.Column('org_id', sa.BigInteger, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
    sa.Column('last_modified_at', sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False)
  )

  op.create_table('email_namespace',
    sa.Column('id', sa.BigInteger, primary_key=True),
    sa.Column('email_id', sa.BigInteger, sa.ForeignKey('email.id'), nullable=False),
    sa.Column('namespace', sa.String(250), nullable=False),
    sa.Column('org_id', sa.BigInteger, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
    sa.Column('last_modified_at', sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False)
  )

  op.create_table('activation',
    sa.Column('id', sa.BigInteger, primary_key=True),
    sa.Column('namespace', sa.String(250), nullable=False),
    sa.Column('activation_token', sa.String(2000), nullable=False),
    sa.Column('org_id', sa.BigInteger, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.current_timestamp(), nullable=False),
  )
  op.create_unique_constraint('uq_activation', 'activation', ['activation_token'])

def downgrade():
  op.drop_table('activation')
  op.drop_table('email_namespace')
  op.drop_table('group_email')
  op.drop_table('email')
  op.drop_table('group')
