"""test the inspection registry system."""

from sqlalchemy import exc, inspect, inspection
from sqlalchemy.testing import assert_raises_message, eq_, fixtures, is_true


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


class TestInspectionReregistration(fixtures.TestBase):
    def teardown_test(self):
        for type_ in list(inspection._registrars):
            if issubclass(type_, TestFixture):
                del inspection._registrars[type_]

    def test_inspects_same_function_idempotent(self):
        """Registering the identical function object twice does not raise."""

        class FooA(TestFixture):
            pass

        @inspection._inspects(FooA)
        def insp_foo_a(subject):
            return {"val": subject}

        inspection._inspects(FooA)(insp_foo_a)

        obj = FooA()
        eq_(inspect(obj)["val"], obj)

    def test_inspects_equivalent_function_on_reload(self):
        """Two distinct function objects sharing __name__ and __module__
        can register for the same type without error."""

        class FooB(TestFixture):
            pass

        def insp_handler(subject):
            return 1

        first_fn = insp_handler
        inspection._inspects(FooB)(first_fn)

        def insp_handler(subject):
            return 2

        second_fn = insp_handler

        is_true(first_fn is not second_fn)
        eq_(first_fn.__name__, second_fn.__name__)
        eq_(first_fn.__module__, second_fn.__module__)

        inspection._inspects(FooB)(second_fn)

    def test_self_inspects_idempotent(self):
        """Calling _self_inspects on the same class twice does not raise."""

        class FooC(TestFixture):
            pass

        inspection._self_inspects(FooC)
        inspection._self_inspects(FooC)

        obj = FooC()
        eq_(inspect(obj), obj)

    def test_inspects_class_inspector_idempotent(self):
        """Re-registering the same class-based inspector does not raise."""

        class FooD(TestFixture):
            pass

        class FooDInspect:
            def __init__(self, target):
                self.target = target

        inspection._inspects(FooD)(FooDInspect)
        inspection._inspects(FooD)(FooDInspect)

        obj = FooD()
        insp = inspect(obj)
        assert isinstance(insp, FooDInspect)
        eq_(insp.target, obj)

    def test_inspects_multiple_types_idempotent(self):
        """Re-registering the same handler for multiple types at once
        does not raise."""

        class FooE(TestFixture):
            pass

        class BarE(TestFixture):
            pass

        @inspection._inspects(FooE, BarE)
        def insp_multi(subject):
            return {"multi": subject}

        inspection._inspects(FooE, BarE)(insp_multi)

        foo = FooE()
        bar = BarE()
        eq_(inspect(foo)["multi"], foo)
        eq_(inspect(bar)["multi"], bar)

    def test_inspect_functional_after_function_reregistration(self):
        """inspect() returns correct results after idempotent re-registration
        of a function-based inspector."""

        class FooF(TestFixture):
            pass

        def handler(subject):
            return {"result": subject}

        first_handler = handler
        inspection._inspects(FooF)(first_handler)

        def handler(subject):
            return {"result": subject}

        second_handler = handler
        inspection._inspects(FooF)(second_handler)

        obj = FooF()
        result = inspect(obj)
        eq_(result["result"], obj)

    def test_self_inspects_returns_subject_after_reregistration(self):
        """inspect() returns the subject itself after idempotent
        _self_inspects re-registration."""

        class FooG(TestFixture):
            pass

        inspection._self_inspects(FooG)
        inspection._self_inspects(FooG)

        obj = FooG()
        eq_(inspect(obj), obj)

    def test_inspects_partial_type_overlap_reregistration(self):
        """Re-registering a subset of previously registered types with the
        same handler does not raise."""

        class FooH(TestFixture):
            pass

        class BarH(TestFixture):
            pass

        @inspection._inspects(FooH, BarH)
        def insp_partial(subject):
            return {"partial": subject}

        inspection._inspects(FooH)(insp_partial)

        foo = FooH()
        bar = BarH()
        eq_(inspect(foo)["partial"], foo)
        eq_(inspect(bar)["partial"], bar)

    def test_inspects_hierarchy_with_reregistration(self):
        """Re-registration is idempotent even when types form an
        inheritance hierarchy."""

        class BaseFooI(TestFixture):
            pass

        class SubFooI(BaseFooI):
            pass

        @inspection._inspects(BaseFooI)
        def insp_base(subject):
            return "base"

        @inspection._inspects(SubFooI)
        def insp_sub(subject):
            return "sub"

        inspection._inspects(BaseFooI)(insp_base)
        inspection._inspects(SubFooI)(insp_sub)

        eq_(inspect(BaseFooI()), "base")
        eq_(inspect(SubFooI()), "sub")

    def test_inspects_different_callable_raises(self):
        """Registering a genuinely different callable for an already-registered
        type raises AssertionError."""

        class FooJ(TestFixture):
            pass

        @inspection._inspects(FooJ)
        def insp_first(subject):
            return 1

        def insp_second(subject):
            return 2

        assert_raises_message(
            AssertionError,
            "is already registered",
            inspection._inspects(FooJ),
            insp_second,
        )

    def test_self_inspects_after_function_inspects_raises(self):
        """_self_inspects on a type already registered via _inspects
        raises AssertionError."""

        class FooK(TestFixture):
            pass

        @inspection._inspects(FooK)
        def insp_foo_k(subject):
            return 1

        assert_raises_message(
            AssertionError,
            "is already registered",
            inspection._self_inspects,
            FooK,
        )

    def test_function_inspects_after_self_inspects_raises(self):
        """_inspects on a type already registered via _self_inspects
        raises AssertionError."""

        class FooL(TestFixture):
            pass

        inspection._self_inspects(FooL)

        def insp_foo_l(subject):
            return 1

        assert_raises_message(
            AssertionError,
            "is already registered",
            inspection._inspects(FooL),
            insp_foo_l,
        )
