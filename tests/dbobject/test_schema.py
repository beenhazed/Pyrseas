# -*- coding: utf-8 -*-
"""Test schemas"""

import unittest

from pyrseas.testutils import PyrseasTestCase, fix_indent

CREATE_STMT = "CREATE SCHEMA s1"
COMMENT_STMT = "COMMENT ON SCHEMA s1 IS 'Test schema s1'"


class SchemaToMapTestCase(PyrseasTestCase):
    """Test mapping of created schemas"""

    def test_map_schema(self):
        "Map a created schema"
        dbmap = self.db.execute_and_map(CREATE_STMT)
        self.assertEqual(dbmap['schema s1'], {})

    def test_map_table_within_schema(self):
        "Map a schema and a table within it"
        self.db.execute(CREATE_STMT)
        ddlstmt = "CREATE TABLE s1.t1 (c1 INTEGER, c2 TEXT)"
        expmap = {'table t1': {
                'columns': [{'c1': {'type': 'integer'}},
                            {'c2': {'type': 'text'}}]}}
        dbmap = self.db.execute_and_map(ddlstmt)
        self.assertEqual(dbmap['schema s1'], expmap)

    def test_map_schema_comment(self):
        "Map a schema comment"
        self.db.execute(CREATE_STMT)
        dbmap = self.db.execute_and_map(COMMENT_STMT)
        self.assertEqual(dbmap['schema s1'], {'description': 'Test schema s1'})

    def test_map_select_schema(self):
        "Map a single schema when three schemas exist"
        self.db.execute(CREATE_STMT)
        self.db.execute("CREATE SCHEMA s2")
        dbmap = self.db.execute_and_map("CREATE SCHEMA s3", ['s2'])
        self.assertEqual(dbmap['schema s2'], {})


class SchemaToSqlTestCase(PyrseasTestCase):
    """Test SQL generation from input schemas"""

    _schmap = {'schema s1': {'description': 'Test schema s1'}}

    def test_create_schema(self):
        "Create a schema that didn't exist"
        inmap = {'schema s1': {}}
        dbsql = self.db.process_map(inmap)
        self.assertEqual(dbsql, [CREATE_STMT])

    def test_bad_schema_map(self):
        "Error creating a schema with a bad map"
        inmap = {'s1': {}}
        self.assertRaises(KeyError, self.db.process_map, inmap)

    def test_drop_schema(self):
        "Drop an existing schema"
        self.db.execute_commit(CREATE_STMT)
        dbsql = self.db.process_map({})
        self.assertEqual(dbsql, ["DROP SCHEMA s1"])

    def test_rename_schema(self):
        "Rename an existing schema"
        self.db.execute_commit(CREATE_STMT)
        inmap = {'schema s2': {'oldname': 's1'}}
        dbsql = self.db.process_map(inmap)
        self.assertEqual(dbsql, ["ALTER SCHEMA s1 RENAME TO s2"])

    def test_bad_rename_schema(self):
        "Error renaming a non-existing schema"
        self.db.execute_commit(CREATE_STMT)
        inmap = {'schema s2': {'oldname': 's3'}}
        self.assertRaises(KeyError, self.db.process_map, inmap)

    def test_schema_with_comment(self):
        "Create a schema with a comment"
        dbsql = self.db.process_map(self._schmap)
        self.assertEqual(dbsql, [CREATE_STMT, COMMENT_STMT])

    def test_comment_on_schema(self):
        "Create a comment for an existing schema"
        self.db.execute_commit(CREATE_STMT)
        dbsql = self.db.process_map(self._schmap)
        self.assertEqual(dbsql, [COMMENT_STMT])

    def test_drop_schema_comment(self):
        "Drop a comment on an existing schema"
        self.db.execute(CREATE_STMT)
        self.db.execute_commit(COMMENT_STMT)
        dbsql = self.db.process_map({'schema s1': {}})
        self.assertEqual(dbsql, ["COMMENT ON SCHEMA s1 IS NULL"])

    def test_change_schema_comment(self):
        "Change existing comment on a schema"
        self.db.execute(CREATE_STMT)
        self.db.execute_commit(COMMENT_STMT)
        inmap = {'schema s1': {'description': 'Changed schema s1'}}
        dbsql = self.db.process_map(inmap)
        self.assertEqual(dbsql, [
                "COMMENT ON SCHEMA s1 IS 'Changed schema s1'"])


def suite():
    tests = unittest.TestLoader().loadTestsFromTestCase(SchemaToMapTestCase)
    tests.addTest(unittest.TestLoader().loadTestsFromTestCase(
            SchemaToSqlTestCase))
    return tests

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
