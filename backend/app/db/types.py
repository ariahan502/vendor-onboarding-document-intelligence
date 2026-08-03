from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB


json_type = JSON().with_variant(JSONB, "postgresql")
