"""
Migration: profile.yaml schema v1.0 → v2.0 (placeholder)

This file is a scaffold for the first future migration.
When profile.yaml schema changes from 1.0 to 2.0:
1. Implement migrate() below
2. Update CURRENT_SCHEMA_VERSION in src/profile.py to "2.0"
3. Add the migration to the registry in src/profile.py

Migration contract:
- migrate() receives the raw dict from profile.yaml
- Returns a new dict representing the v2.0 schema
- Must be idempotent (safe to run twice)
- Must not raise on valid v1.0 input
"""


def migrate(profile_data: dict) -> dict:
    """Migrate a v1.0 profile dict to v2.0 schema.

    Not yet implemented — placeholder for future schema changes.
    """
    raise NotImplementedError(
        "v1.0 → v2.0 migration has not been implemented yet. "
        "This file is a scaffold — implement migrate() when the schema changes."
    )
