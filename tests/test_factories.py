import re
from copy import deepcopy

import pytest

from tests.data import data_transformers as dt, sample_transformers as st
from transformers.exceptions import ContentValidationError
from transformers.factories import JSONAPITransformerFactory, from_jsonapi_generic
from transformers.impl import factories_impl, transformers_impl
from transformers.transformers import JSONAPIListTransformer, JSONAPITransformer


class TestJSONAPITransformerFactory:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.transformer_factory = JSONAPITransformerFactory(
            transformer_classes=[
                st.CustomerTransformer,
                st.ProductTransformer,
                st.QuoteTransformer,
                st.AgentTransformer,
                st.AgencyTransformer,
                st.DocumentTransformer,
                st.TermTransformer,
                st.ProductCoverageTransformer,
                st.ProductDeductibleTransformer,
                st.CompanyTransformer,
                st.ProductTypeTransformer,
                st.InstallmentPlanTransformer,
                st.DeductibleTransformer,
                st.LimitTransformer,
                st.PolicyTransformer,
                st.InsuredRiskTransformer,
                st.AgentLicenseTransformer,
                st.AgentAppointmentTransformer,
                st.BlacklistedEntityTransformer,
                st.AlternateIdentityTransformer,
                st.AddressTransformer,
            ]
        )

    def test_data_fixture_transformers_replacing_reference_placeholder(self):
        """
        This is a meta test to ensure that the fixture is being populated correctly.
        If this test fails, it would mean that there exists `reference_placeholder` instances
        on the transformer fixture. This is not allowed and should be replaced within the
        fixture.
        """
        transformers = (item for item in vars(dt) if isinstance(item, JSONAPITransformer))
        for transformer in transformers:
            for (
                related_transformer
            ) in transformers_impl.iter_transformer_and_relationships_recursively(transformer):
                assert related_transformer is not dt.reference_placeholder

    def test_get_class_for_type_success(self):
        """
        Verify that the correct class is returned for the given transformer type.
        """
        factory = self.transformer_factory
        assert factories_impl.get_class_for_type(factory, "customer") == st.CustomerTransformer
        assert factories_impl.get_class_for_type(factory, "product") == st.ProductTransformer

    def test_get_class_for_type_exceptions(self):
        """
        Verify that if allow_generic is False, then an error is raised for a non-existent
        transformer.
        """
        factory = self.transformer_factory
        with pytest.raises(ValueError, match="No known transformers for type non-existent"):
            factories_impl.get_class_for_type(factory, "non-existent")

    def test_get_class_for_type_allow_generic(self):
        """
        Verify that if allow_generic is True, then the JSONAPITransformer class is returned for a
        non-existent transformer.
        """
        factory = self.transformer_factory
        factory.allow_generic = True
        result = factories_impl.get_class_for_type(factory, "non-existent")
        assert result == JSONAPITransformer

    @pytest.mark.parametrize(
        ("jsonapi_blob", "expected_transformer"),
        (
            (dt.BASIC_JSONAPI, dt.BASIC_JSONAPI_TRANSFORMER),
            (dt.JSONAPI_ID_MATCHING, dt.JSONAPI_ID_MATCHING_TRANSFORMER),
            (dt.JSONAPI_ID_AS_INTEGER, dt.JSONAPI_ID_AS_INTEGER_TRANSFORMER),
            (dt.JSONAPI_ID_NONE_LID_EMPTY, dt.JSONAPI_ID_NONE_LID_EMPTY_TRANSFORMER),
            (dt.JSONAPI_SAME_LID_VALUE, dt.JSONAPI_SAME_LID_VALUE_TRANSFORMER),
            (
                dt.JSONAPI_SAME_LID_VALUE_IN_NESTED_RELATIONSHIP,
                dt.JSONAPI_SAME_LID_VALUE_IN_NESTED_RELATIONSHIP_TRANSFORMER,
            ),
            (dt.JSONAPI_INCLUDE_RELATIONSHIP, dt.JSONAPI_INCLUDE_RELATIONSHIP_TRANSFORMER),
            (
                dt.JSONAPI_INCLUDE_COMPLEX_RELATIONSHIP,
                dt.JSONAPI_INCLUDE_COMPLEX_RELATIONSHIP_TRANSFORMER,
            ),
            (dt.JSONAPI_ID_LID, dt.JSONAPI_ID_LID_TRANSFORMER),
            (dt.JSONAPI_RELATIONSHIP_WITH_NONE, dt.JSONAPI_RELATIONSHIP_WITH_NONE_TRANSFORMER),
            (dt.JSONAPI_LIST, dt.JSONAPI_LIST_TRANSFORMER),
            (dt.JSONAPI_TOP_LIST, dt.JSONAPI_TOP_LIST_TRANSFORMERS),
            (dt.JSONAPI_SIMPLE_RECURSIVE, dt.JSONAPI_SIMPLE_RECURSIVE_TRANSFORMER),
            (dt.JSONAPI_RECURSIVE_LIST, dt.JSONAPI_RECURSIVE_LIST_TRANSFORMERS),
            (dt.JSONAPI_COMPLEX_RECURSIVE, dt.JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER),
            (dt.JSONAPI_RECURSIVE, dt.JSONAPI_RECURSIVE_TRANSFORMER),
            (
                dt.JSONAPI_RECURSIVE_WITH_IDS_AS_INTEGERS,
                dt.JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS,
            ),
            (dt.JSONAPI_TOP_LIST_WITH_INCLUDES, dt.JSONAPI_TOP_LIST_WITH_INCLUDES_TRANSFORMERS),
        ),
    )
    def test_all_from_jsonapi_data(self, jsonapi_blob, expected_transformer):
        """
        Run through all the different JSONAPI inputs and verify that the resulting transformers
        are exactly as expected.
        """
        actual_transformer = self.transformer_factory.from_jsonapi(jsonapi_blob)
        # To verify `==` is symmetric test equality in both directions
        assert expected_transformer == actual_transformer
        assert actual_transformer == expected_transformer

    def test_recursive_jsonapi_reuses_same_transformer(self):
        """
        The same instance of a transformer should be reused for all transformer relationships
        irregardless of any recursive structures.
        """
        transformer = self.transformer_factory.from_jsonapi(dt.JSONAPI_COMPLEX_RECURSIVE)
        transformer_ids = [
            transformers_impl.object_identifier(t)
            for t in transformers_impl.iter_transformer_and_relationships_recursively(transformer)
        ]
        assert len(set(transformer_ids)) == len(transformer_ids)

    def test_from_jsonapi_raises_relationship_missing_id_or_lid(self):
        """
        JSONAPI relationships missing id or lid should throw an error.
        """
        message = deepcopy(dt.BASIC_JSONAPI)
        message.pop("included")
        message["data"]["relationships"]["customer"]["data"].pop("lid")

        msg = "Relationship for type 'customer' must contain either 'id' or 'lid'"
        with pytest.raises(ContentValidationError, match=msg):
            self.transformer_factory.from_jsonapi(message)

    @pytest.mark.parametrize("key", ["attributes", "relationships"])
    def test_from_jsonapi_raises_relationship_containing_key(self, key):
        """
        Verify that relationships containing these keys will raise an error.
        """
        message = deepcopy(dt.BASIC_JSONAPI)
        customer = message["data"]["relationships"]["customer"]["data"]
        customer[key] = {"something": "not_allowed"}

        msg = f"Relationship '{customer['type']}' cannot contain the key '{key}'"
        with pytest.raises(ContentValidationError, match=msg):
            self.transformer_factory.from_jsonapi(message)

    def test_from_jsonapi_raises_unmatched_objects_error(self):
        """
        Verify that from_jsonapi() will raise an error when the `included` list contains entries
        that are not matched up with any relationship, since all includes must be matched to
        something.
        """
        message = deepcopy(dt.BASIC_JSONAPI)
        message["included"].append({"type": "customer", "lid": "LID-C2", "attributes": {"a": "b"}})
        message["included"].append({"type": "agent", "lid": "LID-A1", "attributes": {"a": "b"}})

        msg = "Missing matching relationship for these included items: agent, customer"
        with pytest.raises(ContentValidationError, match=msg):
            self.transformer_factory.from_jsonapi(message)

    def test_from_jsonapi_raises_unmatched_includes_error(self):
        """
        Verify that from_jsonapi() will raise an error when a relationship contains a local id to
        some non-existent include.

        All local id entries in a relationship must be matched up to some entry from the included
        list.
        """
        message = deepcopy(dt.BASIC_JSONAPI)
        del message["included"]

        msg = "Missing matching include for relationship in data.relationships: LID-C"
        with pytest.raises(ContentValidationError, match=msg):
            self.transformer_factory.from_jsonapi(message)

    def test_from_jsonapi_raises_duplicate_resource_key_errors(self):
        """
        Verify that from_jsonapi() will raise an error when a top level resource contains duplicate
        resource id/lids
        """
        message = deepcopy(dt.JSONAPI_SAME_ID_VALUE_IN_TOP_LEVEL_RESOURCE)

        msg = "Resource quote has duplicate id: id1"
        with pytest.raises(ContentValidationError, match=msg):
            self.transformer_factory.from_jsonapi(message)

    def test_from_jsonapi_raises_duplicate_resource_key_in_includes_errors(self):
        """
        Verify that from_jsonapi() will raise an error when a top level resource contains duplicate
        resource id/lids
        """
        message = deepcopy(dt.BASIC_JSONAPI)
        message["included"].append({"type": "customer", "lid": "LID-C", "attributes": {"a": "b"}})

        msg = "Resource customer has duplicate lid: LID-C."
        with pytest.raises(ContentValidationError, match=msg):
            self.transformer_factory.from_jsonapi(message)

    def test_from_jsonapi_raises_many_duplicate_resource_key_in_includes_errors(self):
        """
        Verify that from_jsonapi() will raise an error when a top level resource contains duplicate
        resource id/lids
        """
        message = deepcopy(dt.BASIC_JSONAPI)
        message["included"].extend(
            [
                {"type": "customer", "id": "LID-C", "attributes": {"a": "b"}},
                {"type": "customer", "id": "LID-C", "attributes": {"b": "c"}},
                {"type": "product", "id": "p1", "attributes": {"a": "b"}},
                {"type": "product", "id": "p1", "attributes": {"c": "b"}},
            ]
        )
        msg = (
            "('Resource customer has duplicate id: LID-C.', "
            "'Resource product has duplicate id: p1.')"
        )
        with pytest.raises(ContentValidationError, match=msg):
            self.transformer_factory.from_jsonapi(message)

    def test_transformer_supports_list_tuples_in_relationships(self):
        """
        Iterating relationships should support both list and tuples.
        """
        transformer = JSONAPITransformer(
            lid=1,
            type_name="item",
            relationships={
                "b": JSONAPITransformer(
                    lid=2,
                    type_name="item",
                    relationships={
                        "c": [
                            JSONAPITransformer(lid=3, type_name="item"),
                            JSONAPITransformer(lid=4, type_name="item"),
                            JSONAPITransformer(lid=5, type_name="item"),
                        ],
                        "d": JSONAPITransformer(lid=6, type_name="item"),
                    },
                ),
                "e": (
                    JSONAPITransformer(lid=7, type_name="item"),
                    JSONAPITransformer(lid=8, type_name="item"),
                ),
            },
        )
        transformers = transformers_impl.iter_transformer_and_relationships_recursively(
            transformer
        )
        assert {1, 2, 3, 4, 5, 6, 7, 8} == {p.lid for p in transformers}

    def test_iter_transformer_and_relationships_recursively_detects_cycles(self):
        """
        Recursive transformer relationships should be only iterated through once.
        """
        transformer = JSONAPITransformer(
            lid=1,
            type_name="item",
            relationships={
                "b": JSONAPITransformer(
                    lid=2,
                    type_name="item",
                    relationships={
                        "c": JSONAPITransformer(lid=3, type_name="item"),
                        "d": JSONAPITransformer(
                            lid=4,
                            type_name="item",
                            relationships={"e": JSONAPITransformer(lid=5, type_name="item")},
                        ),
                    },
                )
            },
        )
        # create recursive structure for two relationships
        transformer["b"]["c"].relationships["a"] = transformer
        transformer["b"]["d"]["e"].relationships["e"] = transformer["b"]

        transformers = transformers_impl.iter_transformer_and_relationships_recursively(
            transformer
        )
        assert {1, 2, 3, 4, 5} == {p.lid for p in transformers}

    def test_transformer_factory_disallows_duplicate_transformer_type_name(self):
        """
        Verify that Transformer factories raise an error when receiving a list of
        JSONAPITransformer that holds a duplicate type_name property
        """

        class TestTransformer(JSONAPIListTransformer):
            type_name = "test"

        class AnotherTestTransformer(JSONAPIListTransformer):
            type_name = "test"

        transformers_by_type_name = {"test": ["TestTransformer", "AnotherTestTransformer"]}

        msg = re.escape(
            f"More than one transformer of the same ''type_name'' was found."
            f" Duplicates: {transformers_by_type_name}"
        )

        with pytest.raises(ValueError, match=msg):
            JSONAPITransformerFactory(
                transformer_classes=[TestTransformer, AnotherTestTransformer]
            )


def test_from_jsonapi_generic_helper():
    """from_jsonapi_generic must convert to generic JSONAPI transformers."""

    data = {"data": {"type": "foo", "id": "bar", "attributes": {"foobar": True}}}
    result = from_jsonapi_generic(data)

    actual = JSONAPITransformer(type_name="foo", id="bar", attributes={"foobar": True})
    # To verify `==` is symmetric test equality in both directions
    assert result == actual
    assert actual == result
    # Check exact type to ensure it is generic
    assert type(result) == JSONAPITransformer  # pylint: disable=unidiomatic-typecheck
