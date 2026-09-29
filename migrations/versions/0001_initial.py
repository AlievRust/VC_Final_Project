"""Первичная схема базы знаний.

Revision ID: 0001
Revises:
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import VECTOR

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "snippets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", VECTOR(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_snippets_document_chunk"),
    )
    op.create_index("ix_snippets_document_id", "snippets", ["document_id"])
    op.create_table(
        "qa_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("sources", sa.JSON(), nullable=False),
        sa.Column("needs_review", sa.Boolean(), nullable=False),
        sa.Column("review_reason", sa.Text()),
        sa.Column("diagnostics", sa.JSON(), nullable=False),
    )
    op.create_table(
        "audit_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.Integer()),
        sa.Column("details", sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_runs")
    op.drop_table("qa_runs")
    op.drop_index("ix_snippets_document_id", table_name="snippets")
    op.drop_table("snippets")
    op.drop_table("documents")
