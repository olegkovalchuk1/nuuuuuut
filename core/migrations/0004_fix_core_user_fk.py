# Generated manually on 2026-05-08

from django.db import migrations


def fix_core_user_foreign_keys(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    table_specs = [
        ("core_goaltest", "user_id", False),
        ("core_userprofile", "user_id", False),
        ("core_recipe", "created_by_id", True),
        ("core_workout", "created_by_id", True),
        ("core_kcaltracker", "user_id", False),
        ("core_mealschedule", "user_id", False),
        ("core_progresstracker", "user_id", False),
        ("core_watertracker", "user_id", False),
        ("core_workouttracker", "user_id", False),
        ("core_notification", "user_id", False),
    ]

    with schema_editor.connection.cursor() as cursor:
        for table_name, column_name, nullable in table_specs:
            if nullable:
                cursor.execute(
                    f"""
                    UPDATE "{table_name}"
                    SET "{column_name}" = NULL
                    WHERE "{column_name}" IS NOT NULL
                      AND "{column_name}" NOT IN (SELECT id FROM "accounts_customuser")
                    """
                )
            else:
                cursor.execute(
                    f"""
                    DELETE FROM "{table_name}"
                    WHERE "{column_name}" NOT IN (SELECT id FROM "accounts_customuser")
                    """
                )

            cursor.execute(
                """
                SELECT con.conname
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                JOIN pg_attribute att
                    ON att.attrelid = rel.oid
                   AND att.attnum = ANY(con.conkey)
                WHERE con.contype = 'f'
                  AND rel.relname = %s
                  AND att.attname = %s
                """,
                [table_name, column_name],
            )
            constraint_names = [row[0] for row in cursor.fetchall()]
            for constraint_name in constraint_names:
                cursor.execute(
                    f'ALTER TABLE "{table_name}" DROP CONSTRAINT IF EXISTS "{constraint_name}"'
                )

            target_constraint = f"{table_name}_{column_name}_fk_accounts_customuser"[:63]
            cursor.execute(
                f'ALTER TABLE "{table_name}" DROP CONSTRAINT IF EXISTS "{target_constraint}"'
            )
            cursor.execute(
                f"""
                ALTER TABLE "{table_name}"
                ADD CONSTRAINT "{target_constraint}"
                FOREIGN KEY ("{column_name}")
                REFERENCES "accounts_customuser" ("id")
                DEFERRABLE INITIALLY DEFERRED
                """
            )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_notification"),
    ]

    operations = [
        migrations.RunPython(fix_core_user_foreign_keys, migrations.RunPython.noop),
    ]
