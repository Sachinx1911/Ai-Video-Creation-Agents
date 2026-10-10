"""foundation

Revision ID: 0001
Revises: 
Create Date: 2026-10-10 18:35:44.219619
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('audit_logs',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('entity_type', sa.String(length=50), nullable=False),
    sa.Column('entity_id', sa.String(length=64), nullable=False),
    sa.Column('action', sa.String(length=50), nullable=False),
    sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs'))
    )
    op.create_index('ix_audit_entity', 'audit_logs', ['entity_type', 'entity_id'], unique=False)
    op.create_table('projects',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('topic', sa.Text(), nullable=False),
    sa.Column('target_audience', sa.String(length=300), nullable=True),
    sa.Column('language', sa.Enum('mr', 'hi', 'en', name='language', native_enum=False, create_constraint=False, length=32), nullable=False),
    sa.Column('platform', sa.Enum('instagram_reels', 'youtube_shorts', name='platform', native_enum=False, create_constraint=False, length=32), nullable=False),
    sa.Column('target_duration_sec', sa.Integer(), nullable=False),
    sa.Column('style', sa.Enum('cinematic_documentary', 'photorealistic_commercial', 'educational_explainer', 'animation_3d', name='video_style', native_enum=False, create_constraint=False, length=32), nullable=False),
    sa.Column('visual_method', sa.Enum('ai_images', 'ai_video', 'ai_images_and_video', name='visual_method', native_enum=False, create_constraint=False, length=32), nullable=False),
    sa.Column('aspect_ratio', sa.String(length=8), nullable=False),
    sa.Column('export_preset', sa.String(length=64), nullable=False),
    sa.Column('width', sa.Integer(), nullable=False),
    sa.Column('height', sa.Integer(), nullable=False),
    sa.Column('fps', sa.Integer(), nullable=False),
    sa.Column('voiceover_enabled', sa.Boolean(), nullable=False),
    sa.Column('captions_enabled', sa.Boolean(), nullable=False),
    sa.Column('voice_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('caption_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('branding', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('provider_preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('status', sa.Enum('draft', 'planning', 'generating', 'rendering', 'review', 'completed', 'failed', name='project_status', native_enum=False, create_constraint=False, length=32), nullable=False),
    sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('current_revision', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("language IN ('mr', 'hi', 'en')", name=op.f('ck_projects_language')),
    sa.CheckConstraint("platform IN ('instagram_reels', 'youtube_shorts')", name=op.f('ck_projects_platform')),
    sa.CheckConstraint("status IN ('draft', 'planning', 'generating', 'rendering', 'review', 'completed', 'failed')", name=op.f('ck_projects_project_status')),
    sa.CheckConstraint("style IN ('cinematic_documentary', 'photorealistic_commercial', 'educational_explainer', 'animation_3d')", name=op.f('ck_projects_video_style')),
    sa.CheckConstraint("visual_method IN ('ai_images', 'ai_video', 'ai_images_and_video')", name=op.f('ck_projects_visual_method')),
    sa.CheckConstraint('target_duration_sec BETWEEN 5 AND 180', name=op.f('ck_projects_duration_range')),
    sa.CheckConstraint('width > 0 AND height > 0 AND fps BETWEEN 1 AND 120', name=op.f('ck_projects_video_dims')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_projects'))
    )
    op.create_index('ix_projects_archived_updated', 'projects', ['archived_at', 'updated_at'], unique=False)
    op.create_index('ix_projects_status', 'projects', ['status'], unique=False)
    op.create_table('worker_heartbeats',
    sa.Column('worker_id', sa.String(length=200), nullable=False),
    sa.Column('hostname', sa.String(length=200), nullable=False),
    sa.Column('pid', sa.Integer(), nullable=False),
    sa.Column('job_types', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('worker_id', name=op.f('pk_worker_heartbeats'))
    )
    op.create_table('assets',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('project_id', sa.UUID(), nullable=False),
    sa.Column('kind', sa.Enum('image', 'video', 'voice', 'music', 'sfx', 'logo', 'font', 'reference_image', 'subtitle', 'final_export', 'other', name='asset_kind', native_enum=False, create_constraint=False, length=32), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('origin', sa.Enum('upload', 'generated', 'rendered', name='asset_origin', native_enum=False, create_constraint=False, length=32), nullable=False),
    sa.Column('license_note', sa.Text(), nullable=True),
    sa.Column('scene_id', sa.UUID(), nullable=True),
    sa.Column('current_version', sa.Integer(), nullable=False),
    sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("kind IN ('image', 'video', 'voice', 'music', 'sfx', 'logo', 'font', 'reference_image', 'subtitle', 'final_export', 'other')", name=op.f('ck_assets_asset_kind')),
    sa.CheckConstraint("origin IN ('upload', 'generated', 'rendered')", name=op.f('ck_assets_asset_origin')),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_assets_project_id_projects'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_assets'))
    )
    op.create_index('ix_assets_project_kind', 'assets', ['project_id', 'kind'], unique=False)
    op.create_table('jobs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('type', sa.String(length=64), nullable=False),
    sa.Column('status', sa.Enum('queued', 'running', 'awaiting_retry', 'succeeded', 'failed', 'cancelled', name='job_status', native_enum=False, create_constraint=False, length=32), nullable=False),
    sa.Column('project_id', sa.UUID(), nullable=True),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('error_category', sa.Enum('transient', 'rate_limited', 'provider_outage', 'invalid_request', 'auth', 'invalid_output', 'internal', 'cancelled', 'lease_expired', name='error_category', native_enum=False, create_constraint=False, length=32), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('attempts', sa.Integer(), nullable=False),
    sa.Column('max_attempts', sa.Integer(), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('run_after', sa.DateTime(timezone=True), nullable=False),
    sa.Column('locked_by', sa.String(length=200), nullable=True),
    sa.Column('lease_expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('cancel_requested', sa.Boolean(), nullable=False),
    sa.Column('idempotency_key', sa.String(length=200), nullable=True),
    sa.Column('provider_job_id', sa.String(length=200), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("error_category IN ('transient', 'rate_limited', 'provider_outage', 'invalid_request', 'auth', 'invalid_output', 'internal', 'cancelled', 'lease_expired')", name=op.f('ck_jobs_error_category')),
    sa.CheckConstraint("status IN ('queued', 'running', 'awaiting_retry', 'succeeded', 'failed', 'cancelled')", name=op.f('ck_jobs_job_status')),
    sa.CheckConstraint('attempts >= 0 AND max_attempts >= 1', name=op.f('ck_jobs_attempts_range')),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_jobs_project_id_projects'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_jobs')),
    sa.UniqueConstraint('idempotency_key', name=op.f('uq_jobs_idempotency_key'))
    )
    op.create_index('ix_jobs_claim', 'jobs', ['status', 'run_after', 'priority', 'created_at'], unique=False)
    op.create_index('ix_jobs_project', 'jobs', ['project_id'], unique=False)
    op.create_index('ix_jobs_type', 'jobs', ['type'], unique=False)
    op.create_table('project_revisions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('project_id', sa.UUID(), nullable=False),
    sa.Column('revision', sa.Integer(), nullable=False),
    sa.Column('snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('change_summary', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_project_revisions_project_id_projects'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_project_revisions')),
    sa.UniqueConstraint('project_id', 'revision', name='uq_project_revision')
    )
    op.create_table('asset_versions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('asset_id', sa.UUID(), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('storage_key', sa.String(length=500), nullable=False),
    sa.Column('original_filename', sa.String(length=255), nullable=False),
    sa.Column('mime_type', sa.String(length=100), nullable=False),
    sa.Column('size_bytes', sa.BigInteger(), nullable=False),
    sa.Column('sha256', sa.String(length=64), nullable=False),
    sa.Column('validation_status', sa.Enum('pending', 'valid', 'invalid', name='validation_status', native_enum=False, create_constraint=False, length=32), nullable=False),
    sa.Column('validation_error', sa.Text(), nullable=True),
    sa.Column('media_info', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("validation_status IN ('pending', 'valid', 'invalid')", name=op.f('ck_asset_versions_validation_status')),
    sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], name=op.f('fk_asset_versions_asset_id_assets'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_asset_versions')),
    sa.UniqueConstraint('asset_id', 'version', name='uq_asset_version')
    )
    op.create_index('ix_asset_versions_sha256', 'asset_versions', ['sha256'], unique=False)
    op.create_table('job_events',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('job_id', sa.UUID(), nullable=False),
    sa.Column('from_status', sa.String(length=32), nullable=True),
    sa.Column('to_status', sa.String(length=32), nullable=False),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], name=op.f('fk_job_events_job_id_jobs'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_events'))
    )
    op.create_index('ix_job_events_job', 'job_events', ['job_id', 'id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_job_events_job', table_name='job_events')
    op.drop_table('job_events')
    op.drop_index('ix_asset_versions_sha256', table_name='asset_versions')
    op.drop_table('asset_versions')
    op.drop_table('project_revisions')
    op.drop_index('ix_jobs_type', table_name='jobs')
    op.drop_index('ix_jobs_project', table_name='jobs')
    op.drop_index('ix_jobs_claim', table_name='jobs')
    op.drop_table('jobs')
    op.drop_index('ix_assets_project_kind', table_name='assets')
    op.drop_table('assets')
    op.drop_table('worker_heartbeats')
    op.drop_index('ix_projects_status', table_name='projects')
    op.drop_index('ix_projects_archived_updated', table_name='projects')
    op.drop_table('projects')
    op.drop_index('ix_audit_entity', table_name='audit_logs')
    op.drop_table('audit_logs')
