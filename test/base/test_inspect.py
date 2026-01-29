"""test the inspection registry system."""

import importlib

from sqlalchemy import exc, inspect, inspection
from sqlalchemy.testing import assert_raises_message, eq_, fixtures, is_none


class TestFixture:
    pass


class TestInspection(fixtures.TestBase):
    def teardown_test(self):
        for type_ in list(inspection._registrars):
            if issubclass(type_, TestFixture):
                del inspection._registrars[type_]

    def test_def_insp(self):
        class SomeFoo(TestFixture):
            pass

        @inspection._inspects(SomeFoo)
        def insp_somefoo(subject):
            return {"insp": subject}

        somefoo = SomeFoo()
        insp = inspect(somefoo)
        assert insp["insp"] is somefoo

    def test_no_inspect(self):
        class SomeFoo(TestFixture):
            pass

        assert_raises_message(
            exc.NoInspectionAvailable,
            "No inspection system is available for object of type ",
            inspect,
            SomeFoo,
        )

    def test_class_insp(self):
        class SomeFoo(TestFixture):
            pass

        class SomeFooInspect:
            def __init__(self, target):
                self.target = target

        SomeFooInspect = inspection._inspects(SomeFoo)(SomeFooInspect)

        somefoo = SomeFoo()
        insp = inspect(somefoo)
        assert isinstance(insp, SomeFooInspect)
        assert insp.target is somefoo

    def test_hierarchy_insp(self):
        class SomeFoo(TestFixture):
            pass

        class SomeSubFoo(SomeFoo):
            pass

        @inspection._inspects(SomeFoo)
        def insp_somefoo(subject):
            return 1

        @inspection._inspects(SomeSubFoo)
        def insp_somesubfoo(subject):
            return 2

        SomeFoo()
        eq_(inspect(SomeFoo()), 1)
        eq_(inspect(SomeSubFoo()), 2)


class TestInspectionModuleReload(fixtures.TestBase):
    def test_reload_orm_base(self):
        """Reloading orm.base does not raise."""
        from sqlalchemy.orm import base

        importlib.reload(base)

    def test_reload_engine_reflection(self):
        """Reloading engine.reflection does not raise."""
        from sqlalchemy.engine import reflection

        importlib.reload(reflection)

    def test_reload_orm_util(self):
        """Reloading orm.util does not raise."""
        from sqlalchemy.orm import util as orm_util

        importlib.reload(orm_util)

    def test_reload_orm_base_multiple_times(self):
        """Three successive reloads of orm.base remain safe."""
        from sqlalchemy.orm import base

        importlib.reload(base)
        importlib.reload(base)
        importlib.reload(base)

    def test_reload_multiple_modules_sequentially(self):
        """Reloading several modules in sequence does not raise."""
        from sqlalchemy.engine import reflection
        from sqlalchemy.orm import base

        importlib.reload(base)
        importlib.reload(reflection)

    def test_inspect_unmapped_instance_after_reload(self):
        """inspect() returns None for unmapped objects after module
        reload."""
        from sqlalchemy.orm import base

        importlib.reload(base)
        result = inspect(object(), raiseerr=False)
        is_none(result)

    def test_inspect_table_after_reload(self):
        """inspect() on a Table still returns the table itself after
        module reload."""
        from sqlalchemy import Column, Integer, MetaData, Table
        from sqlalchemy.orm import base

        metadata = MetaData()
        t = Table("t_reload", metadata, Column("id", Integer, primary_key=True))

        importlib.reload(base)

        result = inspect(t)
        eq_(result, t)

    def test_inspect_clause_element_after_reload(self):
        """inspect() on a ClauseElement is unaffected by module reload."""
        from sqlalchemy import literal_column
        from sqlalchemy.orm import base

        expr = literal_column("1")

        importlib.reload(base)

        result = inspect(expr)
        eq_(result, expr)

    def test_no_inspection_available_after_reload(self):
        """NoInspectionAvailable is still raised for non-inspectable
        subjects after module reload."""
        from sqlalchemy.orm import base

        importlib.reload(base)

        assert_raises_message(
            exc.NoInspectionAvailable,
            "No inspection system is available for object of type",
            inspect,
            42,
        )
