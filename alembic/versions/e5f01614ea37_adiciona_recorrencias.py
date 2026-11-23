"""adiciona recorrencias

Revision ID: e5f01614ea37
Revises: 96e73d72a4a2
Create Date: 2026-11-22 23:47:09.007031

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f01614ea37'
down_revision: Union[str, Sequence[str], None] = '96e73d72a4a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'recorrencias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('descricao', sa.String(), nullable=False),
        sa.Column('valor', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('categoria', sa.String(), nullable=False),
        sa.Column('tipo', sa.String(), nullable=False),
        sa.Column('dia_vencimento', sa.Integer(), nullable=False),
        sa.Column('data_inicio', sa.Date(), nullable=False),
        sa.Column('data_fim', sa.Date(), nullable=True),
        sa.Column('ativa', sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "tipo IN ('receita', 'despesa')", name='ck_recorrencias_tipo'
        ),
        sa.CheckConstraint(
            'dia_vencimento >= 1 AND dia_vencimento <= 31',
            name='ck_recorrencias_dia_vencimento',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_recorrencias_id'), 'recorrencias', ['id'], unique=False
    )

    # SQLite nao suporta ALTER de constraint; batch mode recria a tabela
    # (copy-and-move) preservando os dados e permitindo a FK.
    with op.batch_alter_table('despesas') as batch_op:
        batch_op.add_column(
            sa.Column('recorrencia_id', sa.Integer(), nullable=True)
        )
        batch_op.create_index(
            'uq_despesas_recorrencia_data',
            ['recorrencia_id', 'data'],
            unique=True,
        )
        batch_op.create_foreign_key(
            'fk_despesas_recorrencia',
            'recorrencias',
            ['recorrencia_id'],
            ['id'],
        )

    with op.batch_alter_table('receitas') as batch_op:
        batch_op.add_column(
            sa.Column('recorrencia_id', sa.Integer(), nullable=True)
        )
        batch_op.create_index(
            'uq_receitas_recorrencia_data',
            ['recorrencia_id', 'data'],
            unique=True,
        )
        batch_op.create_foreign_key(
            'fk_receitas_recorrencia',
            'recorrencias',
            ['recorrencia_id'],
            ['id'],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('receitas') as batch_op:
        batch_op.drop_constraint(
            'fk_receitas_recorrencia', type_='foreignkey'
        )
        batch_op.drop_index('uq_receitas_recorrencia_data')
        batch_op.drop_column('recorrencia_id')

    with op.batch_alter_table('despesas') as batch_op:
        batch_op.drop_constraint(
            'fk_despesas_recorrencia', type_='foreignkey'
        )
        batch_op.drop_index('uq_despesas_recorrencia_data')
        batch_op.drop_column('recorrencia_id')

    op.drop_index(op.f('ix_recorrencias_id'), table_name='recorrencias')
    op.drop_table('recorrencias')
