import re
from contextlib import contextmanager
from decimal import Decimal
from unittest.mock import call, patch

import pytest

from tests.data import data_transformers as dt, sample_transformers as st
from transformers.exceptions import ContentValidationError
from transformers.impl.transformers_impl import apply_defaults_non_recursively
from transformers.transformers import JSONAPIListTransformer, JSONAPITransformer


@contextmanager
def should_raise(expected_exception, **kwargs):
    """
    Context manager to allow for conditional expectation of exceptions.

    If `expected_exception` is given, test will fail if the exception is not thrown.
    If `expected_exception` is None, test will fail if any exception is raised, as normal.

    Usage:
        with should_raise(AttributeError):
            this_function_is_supposed_to_raise_an_attribute_error()
        with should_raise(None):
            this_function_should_not_raise_an_error()

    Args:
        expected_exception: Exception subclass to look for, or None to not expect one.
        **kwargs: passed through to pytest.raises

    Yields:
        Pytest ExceptionInfo instance or None.
    """
    if expected_exception is None:
        yield None
    else:
        with pytest.raises(expected_exception, **kwargs) as exception_info:
            yield exception_info


class TestJSONAPITransformer:
    @pytest.mark.parametrize(
        ("transformer", "expected_jsonapi_blob"),
        (
            # The following are all from the above from_jsonapi tests
            (dt.BASIC_JSONAPI_TRANSFORMER, dt.BASIC_JSONAPI),
            (dt.JSONAPI_ID_MATCHING_TRANSFORMER, dt.JSONAPI_ID_MATCHING),
            (dt.JSONAPI_INCLUDE_RELATIONSHIP_TRANSFORMER, dt.JSONAPI_INCLUDE_RELATIONSHIP),
            (dt.JSONAPI_ID_LID_TRANSFORMER, dt.JSONAPI_ID_LID),
            (dt.JSONAPI_LIST_TRANSFORMER, dt.JSONAPI_LIST),
            (dt.JSONAPI_SIMPLE_RECURSIVE_TRANSFORMER, dt.JSONAPI_SIMPLE_RECURSIVE),
            (dt.JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER, dt.JSONAPI_COMPLEX_RECURSIVE),
            (dt.JSONAPI_RECURSIVE_TRANSFORMER, dt.JSONAPI_RECURSIVE),
            # The following are just for this test (not used in from_jsonapi tests)
            (dt.TO_JSONAPI_COMPLEX_TRANSFORMER, dt.TO_JSONAPI_COMPLEX_TRANSFORMER_EXP_JSONAPI),
        ),
    )
    def test_all_to_jsonapi_data(self, transformer, expected_jsonapi_blob):
        actual = transformer.to_jsonapi()
        # To verify `==` is symmetric test equality in both directions
        assert expected_jsonapi_blob == actual
        assert actual == expected_jsonapi_blob

    @pytest.mark.parametrize(
        ("type_name", "expected_error"), (("customer", None), ("foo", ValueError), (None, None))
    )
    def test_cannot_change_type_name_on_init(self, type_name, expected_error):
        """
        type_name must not be able to be changed on init if class has non-None type_name attribute.
        """
        with should_raise(expected_error):
            transformer = st.CustomerTransformer(type_name=type_name)
            assert transformer.type_name == st.CustomerTransformer.type_name

    @pytest.mark.parametrize(
        ("type_name", "expected_error"), (("customer", None), (None, ValueError))
    )
    def test_must_set_type_name_on_init_or_as_attribute(self, type_name, expected_error):
        """type_name must be set on init if it is not set as a class attribute."""
        with should_raise(expected_error):
            transformer = JSONAPITransformer(type_name=type_name)
            assert transformer.type_name == type_name

    def test_apply_defaults_applies_recursively(self):
        """
        Defaults must be applied recursively by `apply_defaults`, not on init.

        Defaults are applied to self and all relationships, their relationships, etc. If a default
        relationship itself has defaults, those are applied as well.
        """

        class ParentTransformer(JSONAPITransformer):
            type_name = "parent"

            def get_defaults_for_optional_attributes(self):
                return {"i-am-a": "parent"}

            def get_defaults_for_optional_relationships(self):
                return {"default-child": ChildTransformer()}

        class ChildTransformer(JSONAPITransformer):
            type_name = "child"

            def get_defaults_for_optional_attributes(self):
                return {"i-am-a": "child"}

            def get_defaults_for_optional_relationships(self):
                return {"grandchild": GrandchildTransformer()}

        class GrandchildTransformer(JSONAPITransformer):
            type_name = "grandchild"

            def get_defaults_for_optional_attributes(self):
                return {"i-am-a": "grandchild"}

            def get_defaults_for_optional_relationships(self):
                return {"some-relationship": []}

        parent = ParentTransformer(
            attributes={"foo": "bar"}, relationships={"baz": [], "other-child": ChildTransformer()}
        )

        # Confirm defaults not applied on init
        assert parent.attributes == {"foo": "bar"}
        assert parent.relationships == {"baz": [], "other-child": ChildTransformer()}

        parent.apply_defaults()

        assert parent.attributes == {"foo": "bar", "i-am-a": "parent"}
        assert set(parent.relationships.keys()) == {"baz", "default-child", "other-child"}
        assert parent.relationships["baz"] == []

        for child in parent.relationships["default-child"], parent.relationships["other-child"]:
            assert child.type_name == "child"
            assert child.attributes == {"i-am-a": "child"}
            assert set(child.relationships.keys()) == {"grandchild"}

            grandchild = child.relationships["grandchild"]
            assert grandchild.type_name == "grandchild"
            assert grandchild.attributes == {"i-am-a": "grandchild"}
            assert grandchild.relationships == {"some-relationship": []}

    def test_apply_defaults_does_not_loop(self):
        """
        Defaults must be applied recursively by `apply_defaults`, but must handle circular
        references, whether previously existing or applied in defaults, by exiting.

        Defaults must only be applied once, and obviously there must be no infinite recursion.
        """

        class Transformer(JSONAPITransformer):
            type_name = "parent"

            def get_defaults_for_optional_relationships(self):
                return {"default_self": self}

        transformer = Transformer()
        transformer.relationships["already_existing_self"] = transformer

        # Confirm defaults not applied on init
        assert transformer.relationships == {"already_existing_self": transformer}

        with patch(
            "transformers.impl.transformers_impl.apply_defaults_non_recursively",
        ) as transformer_apply_defaults:
            transformer_apply_defaults.side_effect = apply_defaults_non_recursively

            transformer.apply_defaults()

        # There's one parent transformer and a reference to that same transformer in the
        # relationships, ie, there is only one unique transformer. The mocked function should
        # only be called *per unique* transformer!
        assert transformer_apply_defaults.call_args_list == [call(transformer)]
        assert transformer.relationships == {
            "already_existing_self": transformer,
            "default_self": transformer,
        }

    @pytest.mark.parametrize("value", (None, "string", "", 1, 3.14, Decimal("100")))
    def test_eq_to_non_jsonapi_transformer(self, value):
        """
        A JSONAPITransformer is never equal to a non-JSONAPITransformer, including None.

        While you generally aren't doing == None, it can happen when comparing to an unknown
        variable and it definitely shouldn't crash.

        Args:
            value: Value to test against.
        """
        result = JSONAPITransformer(type_name="foo")
        # To verify `!=` is symmetric test equality in both directions
        assert result != value
        assert value != result

    @pytest.mark.parametrize("value", (None, "string", "", 1, 3.14, Decimal("100")))
    def test_eq_when_relationships_contains_non_jsonapi_transformer(self, value):
        class MyTransformer(JSONAPITransformer):
            type_name = "hello"

        foo = MyTransformer(relationships={"hello": MyTransformer()})
        bar = MyTransformer(relationships={"hello": value})
        # To verify `!=` is symmetric test equality in both directions
        assert foo != bar
        assert bar != foo

    @pytest.mark.parametrize("value", (None, "string", "", 1, 3.14, Decimal("100")))
    def test_eq_when_relationships_contains_list_with_non_matching_relationship(self, value):
        class MyTransformer(JSONAPITransformer):
            type_name = "hello"

        class Coverage(JSONAPITransformer):
            type_name = "coverage"

        class InsuredRisk(JSONAPITransformer):
            type_name = "insured_risk"

        foo = MyTransformer(
            relationships={"coverages": [Coverage(relationships={"insured_risk": InsuredRisk()})]}
        )
        bar = MyTransformer(
            relationships={"coverages": [Coverage(relationships={"insured_risk": value})]}
        )
        # To verify `!=` is symmetric test equality in both directions
        assert foo != bar
        assert bar != foo

    @pytest.mark.parametrize("value", (None, "string", "", 1, 3.14, Decimal("100")))
    def test_eq_when_relationships_contains_list_compared_with_non_list(self, value):
        class MyTransformer(JSONAPITransformer):
            type_name = "hello"

        foo = MyTransformer(relationships={"coverages": []})
        bar = MyTransformer(relationships={"coverages": value})
        # To verify `!=` is symmetric test equality in both directions
        assert foo != bar
        assert bar != foo


class TestJSONAPIListTransformer:
    @pytest.mark.parametrize(
        ("transformer_list", "expected_jsonapi_blob"),
        (
            (dt.JSONAPI_TOP_LIST_TRANSFORMERS, dt.JSONAPI_TOP_LIST_CORRECTED),
            (dt.JSONAPI_RECURSIVE_LIST_TRANSFORMERS, dt.JSONAPI_RECURSIVE_LIST),
            (
                dt.JSONAPI_TOP_LIST_WITH_INCLUDES_TRANSFORMERS,
                dt.JSONAPI_TOP_LIST_WITH_INCLUDES_CLEAN,
            ),
            # Lets just make sure it works with tuples of Transformers too
            (tuple(dt.JSONAPI_TOP_LIST_TRANSFORMERS), dt.JSONAPI_TOP_LIST_CORRECTED),
        ),
    )
    def test_all_list_to_jsonapi_data(self, transformer_list, expected_jsonapi_blob):
        actual = JSONAPIListTransformer(transformer_list).to_jsonapi()
        # To verify `==` is symmetric test equality in both directions
        assert expected_jsonapi_blob == actual
        assert actual == expected_jsonapi_blob

    @pytest.mark.parametrize(
        ("input_value", "exp_error"),
        (
            (1, "'int' object is not iterable"),
            (JSONAPITransformer, "'type' object is not iterable"),
        ),
    )
    def test_to_jsonapi_requires_iterable(self, input_value, exp_error):
        """TestJSONAPIListTransformer only works on lists of transformers."""
        with should_raise(TypeError, match=exp_error):
            JSONAPIListTransformer(input_value).to_jsonapi()


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (None, None),
        ("16", "16"),
        (16, "16"),
        ("2da7f1d8-4f92-40a4-823f-a6a7c33d76ca", "2da7f1d8-4f92-40a4-823f-a6a7c33d76ca"),
    ),
)
def test_jsonapi_spec_requires_id_is_string(value, expected):
    transformer = JSONAPITransformer(type_name="quote", id=value, lid="my_lid")
    data = transformer.to_jsonapi()["data"]
    if expected is None:
        assert "id" not in data
    else:
        assert data["id"] == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (None, None),
        ("16", "16"),
        (16, "16"),
        ("2da7f1d8-4f92-40a4-823f-a6a7c33d76ca", "2da7f1d8-4f92-40a4-823f-a6a7c33d76ca"),
    ),
)
def test_jsonapi_spec_requires_lid_is_string(value, expected):
    transformer = JSONAPITransformer(type_name="quote", id="my_id", lid=value)
    data = transformer.to_jsonapi()["data"]
    if expected is None:
        assert "lid" not in data
    else:
        assert data["lid"] == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (None, None),
        ("16", "16"),
        (16, "16"),
        ("2da7f1d8-4f92-40a4-823f-a6a7c33d76ca", "2da7f1d8-4f92-40a4-823f-a6a7c33d76ca"),
    ),
)
def test_jsonapi_spec_requires_id_is_string_in_relationships(value, expected):
    transformer = JSONAPITransformer(
        type_name="quote",
        id="my_id",
        relationships={
            "related_item": JSONAPITransformer(type_name="my_related", id=value, lid="my_lid")
        },
    )
    related_data = transformer.to_jsonapi()["data"]["relationships"]["related_item"]["data"]
    included = transformer.to_jsonapi()["included"][0]
    if expected is None:
        assert "id" not in related_data
        assert "id" not in included
    else:
        assert related_data["id"] == expected
        assert included["id"] == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (None, None),
        ("16", "16"),
        (16, "16"),
        ("2da7f1d8-4f92-40a4-823f-a6a7c33d76ca", "2da7f1d8-4f92-40a4-823f-a6a7c33d76ca"),
    ),
)
def test_jsonapi_spec_requires_lid_is_string_in_relationships(value, expected):
    transformer = JSONAPITransformer(
        type_name="quote",
        id="my_id",
        relationships={
            "related_item": JSONAPITransformer(
                type_name="my_related", id="my_id", lid=value, attributes={"hello": "world"}
            )
        },
    )
    related_data = transformer.to_jsonapi()["data"]["relationships"]["related_item"]["data"]
    included = transformer.to_jsonapi()["included"][0]
    if expected is None:
        assert "lid" not in related_data
        assert "lid" not in included
    else:
        assert "lid" not in related_data
        assert included["lid"] == expected


def test_jsonapi_spec_requires_attribute_and_relationship_keys_must_be_unique():
    transformer = JSONAPITransformer(
        type_name="quote",
        id="my_id",
        attributes={
            "hello": "world",
            "goodbye": "friend",
            "greetings": "earthling",
        },
        relationships={
            "hello": JSONAPITransformer(type_name="my_hello_related", id="my_hello_id"),
            "goodbye": JSONAPITransformer(type_name="my_goodbye_related", id="my_goodbye_id"),
            "nothing": JSONAPITransformer(type_name="my_nothing_related", id="my_nothing_id"),
        },
    )

    with should_raise(
        ContentValidationError,
        match=re.escape("Key `hello` must not be in both attributes and relationships."),
    ):
        _ = transformer["hello"]

    with should_raise(
        ContentValidationError,
        match=re.escape("Cannot add `nothing` to attributes, it is already a relationship."),
    ):
        transformer["nothing"] = "assigning to an attribute"

    with should_raise(
        ContentValidationError,
        match=re.escape(
            "Key names cannot be common to both `attributes` and `relationships`: "
            "['goodbye', 'hello']"
        ),
    ):
        transformer.to_jsonapi()


def test_jsonapi_spec_requires_type_name_to_be_string():
    error_msg = "`type_name` must be a string."

    with should_raise(ContentValidationError, match=re.escape(error_msg)):
        _ = JSONAPITransformer(type_name=["my_type_name"])

    transformer = JSONAPITransformer(type_name="quote")
    transformer.type_name = ["my_type_name"]

    with should_raise(ContentValidationError, match=re.escape(error_msg)):
        transformer.to_jsonapi()
