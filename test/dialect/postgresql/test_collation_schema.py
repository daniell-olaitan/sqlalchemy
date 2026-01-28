"""Tests for schema-qualified collation rendering in PostgreSQL DDL."""
from sqlalchemy import String, Text, Unicode, testing
from sqlalchemy.dialects import postgresql
from sqlalchemy.testing import fixtures
from sqlalchemy.testing.assertions import AssertsCompiledSQL


class SchemaQualifiedCollationTest(AssertsCompiledSQL, fixtures.TestBase):
    """Tests for schema-qualified collation rendering in PostgreSQL DDL."""

    __dialect__ = "postgresql"

    def test_text_simple_collation_is_quoted(self):
        """Text type with simple collation is quoted."""
        self.assert_compile(
            Text(collation="en_US"), 'TEXT COLLATE "en_US"'
        )

    def test_string_simple_collation_is_quoted(self):
        """String type with simple collation is quoted."""
        self.assert_compile(
            String(50, collation="en_US"), 'VARCHAR(50) COLLATE "en_US"'
        )

    def test_unicode_simple_collation_is_quoted(self):
        """Unicode type with simple collation is quoted."""
        self.assert_compile(
            Unicode(50, collation="en_US"), 'VARCHAR(50) COLLATE "en_US"'
        )

    def test_text_schema_qualified_collation_not_fully_quoted(self):
        """Text type with schema-qualified collation not fully quoted."""
        self.assert_compile(
            Text(collation="my_schema.my_collation"),
            "TEXT COLLATE my_schema.my_collation",
        )

    def test_string_schema_qualified_collation_not_fully_quoted(self):
        """String type with schema-qualified collation not fully quoted."""
        self.assert_compile(
            String(50, collation="my_schema.my_collation"),
            "VARCHAR(50) COLLATE my_schema.my_collation",
        )

    def test_unicode_schema_qualified_collation_not_fully_quoted(self):
        """Unicode type with schema-qualified collation not fully quoted."""
        self.assert_compile(
            Unicode(50, collation="my_schema.my_collation"),
            "VARCHAR(50) COLLATE my_schema.my_collation",
        )

    def test_text_with_custom_schema_qualified_collation(self):
        """Text type with custom schema-qualified collation."""
        self.assert_compile(
            Text(collation="custom_schema.unicode_ci"),
            "TEXT COLLATE custom_schema.unicode_ci",
        )

    def test_string_with_length_and_schema_qualified_collation(self):
        """String type with length and schema-qualified collation."""
        self.assert_compile(
            String(255, collation="my_schema.my_collation"),
            "VARCHAR(255) COLLATE my_schema.my_collation",
        )

    def test_unicode_with_length_and_schema_qualified_collation(self):
        """Unicode type with length and schema-qualified collation."""
        self.assert_compile(
            Unicode(100, collation="public.case_insensitive"),
            "VARCHAR(100) COLLATE public.case_insensitive",
        )

    def test_array_with_schema_qualified_collation(self):
        """ARRAY with schema-qualified collation on element type."""
        self.assert_compile(
            postgresql.ARRAY(Unicode(30, collation="my_schema.my_collation")),
            "VARCHAR(30)[] COLLATE my_schema.my_collation",
        )

    def test_array_multidim_with_schema_qualified_collation(self):
        """Multi-dimensional ARRAY with schema-qualified collation."""
        self.assert_compile(
            postgresql.ARRAY(Text(collation="custom.text_ops"), dimensions=2),
            "TEXT[][] COLLATE custom.text_ops",
        )

    def test_pg_catalog_collation(self):
        """pg_catalog.default collation quotes reserved word 'default'."""
        self.assert_compile(
            Text(collation="pg_catalog.default"),
            'TEXT COLLATE pg_catalog."default"',
        )

    def test_public_schema_collation(self):
        """Collation in public schema renders without full quoting."""
        self.assert_compile(
            String(50, collation="public.nocase"),
            "VARCHAR(50) COLLATE public.nocase",
        )

    def test_simple_collation_with_underscore(self):
        """Simple collation with underscores is still quoted."""
        self.assert_compile(
            Text(collation="en_US_utf8"), 'TEXT COLLATE "en_US_utf8"'
        )

    def test_simple_collation_case_sensitive(self):
        """Simple collation with mixed case is quoted."""
        self.assert_compile(
            String(50, collation="German_phonebook"),
            'VARCHAR(50) COLLATE "German_phonebook"',
        )

    def test_array_simple_collation_is_quoted(self):
        """ARRAY with simple collation is quoted correctly."""
        self.assert_compile(
            postgresql.ARRAY(Unicode(30, collation="en_US")),
            'VARCHAR(30)[] COLLATE "en_US"',
        )

    def test_text_no_collation(self):
        """Text type without collation renders without COLLATE clause."""
        self.assert_compile(Text(), "TEXT")

    def test_string_with_length_no_collation(self):
        """String type with length but no collation."""
        self.assert_compile(String(100), "VARCHAR(100)")

    @testing.combinations(
        ("psycopg", "postgresql+psycopg"),
        ("psycopg2", "postgresql+psycopg2"),
        ("asyncpg", "postgresql+asyncpg"),
        ("pg8000", "postgresql+pg8000"),
        argnames="driver_name, dialect_str",
    )
    def test_schema_qualified_collation_across_drivers(
        self, driver_name, dialect_str
    ):
        """Schema-qualified collation works across all PostgreSQL drivers."""
        self.assert_compile(
            Text(collation="myschema.mycollation"),
            "TEXT COLLATE myschema.mycollation",
            dialect=dialect_str,
        )

    @testing.combinations(
        ("psycopg", "postgresql+psycopg"),
        ("psycopg2", "postgresql+psycopg2"),
        ("asyncpg", "postgresql+asyncpg"),
        ("pg8000", "postgresql+pg8000"),
        argnames="driver_name, dialect_str",
    )
    def test_simple_collation_across_drivers(self, driver_name, dialect_str):
        """Simple collation works across all PostgreSQL drivers."""
        self.assert_compile(
            Text(collation="POSIX"),
            'TEXT COLLATE "POSIX"',
            dialect=dialect_str,
        )

    def test_schema_qualified_three_parts_treated_as_single(self):
        """Collation with multiple dots splits on the first dot only."""
        self.assert_compile(
            Text(collation="a.b.c"),
            'TEXT COLLATE a."b.c"',
        )

    def test_schema_qualified_collation_injection_is_escaped(self):
        """Schema-qualified collation with injection attempt is quoted."""
        self.assert_compile(
            Text(collation='public.utf8"; DROP TABLE users; --'),
            'TEXT COLLATE public."utf8""; DROP TABLE users; --"',
        )
