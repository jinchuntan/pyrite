"""The repair plans SQLite's ADD COLUMN restrictions before issuing DDL."""

import sqlite3

import pytest
from sqlalchemy import Column, Computed, Integer, MetaData, String, Table, text

from pyrite.exceptions import IndexSchemaRefusedError
from pyrite.storage.schema_repair import REBUILD_SUGGESTION, repair_schema


@pytest.mark.parametrize(
    "default",
    ["CURRENT_TIMESTAMP", "CURRENT_DATE", "CURRENT_TIME", "(1 + 2)", "stored"],
)
@pytest.mark.parametrize(
    "populated",
    [
        pytest.param(False, marks=pytest.mark.control(reason="empty-table repairs already worked")),
        True,
    ],
)
def test_non_constant_default_requires_an_empty_table(default, populated):
    metadata = MetaData()
    extra = (
        Column("stamp", Integer, Computed("id + 1", persisted=True))
        if default == "stored"
        else Column("stamp", String, server_default=text(default))
    )
    Table("demo", metadata, Column("id", Integer), Column("safe", String), extra)
    with sqlite3.connect(":memory:") as conn:
        conn.execute("CREATE TABLE demo (id INTEGER)")
        if populated:
            conn.execute("INSERT INTO demo VALUES (1)")
        conn.commit()
        before = conn.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall()
        if populated:
            with pytest.raises(IndexSchemaRefusedError, match="demo.stamp") as info:
                repair_schema(conn, metadata)
            assert info.value.suggestion == REBUILD_SUGGESTION
            assert conn.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall() == before
            assert conn.execute("SELECT * FROM demo").fetchall() == [(1,)]
        else:
            assert repair_schema(conn, metadata) == ["demo.safe", "demo.stamp"]
            assert repair_schema(conn, metadata) == []


@pytest.mark.control(reason="constant defaults remain addable on populated tables")
@pytest.mark.parametrize("default", ["'active'", "'CURRENT_TIMESTAMP'", "7", "NULL"])
def test_constant_defaults_are_added_on_populated_tables(default):
    metadata = MetaData()
    Table(
        "demo",
        metadata,
        Column("id", Integer),
        Column("value", String, server_default=text(default)),
    )
    with sqlite3.connect(":memory:") as conn:
        conn.execute("CREATE TABLE demo (id INTEGER)")
        conn.execute("INSERT INTO demo VALUES (1)")
        conn.commit()
        assert repair_schema(conn, metadata) == ["demo.value"]
        assert [row[1] for row in conn.execute("PRAGMA table_info(demo)")] == ["id", "value"]
