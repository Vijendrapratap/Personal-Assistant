"""Initial schema for Alfred

Revision ID: 0001
Revises:
Create Date: 2026-01-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('preferences', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('color', sa.String(7)),
        sa.Column('icon', sa.String(50)),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='SET NULL'), index=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('status', sa.String(50), default='pending', index=True),
        sa.Column('priority', sa.String(20), default='medium'),
        sa.Column('due_date', sa.DateTime(timezone=True), index=True),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('tags', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Habits table
    op.create_table(
        'habits',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('frequency', sa.String(20), default='daily'),
        sa.Column('target_count', sa.Integer, default=1),
        sa.Column('icon', sa.String(50)),
        sa.Column('color', sa.String(7)),
        sa.Column('current_streak', sa.Integer, default=0),
        sa.Column('longest_streak', sa.Integer, default=0),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Habit logs table
    op.create_table(
        'habit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('habit_id', sa.String(36), sa.ForeignKey('habits.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('count', sa.Integer, default=1),
        sa.Column('notes', sa.Text),
    )

    # Conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(255)),
        sa.Column('summary', sa.Text),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('role', sa.String(20), nullable=False),  # user, assistant, system, tool
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('tool_calls', postgresql.JSONB),
        sa.Column('tool_call_id', sa.String(100)),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('type', sa.String(50), nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('body', sa.Text),
        sa.Column('data', postgresql.JSONB, default={}),
        sa.Column('status', sa.String(20), default='pending', index=True),  # pending, sent, read, dismissed
        sa.Column('scheduled_for', sa.DateTime(timezone=True), index=True),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('read_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Push tokens table
    op.create_table(
        'push_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('token', sa.String(500), nullable=False, unique=True),
        sa.Column('platform', sa.String(20)),  # ios, android
        sa.Column('device_id', sa.String(255)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Connectors table (for OAuth integrations)
    op.create_table(
        'connectors',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('provider', sa.String(50), nullable=False, index=True),  # google, notion, slack, etc.
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('access_token', sa.Text),  # Encrypted
        sa.Column('refresh_token', sa.Text),  # Encrypted
        sa.Column('token_expires_at', sa.DateTime(timezone=True)),
        sa.Column('scopes', postgresql.ARRAY(sa.String)),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('user_id', 'provider', name='unique_user_provider'),
    )

    # Knowledge entities table (for knowledge graph sync)
    op.create_table(
        'knowledge_entities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('type', sa.String(50), nullable=False, index=True),  # person, company, project, concept, etc.
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('properties', postgresql.JSONB, default={}),
        sa.Column('source', sa.String(50)),  # conversation, connector, manual
        sa.Column('confidence', sa.Float, default=1.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create indexes for common queries
    op.create_index('idx_tasks_user_status', 'tasks', ['user_id', 'status'])
    op.create_index('idx_tasks_user_due', 'tasks', ['user_id', 'due_date'])
    op.create_index('idx_habits_user_active', 'habits', ['user_id', 'is_active'])
    op.create_index('idx_messages_conversation_created', 'messages', ['conversation_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_messages_conversation_created')
    op.drop_index('idx_habits_user_active')
    op.drop_index('idx_tasks_user_due')
    op.drop_index('idx_tasks_user_status')

    op.drop_table('knowledge_entities')
    op.drop_table('connectors')
    op.drop_table('push_tokens')
    op.drop_table('notifications')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('habit_logs')
    op.drop_table('habits')
    op.drop_table('tasks')
    op.drop_table('projects')
    op.drop_table('users')
