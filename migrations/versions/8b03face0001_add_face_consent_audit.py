"""Track face consent provenance, withdrawal and deletion progress."""
from alembic import op
import sqlalchemy as sa
revision = "8b03face0001"
down_revision = "5f2d0ace900c"
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table("student_faces") as b:
        b.add_column(sa.Column("consent_at", sa.DateTime(timezone=True)))
        b.add_column(sa.Column("consent_actor_id", sa.Integer()))
        b.add_column(sa.Column("consent_reference", sa.String(150)))
        b.add_column(sa.Column("consent_withdrawn_at", sa.DateTime(timezone=True)))
        b.add_column(sa.Column("deletion_pending", sa.Boolean(), nullable=False, server_default=sa.false()))
        b.create_foreign_key("fk_face_consent_actor", "users", ["consent_actor_id"], ["id"])
    op.create_table("face_consent_audits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("reference", sa.String(150)),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_face_consent_audits_student_id", "face_consent_audits", ["student_id"])

def downgrade():
    op.drop_index("ix_face_consent_audits_student_id", "face_consent_audits")
    op.drop_table("face_consent_audits")
    with op.batch_alter_table("student_faces") as b:
        b.drop_constraint("fk_face_consent_actor", type_="foreignkey")
        for name in ("deletion_pending", "consent_withdrawn_at", "consent_reference", "consent_actor_id", "consent_at"):
            b.drop_column(name)
