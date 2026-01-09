import re

import pyodbc  # pip install pyodbc

from database_wrapper import ColumnMetaIntrospector, DBIntrospector

from .type_mapping import map_db_type  # your existing mapper


class MSSQLIntrospector(DBIntrospector):
    conn: pyodbc.Connection

    def map_db_type(self, db_type: str):
        return map_db_type(db_type)

    def get_table_columns(self, schema: str, table: str) -> list[ColumnMetaIntrospector]:
        """
        Returns ColumnMetaIntrospector for SQL Server:
        - col_name
        - db_type (sys.types.name; e.g., int, bigint, nvarchar, datetime2, bit, numeric, etc.)
        - is_nullable
        - has_default + default_expr (sys.default_constraints.definition)
        - enum_labels (best-effort from CHECK ... IN ('a','b',...))
        """
        # Main column metadata
        q = """
        SELECT
            c.name                                  AS col_name,
            t.name                                  AS typname,
            c.is_nullable                           AS is_nullable,
            dc.definition                           AS default_expr,
            c.column_id                             AS column_id,
            c.max_length                            AS max_length,
            c.precision                             AS precision,
            c.scale                                 AS scale
        FROM sys.columns c
        JOIN sys.tables tb      ON tb.object_id   = c.object_id
        JOIN sys.schemas s      ON s.schema_id    = tb.schema_id
        JOIN sys.types t        ON t.user_type_id = c.user_type_id
        LEFT JOIN sys.default_constraints dc
               ON dc.parent_object_id = c.object_id
              AND dc.parent_column_id = c.column_id
        WHERE s.name = %s AND tb.name = %s
        ORDER BY c.column_id;
        """

        # Enum-like labels via CHECK constraints (best-effort)
        # We collect constraint definitions per column and later parse IN ('a','b',...)
        q_checks = """
        SELECT
            c.name            AS col_name,
            cc.definition     AS definition
        FROM sys.check_constraints cc
        JOIN sys.tables tb   ON tb.object_id   = cc.parent_object_id
        JOIN sys.schemas s   ON s.schema_id    = tb.schema_id
        JOIN sys.columns c   ON c.object_id    = cc.parent_object_id
        WHERE s.name = %s AND tb.name = %s
          AND cc.definition LIKE '% IN (%'
        """

        with self.conn.cursor() as cur:
            cur.execute(q, (schema, table))
            col_rows = cur.fetchall()

            cur.execute(q_checks, (schema, table))
            check_rows = cur.fetchall()

        # Build enum-like labels per column by parsing CHECK defs that reference that column
        # Example def: ([Status] IN ('New','Closed','On Hold'))
        col_to_enum_labels: dict[str, list[str]] = {}
        in_clause_re = re.compile(r"\bIN\s*\((.*?)\)", re.IGNORECASE | re.DOTALL)
        quoted_re = re.compile(r"'((?:''|[^'])*)'")

        for r in check_rows:
            col_name = r["col_name"]
            definition = r["definition"] or ""
            # Heuristic: ensure constraint references the column (with or without brackets)
            if f"[{col_name}]" not in definition and col_name not in definition:
                continue
            m = in_clause_re.search(definition)
            if not m:
                continue
            inner = m.group(1)
            labels = [q.replace("''", "'") for q in quoted_re.findall(inner)]
            if labels:
                # keep unique, stable
                seen = set()
                uniq = [x for x in labels if not (x in seen or seen.add(x))]
                col_to_enum_labels[col_name] = uniq

        out: list[ColumnMetaIntrospector] = []
        for row in col_rows:
            col_name = row["col_name"]
            typname = row["typname"]  # short type token
            is_nullable = bool(row["is_nullable"])
            default_expr = row["default_expr"]
            enum_labels = col_to_enum_labels.get(col_name)

            out.append(
                ColumnMetaIntrospector(
                    col_name=col_name,
                    db_type=typname,
                    is_nullable=is_nullable,
                    has_default=(default_expr is not None),
                    default_expr=default_expr,
                    enum_labels=enum_labels,
                )
            )

        return out
