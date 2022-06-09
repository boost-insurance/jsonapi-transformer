"""
Data structures to use in testing the JSONAPI Transformers.
"""
# flake8: noqa: E701 - Allow long lines as some transformations are much easier to read that way
# pylint: disable=line-too-long
from copy import deepcopy

from tests.data import sample_transformers as st

# To support JSONAPITransformers that have internal references, these placeholder values will be
# set to be replaced with the created object after instantiation.
reference_placeholder = object()

# Basic JSONAPI message that contains relationships and includes which are associated by lid
# Most test structures do not have multiple key/value pairs for attributes, but this one does.
# Leave these in.
BASIC_JSONAPI = {
    "data": {
        "type": "quote",
        "id": "my_id",
        "attributes": {"x": "y", "zzz": "yyy", "aaa": 1234},
        "relationships": {
            # Include a relationship with a local ID
            "customer": {"data": {"type": "customer", "lid": "LID-C"}},
            # Include a relationship with an ID
            "product": {"data": {"type": "product", "id": "p1"}},
        },
    },
    "included": [{"type": "customer", "lid": "LID-C", "attributes": {"w": "z"}}],
}
# Most expected transformers do not have an explicit value for `type_name` since that is defined on
# the transformer itself. Likewise, most expected transformers do not have a value for `id` and
# `lid` if their value is `None` since that is the default value for transformer instances. Not to
# worry though since the transformer's `__eq__` will verify that the values are correct.
# Leave these in.
BASIC_JSONAPI_TRANSFORMER = st.QuoteTransformer(
    type_name="quote",
    id="my_id",
    lid=None,
    attributes={"x": "y", "zzz": "yyy", "aaa": 1234},
    relationships={
        "customer": st.CustomerTransformer(lid="LID-C", attributes={"w": "z"}),
        "product": st.ProductTransformer(id="p1"),
    },
)

# JSONAPI message where the relationship and the include are associated by id (not lid)
# Note: Some tests should have real UUIDs so leave these in here.
JSONAPI_ID_MATCHING = {
    "data": {
        "type": "quote",
        "id": "my_id",
        "attributes": {"x": "y"},
        "relationships": {
            "customer": {
                "data": {"type": "customer", "id": "d63b2b19-3a76-4468-9637-cbb92696e928"}
            },
            "product": {"data": {"type": "product", "id": "p1"}},
        },
    },
    "included": [
        {
            "type": "customer",
            "id": "d63b2b19-3a76-4468-9637-cbb92696e928",
            "attributes": {"w": "z"},
            "relationships": {"agent": {"data": {"type": "agent", "id": "a1"}}},
        }
    ],
}
JSONAPI_ID_MATCHING_TRANSFORMER = st.QuoteTransformer(
    id="my_id",
    attributes={"x": "y"},
    relationships={
        "customer": st.CustomerTransformer(
            id="d63b2b19-3a76-4468-9637-cbb92696e928",
            attributes={"w": "z"},
            relationships={"agent": st.AgentTransformer(id="a1")},
        ),
        "product": st.ProductTransformer(id="p1"),
    },
)


# JSONAPI message where there are multiple includes with the same exact LID value, "LID-1", but for
# different relationship types. It is expected that their includes will be correctly assigned to
# the appropriate relationship, despite their LIDs being the same.
JSONAPI_SAME_LID_VALUE = {
    "data": {
        "type": "quote",
        "attributes": {"x": "y"},
        "relationships": {
            "customer": {"data": {"type": "customer", "lid": "LID-1"}},
            "insured_risk": {"data": {"type": "insured_risk", "lid": "LID-1"}},
        },
    },
    "included": [
        {"type": "customer", "lid": "LID-1", "attributes": {"c": "c2"}},
        {"type": "insured_risk", "lid": "LID-1", "attributes": {"i": "i2"}},
    ],
}
JSONAPI_SAME_LID_VALUE_TRANSFORMER = st.QuoteTransformer(
    attributes={"x": "y"},
    relationships={
        "customer": st.CustomerTransformer(lid="LID-1", attributes={"c": "c2"}),
        "insured_risk": st.InsuredRiskTransformer(lid="LID-1", attributes={"i": "i2"}),
    },
)

# JSONAPI message where there there is both id and lid, lid being an empty string.
JSONAPI_ID_NONE_LID_EMPTY = {
    "data": {"type": "quote", "id": None, "lid": "", "attributes": {"x": "y"}}
}
JSONAPI_ID_NONE_LID_EMPTY_TRANSFORMER = st.QuoteTransformer(id=None, lid="", attributes={"x": "y"})

# JSONAPI message where there are multiple includes with the same exact LID value, "LID-1", but one
# include has a relationship with the same LID (LID-1) as the outer relationship.
# It is expected that their includes will be correctly assigned to the appropriate relationship,
# despite their LIDs being the same.
JSONAPI_SAME_LID_VALUE_IN_NESTED_RELATIONSHIP = {
    "data": {
        "type": "quote",
        "attributes": {"x": "y"},
        "relationships": {"customer": {"data": {"type": "customer", "lid": "LID-1"}}},
    },
    "included": [
        {
            "type": "customer",
            "lid": "LID-1",
            "attributes": {"c": "c2"},
            "relationships": {"insured_risk": {"data": {"type": "insured_risk", "lid": "LID-1"}}},
        },
        {"type": "insured_risk", "lid": "LID-1", "attributes": {"i": "i2"}},
    ],
}
JSONAPI_SAME_LID_VALUE_IN_NESTED_RELATIONSHIP_TRANSFORMER = st.QuoteTransformer(
    attributes={"x": "y"},
    relationships={
        "customer": st.CustomerTransformer(
            lid="LID-1",
            attributes={"c": "c2"},
            relationships={
                "insured_risk": st.InsuredRiskTransformer(lid="LID-1", attributes={"i": "i2"})
            },
        )
    },
)

JSONAPI_ID_AS_INTEGER = {
    "data": {
        "type": "blacklisted_entity",
        "id": 1,
        "attributes": {"name": "name test", "remarks": "test"},
        "relationships": {
            "alternate_identities": {"data": {"type": "alternate_identity", "id": 1}},
            "addresses": {"data": {"type": "address", "id": 1}},
        },
    },
    "included": [
        {
            "type": "alternate_identity",
            "id": 1,
            "attributes": {"name": "test test", "remarks": "test"},
        },
        {
            "type": "address",
            "id": 1,
            "attributes": {"address": "test", "country": "test", "remarks": "test"},
        },
    ],
}
JSONAPI_ID_AS_INTEGER_TRANSFORMER = st.BlacklistedEntityTransformer(
    id="1",
    attributes={"name": "name test", "remarks": "test"},
    relationships={
        "alternate_identities": st.AlternateIdentityTransformer(
            id="1", attributes={"name": "test test", "remarks": "test"}
        ),
        "addresses": st.AddressTransformer(
            id="1", attributes={"address": "test", "country": "test", "remarks": "test"}
        ),
    },
)

# JSONAPI with None relationships and None nested relationships
JSONAPI_RELATIONSHIP_WITH_NONE = {
    "data": {
        "type": "quote",
        "attributes": {"test": 123},
        "relationships": {"parent": None, "sibling": {"data": {"type": "quote", "id": "q1"}}},
    },
    "included": [
        {
            "type": "quote",
            "id": "q1",
            "attributes": {"best": 234},
            "relationships": {"friend": None},
        }
    ],
}
JSONAPI_RELATIONSHIP_WITH_NONE_TRANSFORMER = st.QuoteTransformer(
    attributes={"test": 123},
    relationships={
        "parent": None,
        "sibling": st.QuoteTransformer(
            id="q1", attributes={"best": 234}, relationships={"friend": None}
        ),
    },
)

# JSONAPI message where one of the `data` values is a list of items, including lid associations.
JSONAPI_LIST = {
    "data": {
        "type": "quote",
        "id": "my_id",
        "attributes": {"x": "y"},
        "relationships": {
            # Include a relationship with a local ID
            "customer": {
                "data": [
                    {"type": "customer", "lid": "LID-C1"},
                    {"type": "customer", "lid": "LID-C2"},
                ]
            },
            # Include a relationship with an ID
            "product": {"data": {"type": "product", "id": "p1"}},
        },
    },
    "included": [
        {"type": "customer", "lid": "LID-C1", "attributes": {"w1": "z1"}},
        {"type": "customer", "lid": "LID-C2", "attributes": {"w2": "z2"}},
    ],
}
JSONAPI_LIST_TRANSFORMER = st.QuoteTransformer(
    id="my_id",
    attributes={"x": "y"},
    relationships={
        "customer": [
            st.CustomerTransformer(lid="LID-C1", attributes={"w1": "z1"}),
            st.CustomerTransformer(lid="LID-C2", attributes={"w2": "z2"}),
        ],
        "product": st.ProductTransformer(id="p1"),
    },
)

# JSONAPI message where one of the includes has a relationship to an item that is listed in the
# includes. The agency item will be put into the product item.
# Suppose an included object (eg: product) has a relationship to another included object
# (eg: agency), we expect that agency to be moved inside that product AND then that entire
# product to be moved into the top level object's relationship section. Notice the agency
# relationship below is inside the product which is inside the quote's relationship.
JSONAPI_INCLUDE_RELATIONSHIP = {
    "data": {
        "type": "quote",
        "id": "my_id",
        "attributes": {"x": "y"},
        "relationships": {
            # Include a relationship with a local ID
            "customer": {"data": {"type": "customer", "lid": "LID-C"}},
            # Include a relationship with an ID
            "product": {"data": {"type": "product", "id": "p1"}},
        },
    },
    "included": [
        {"type": "customer", "lid": "LID-C", "attributes": {"w": "z"}},
        {
            "type": "product",
            "id": "p1",
            "attributes": {"blah3": "blah4"},
            "relationships": {"agency": {"data": {"type": "agency", "id": "a1"}}},
        },
        {"type": "agency", "id": "a1", "attributes": {"blah": "blah2"}},
    ],
}
JSONAPI_INCLUDE_RELATIONSHIP_TRANSFORMER = st.QuoteTransformer(
    id="my_id",
    attributes={"x": "y"},
    relationships={
        "customer": st.CustomerTransformer(lid="LID-C", attributes={"w": "z"}),
        "product": st.ProductTransformer(
            id="p1",
            attributes={"blah3": "blah4"},
            relationships={"agency": st.AgencyTransformer(id="a1", attributes={"blah": "blah2"})},
        ),
    },
)

# Multiple levels of includes where each include can contain other relationships that are also
# included as part of the JSONAPI structure.
JSONAPI_INCLUDE_COMPLEX_RELATIONSHIP = {
    "data": {
        "type": "customer",
        "attributes": {},
        "relationships": {
            "children": {
                "data": [{"type": "quote", "id": "child-1"}, {"type": "quote", "id": "child-2"}]
            }
        },
    },
    "included": [
        {
            "type": "quote",
            "id": "child-1",
            "attributes": {"attr": 1},
            "relationships": {"infant": {"data": {"type": "product", "id": "infant-1"}}},
        },
        {
            "type": "quote",
            "id": "child-2",
            "attributes": {"attr": 2},
            "relationships": {"catman": {"data": {"type": "agent", "id": "cat-1"}}},
        },
        {
            "type": "product",
            "id": "infant-1",
            "attributes": {"attr": 3},
            "relationships": {"pet": {"data": {"type": "agency", "id": "pet-1"}}},
        },
        {
            "type": "agency",
            "id": "pet-1",
            "attributes": {"attr": 4},
            "relationships": {"cat": {"data": {"type": "agent", "id": "cat-1"}}},
        },
    ],
}
_cat = st.AgentTransformer(id="cat-1")
JSONAPI_INCLUDE_COMPLEX_RELATIONSHIP_TRANSFORMER = st.CustomerTransformer(
    relationships={
        "children": [
            st.QuoteTransformer(
                id="child-1",
                attributes={"attr": 1},
                relationships={
                    "infant": st.ProductTransformer(
                        id="infant-1",
                        attributes={"attr": 3},
                        relationships={
                            "pet": st.AgencyTransformer(
                                id="pet-1", attributes={"attr": 4}, relationships={"cat": _cat}
                            )
                        },
                    )
                },
            ),
            st.QuoteTransformer(
                id="child-2", attributes={"attr": 2}, relationships={"catman": _cat}
            ),
        ]
    }
)


# JSONAPI message where the top level data item is a list of items. We expect that a list of
# transformer objects will be returned.
JSONAPI_TOP_LIST = {
    "data": [
        {
            "type": "document",
            "id": "d1",
            "attributes": {"role": "diligence"},
            "relationships": {
                "parent": {"data": {"type": "quote", "id": "q1"}},
                "intake_agent": {"data": {"type": "agent", "id": "a1"}},
                "superceded_by": None,
            },
        },
        {
            "type": "document",
            "id": "d2",
            "attributes": {"role": "application"},
            "relationships": {
                "parent": {"data": {"type": "quote", "id": "q1"}},
                "intake_agent": {"data": {"type": "agent", "id": "a1"}},
                "superceded_by": None,
            },
        },
    ]
}
# JSONAPI_TOP_LIST_CORRECTED is the same as JSONAPI_TOP_LIST, the only difference being that the
# relationships are set to a dictionary and not None.
JSONAPI_TOP_LIST_CORRECTED = deepcopy(JSONAPI_TOP_LIST)
JSONAPI_TOP_LIST_CORRECTED["data"][0]["relationships"]["superceded_by"] = {"data": None}
JSONAPI_TOP_LIST_CORRECTED["data"][1]["relationships"]["superceded_by"] = {"data": None}
JSONAPI_TOP_LIST_TRANSFORMERS = [
    st.DocumentTransformer(
        id="d1",
        attributes={"role": "diligence"},
        relationships={
            "parent": st.QuoteTransformer(id="q1"),
            "intake_agent": st.AgentTransformer(id="a1"),
            "superceded_by": None,
        },
    ),
    st.DocumentTransformer(
        id="d2",
        attributes={"role": "application"},
        relationships={
            "parent": st.QuoteTransformer(id="q1"),
            "intake_agent": st.AgentTransformer(id="a1"),
            "superceded_by": None,
        },
    ),
]

# JSONAPI message where the top level data item is a list of items that contain duplicate ids.
JSONAPI_SAME_ID_VALUE_IN_TOP_LEVEL_RESOURCE = {
    "data": [
        {"id": "id1", "type": "quote", "attributes": {"x": "y"}, "relationships": {}},
        {"id": "id1", "type": "quote", "attributes": {"x": "z"}, "relationships": {}},
    ]
}

JSONAPI_SAME_ID_VALUE_IN_TOP_LEVEL_RESOURCE_TRANSFORMERS = [
    st.DocumentTransformer(id="id1", attributes={"x": "y"}, relationships={}),
    st.DocumentTransformer(id="id1", attributes={"x": "z"}, relationships={}),
]


# JSONAPI message that contains both an id and lid. The related customer object needs to have both
# id and lid values.
JSONAPI_ID_LID = {
    "data": {
        "type": "quote",
        "id": "q1",
        "attributes": {"convertable_on": None},
        "relationships": {"customer": {"data": {"type": "customer", "id": "c1"}}},
    },
    "included": [
        {
            "type": "customer",
            "id": "c1",
            "lid": "LID-C",
            "attributes": {"name": "name2"},
            "relationships": {"agent": {"data": {"type": "agent", "id": "a1"}}},
        }
    ],
}
JSONAPI_ID_LID_TRANSFORMER = st.QuoteTransformer(
    id="q1",
    attributes={"convertable_on": None},
    relationships={
        "customer": st.CustomerTransformer(
            id="c1",
            lid="LID-C",
            attributes={"name": "name2"},
            relationships={"agent": st.AgentTransformer(id="a1")},
        )
    },
)

# JSONAPI message that contains circular dependencies.
# pc1 -> d1 -> pc1
# pc2 -> d2 -> pc2
# pc1 and pc2 are also related to by limits which makes this more complicated.
JSONAPI_RECURSIVE = {
    "data": {
        "type": "product",
        "id": "p1",
        "attributes": {"is_admitted": True},
        "relationships": {
            "terms": {"data": [{"type": "term", "id": "t1"}]},
            "states": {"data": []},
            "coverages": {
                "data": [
                    {"type": "product_coverage", "id": "pc1"},
                    {"type": "product_coverage", "id": "pc2"},
                ]
            },
            "deductibles": {"data": [{"type": "product_deductible", "id": "pd1"}]},
            "company": {"data": {"type": "company", "id": "c1"}},
            "product_type": {"data": {"type": "product_type", "id": "pt1"}},
            "installment_plans": {
                "data": [
                    {"type": "installment_plan", "id": "ip1"},
                    {"type": "installment_plan", "id": "ip2"},
                    {"type": "installment_plan", "id": "ip3"},
                ]
            },
        },
    },
    "included": [
        {
            "type": "term",
            "id": "t1",
            "attributes": {"term_length_unit": "months"},
            "relationships": {"product": {"data": {"type": "product", "id": "p1"}}},
        },
        {
            "type": "product_coverage",
            "id": "pc1",
            "attributes": {"base_premium": "100.00"},
            "relationships": {
                "limits": {"data": [{"type": "limit", "id": "l2"}]},
                "product": {"data": {"type": "product", "id": "p1"}},
                "deductibles": {"data": [{"type": "deductible", "id": "d1"}]},
                "depends_on": {"data": None},
            },
        },
        {
            "type": "product_coverage",
            "id": "pc2",
            "attributes": {"base_premium": "200.00"},
            "relationships": {
                "limits": {"data": [{"type": "limit", "id": "l1"}]},
                "product": {"data": {"type": "product", "id": "p1"}},
                "deductibles": {"data": [{"type": "deductible", "id": "d2"}]},
                "depends_on": {"data": None},
            },
        },
        {
            "type": "product_deductible",
            "id": "pd1",
            "attributes": {"amount": "500.00"},
            "relationships": {"product": {"data": {"type": "product", "id": "p1"}}},
        },
        {"type": "installment_plan", "id": "ip1", "attributes": {"name": "MONTH"}},
        {"type": "installment_plan", "id": "ip2", "attributes": {"name": "QUARTER"}},
        {"type": "installment_plan", "id": "ip3", "attributes": {"name": "SEMI-ANNUAL"}},
        {
            "type": "limit",
            "id": "l2",
            "attributes": {"amount": "2000.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc1"}}},
        },
        {
            "type": "deductible",
            "id": "d1",
            "attributes": {"amount": "500.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc1"}}},
        },
        {
            "type": "limit",
            "id": "l1",
            "attributes": {"amount": "5000.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc2"}}},
        },
        {
            "type": "deductible",
            "id": "d2",
            "attributes": {
                "created_date": "2018-05-31T01:07:04.123219",
                "modified_date": "2018-05-31T01:07:04.123233",
                "amount": "100.00",
            },
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc2"}}},
        },
    ],
}
JSONAPI_RECURSIVE_TRANSFORMER = st.ProductTransformer(
    id="p1",
    attributes={"is_admitted": True},
    relationships={
        "terms": [
            st.TermTransformer(
                id="t1",
                attributes={"term_length_unit": "months"},
                relationships={"product": reference_placeholder},
            )
        ],
        "states": [],
        "coverages": [
            st.ProductCoverageTransformer(
                id="pc1",
                attributes={"base_premium": "100.00"},
                relationships={
                    "limits": [
                        st.LimitTransformer(
                            id="l2",
                            attributes={"amount": "2000.00"},
                            relationships={"coverage": reference_placeholder},
                        )
                    ],
                    "product": reference_placeholder,
                    "deductibles": [
                        st.DeductibleTransformer(
                            id="d1",
                            attributes={"amount": "500.00"},
                            relationships={"coverage": reference_placeholder},
                        )
                    ],
                    "depends_on": None,
                },
            ),
            st.ProductCoverageTransformer(
                id="pc2",
                attributes={"base_premium": "200.00"},
                relationships={
                    "limits": [
                        st.LimitTransformer(
                            id="l1",
                            attributes={"amount": "5000.00"},
                            relationships={"coverage": reference_placeholder},
                        )
                    ],
                    "product": st.ProductTransformer(id="p1"),
                    "deductibles": [
                        st.DeductibleTransformer(
                            id="d2",
                            attributes={
                                "created_date": "2018-05-31T01:07:04.123219",
                                "modified_date": "2018-05-31T01:07:04.123233",
                                "amount": "100.00",
                            },
                            relationships={"coverage": reference_placeholder},
                        )
                    ],
                    "depends_on": None,
                },
            ),
        ],
        "deductibles": [
            st.ProductDeductibleTransformer(
                id="pd1",
                attributes={"amount": "500.00"},
                relationships={"product": reference_placeholder},
            )
        ],
        "company": st.CompanyTransformer(id="c1"),
        "product_type": st.ProductTypeTransformer(id="pt1"),
        "installment_plans": [
            st.InstallmentPlanTransformer(id="ip1", attributes={"name": "MONTH"}),
            st.InstallmentPlanTransformer(id="ip2", attributes={"name": "QUARTER"}),
            st.InstallmentPlanTransformer(id="ip3", attributes={"name": "SEMI-ANNUAL"}),
        ],
    },
)
# fmt: off
JSONAPI_RECURSIVE_TRANSFORMER["terms"][0].relationships["product"] = JSONAPI_RECURSIVE_TRANSFORMER
JSONAPI_RECURSIVE_TRANSFORMER["deductibles"][0].relationships["product"] = JSONAPI_RECURSIVE_TRANSFORMER
JSONAPI_RECURSIVE_TRANSFORMER["coverages"][0].relationships["product"] = JSONAPI_RECURSIVE_TRANSFORMER
JSONAPI_RECURSIVE_TRANSFORMER["coverages"][1].relationships["product"] = JSONAPI_RECURSIVE_TRANSFORMER
JSONAPI_RECURSIVE_TRANSFORMER["coverages"][0]["limits"][0].relationships["coverage"] = JSONAPI_RECURSIVE_TRANSFORMER["coverages"][0]
JSONAPI_RECURSIVE_TRANSFORMER["coverages"][0]["deductibles"][0].relationships["coverage"] = JSONAPI_RECURSIVE_TRANSFORMER["coverages"][0]
JSONAPI_RECURSIVE_TRANSFORMER["coverages"][1]["limits"][0].relationships["coverage"] = JSONAPI_RECURSIVE_TRANSFORMER["coverages"][1]
JSONAPI_RECURSIVE_TRANSFORMER["coverages"][1]["deductibles"][0].relationships["coverage"] = JSONAPI_RECURSIVE_TRANSFORMER["coverages"][1]
# fmt: on

# JSONAPI message with circular dependencies
# pc1 -> d1 -> pc1
# Dev Note: Regarding the `rel_ids` tracking system in the code, this is how it would work for this
# test case: when trying to unpack "p1"s relationship to "pc1", `_find_include` will be called in
# order to find that "pc1" include. It will be called with these arugments:
#     include_type = "product_coverage"
#     identifier = "pc1"
#     identifier_type = "id"
#     parent_identifier = "p1"
#     rel_ids = {}
#
# At the end of the call to `_find_include`, the value of `rel_ids` will be `{'p1': ['pc1']}`
# because the key is the owning relationship ("p1") and the value is the list of its relationships.
# Now since "pc1" has it's own relationship to "d1", `_find_include` will be called once more with
#     include_type = "deductible"
#     identifier = "d1"
#     identifier_type = "id"
#     parent_identifier = "pc1"
#     rel_ids = {'p1': ['pc1']}
#
# Now `_find_include` will do its search and find that "deductble" relationship and will set
# `rel_ids` to: `{'p1': ['pc1', 'd1']}`. The reason it did this is because it found that the parent
# here ("pc1") is inside of a list. That means that there is a chain of relationships that needs to
# be modeled. In order to model that, it appends this newly found include, "d1", to the end of that
# list.
#
# Final (throw-away) value for `rel_ids` in this case is `{'p1': ['pc1', 'd1']}`
JSONAPI_SIMPLE_RECURSIVE = {
    "data": {
        "type": "product",
        "id": "p1",
        "attributes": {"is_admitted": True},
        "relationships": {"coverages": {"data": [{"type": "product_coverage", "id": "pc1"}]}},
    },
    "included": [
        {
            "type": "product_coverage",
            "id": "pc1",
            "attributes": {"base_premium": "100.00"},
            "relationships": {"deductibles": {"data": [{"type": "deductible", "id": "d1"}]}},
        },
        {
            "type": "deductible",
            "id": "d1",
            "attributes": {"amount": "500.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc1"}}},
        },
    ],
}
JSONAPI_SIMPLE_RECURSIVE_TRANSFORMER = st.ProductTransformer(
    id="p1",
    attributes={"is_admitted": True},
    relationships={
        "coverages": [
            st.ProductCoverageTransformer(
                id="pc1",
                attributes={"base_premium": "100.00"},
                relationships={
                    "deductibles": [
                        st.DeductibleTransformer(
                            id="d1",
                            attributes={"amount": "500.00"},
                            relationships={"coverage": reference_placeholder},
                        )
                    ]
                },
            )
        ]
    },
)
# fmt: off
JSONAPI_SIMPLE_RECURSIVE_TRANSFORMER.relationships["coverages"][0].relationships["deductibles"][0].relationships["coverage"] = JSONAPI_SIMPLE_RECURSIVE_TRANSFORMER.relationships["coverages"][0]
# fmt: on

# JSONAPI message where one included item is used by multiple data items.
# a1 is related to by both p1 and p2.
JSONAPI_RECURSIVE_LIST = {
    "data": [
        {
            "type": "product",
            "id": "p1",
            "attributes": {"created_date": "2019-01-09T15:16:24.988798+0000"},
            "relationships": {"agency": {"data": {"type": "agency", "id": "a1"}}},
        },
        {
            "type": "product",
            "id": "p2",
            "attributes": {"created_date": "2019-01-09T15:15:43.531966+0000"},
            "relationships": {"agency": {"data": {"type": "agency", "id": "a1"}}},
        },
    ],
    "included": [{"type": "agency", "id": "a1", "attributes": {"commission_percent": "20.00"}}],
}
JSONAPI_RECURSIVE_LIST_TRANSFORMERS = [
    st.ProductTransformer(
        id="p1",
        attributes={"created_date": "2019-01-09T15:16:24.988798+0000"},
        relationships={
            "agency": st.AgencyTransformer(
                id="a1", attributes={"commission_percent": "20.00"}, relationships={}
            )
        },
    ),
    st.ProductTransformer(
        id="p2",
        attributes={"created_date": "2019-01-09T15:15:43.531966+0000"},
        relationships={
            "agency": st.AgencyTransformer(
                id="a1", attributes={"commission_percent": "20.00"}, relationships={}
            )
        },
    ),
]

# JSONAPI message where an include relates to another include
#     We expect that a list of transformer objects will be returned.
JSONAPI_TOP_LIST_WITH_INCLUDES = {
    "links": {
        "first": "https://example.com/my_query_path_1",
        "last": "https://example.com/my_query_path_2",
        "next": None,
        "prev": None,
    },
    "data": [
        {
            "type": "policy",
            "id": "po1",
            "attributes": {"policy_number": "pn1"},
            "relationships": {
                "coverages": {"meta": {"count": 0}, "data": []},
                "product": {"data": {"type": "product", "id": "p1"}},
                "agent": {"data": {"type": "agent", "id": "at1"}},
                "installment_plan": {"data": {"type": "installment_plan", "id": "ip1"}},
                "customer": {"data": {"type": "customer", "id": "c1"}},
                "parent": {"data": {"type": "policy", "id": "pa1"}},
                "insured_risk": {"data": {"type": "insured_risk", "id": "ir1"}},
                "additional_interests": {"meta": {"count": 0}, "data": []},
                "additional_insured": {"meta": {"count": 0}, "data": []},
            },
        }
    ],
    "included": [
        {
            "type": "agent",
            "id": "at1",
            "attributes": {"email": "a@a.io"},
            "relationships": {
                "licenses": {
                    "meta": {"count": 28},
                    "data": [
                        {"type": "agent_license", "id": "al1"},
                        {"type": "agent_license", "id": "al2"},
                        {"type": "agent_license", "id": "al3"},
                    ],
                },
                "appointments": {
                    "meta": {"count": 56},
                    "data": [
                        {"type": "agent_appointment", "id": "aa1"},
                        {"type": "agent_appointment", "id": "aa2"},
                        {"type": "agent_appointment", "id": "aa3"},
                    ],
                },
                "agency": {"data": {"type": "agency", "id": "ay1"}},
            },
        },
        {"type": "agency", "id": "ay1", "attributes": {"email": "a@a.io"}},
    ],
    "meta": {"pagination": {"page": 1, "pages": 1, "count": 1}},
}
# JSONAPI_TOP_LIST_WITH_INCLUDES_CLEAN is the same as JSONAPI_TOP_LIST_WITH_INCLUDES, but
# without the links and meta keys.
JSONAPI_TOP_LIST_WITH_INCLUDES_CLEAN = deepcopy(JSONAPI_TOP_LIST_WITH_INCLUDES)
del JSONAPI_TOP_LIST_WITH_INCLUDES_CLEAN["links"]
del JSONAPI_TOP_LIST_WITH_INCLUDES_CLEAN["meta"]
del JSONAPI_TOP_LIST_WITH_INCLUDES_CLEAN["data"][0]["relationships"]["coverages"]["meta"]
del JSONAPI_TOP_LIST_WITH_INCLUDES_CLEAN["data"][0]["relationships"]["additional_interests"][
    "meta"
]
del JSONAPI_TOP_LIST_WITH_INCLUDES_CLEAN["data"][0]["relationships"]["additional_insured"]["meta"]
del JSONAPI_TOP_LIST_WITH_INCLUDES_CLEAN["included"][0]["relationships"]["licenses"]["meta"]
del JSONAPI_TOP_LIST_WITH_INCLUDES_CLEAN["included"][0]["relationships"]["appointments"]["meta"]

JSONAPI_TOP_LIST_WITH_INCLUDES_TRANSFORMERS = [
    st.PolicyTransformer(
        id="po1",
        attributes={"policy_number": "pn1"},
        relationships={
            "coverages": [],
            "product": st.ProductTransformer(id="p1"),
            "agent": st.AgentTransformer(
                id="at1",
                attributes={"email": "a@a.io"},
                relationships={
                    "licenses": [
                        st.AgentLicenseTransformer(id="al1"),
                        st.AgentLicenseTransformer(id="al2"),
                        st.AgentLicenseTransformer(id="al3"),
                    ],
                    "appointments": [
                        st.AgentAppointmentTransformer(id="aa1"),
                        st.AgentAppointmentTransformer(id="aa2"),
                        st.AgentAppointmentTransformer(id="aa3"),
                    ],
                    "agency": st.AgencyTransformer(id="ay1", attributes={"email": "a@a.io"}),
                },
            ),
            "installment_plan": st.InstallmentPlanTransformer(id="ip1"),
            "customer": st.CustomerTransformer(id="c1"),
            "parent": st.PolicyTransformer(id="pa1"),
            "insured_risk": st.InsuredRiskTransformer(id="ir1"),
            "additional_interests": [],
            "additional_insured": [],
        },
    )
]

# JSONAPI message where the recursion is complicated by the fact that one relationship is used
# deep inside another relationship.
# pc7 has a `depends_on` relationship to pc8.
# several of the product coverage items have relationships to limits that point back to the
# product coverage item.
JSONAPI_COMPLEX_RECURSIVE = {
    "data": {
        "type": "product",
        "id": "p1",
        "attributes": {"name": "Rentsure"},
        "relationships": {
            "terms": {"data": [{"type": "term", "id": "t1"}, {"type": "term", "id": "t2"}]},
            "deductibles": {
                "data": [
                    {"type": "product_deductible", "id": "pd1"},
                    {"type": "product_deductible", "id": "pd2"},
                    {"type": "product_deductible", "id": "pd3"},
                ]
            },
            "coverages": {
                "data": [
                    {"type": "product_coverage", "id": "pc1"},
                    {"type": "product_coverage", "id": "pc2"},
                    {"type": "product_coverage", "id": "pc3"},
                    {"type": "product_coverage", "id": "pc4"},
                    {"type": "product_coverage", "id": "pc5"},
                    {"type": "product_coverage", "id": "pc6"},
                    {"type": "product_coverage", "id": "pc7"},
                    {"type": "product_coverage", "id": "pc8"},
                ]
            },
            "states": {"data": []},
            "limits": {"data": []},
            "company": {"data": {"type": "company", "id": "c1"}},
            "agency": {"data": {"type": "agency", "id": "fcd74b40-a110-4f59-b88b-a3fa17146891"}},
            "parent": {"data": None},
            "product_type": {"data": {"type": "product_type", "id": "pt1"}},
            "installment_plans": {
                "data": [
                    {"type": "installment_plan", "id": "ip1"},
                    {"type": "installment_plan", "id": "ip2"},
                    {"type": "installment_plan", "id": "ip3"},
                ]
            },
        },
    },
    "included": [
        {
            "type": "term",
            "id": "t1",
            "attributes": {"term_length_max": 12},
            "relationships": {"product": {"data": {"type": "product", "id": "p1"}}},
        },
        {
            "type": "term",
            "id": "t2",
            "attributes": {"term_length_max": 6},
            "relationships": {"product": {"data": {"type": "product", "id": "p1"}}},
        },
        {
            "type": "product_deductible",
            "id": "pd1",
            "attributes": {"amount": "1000.00"},
            "relationships": {"product": {"data": {"type": "product", "id": "p1"}}},
        },
        {
            "type": "product_deductible",
            "id": "pd2",
            "attributes": {"amount": "500.00"},
            "relationships": {"product": {"data": {"type": "product", "id": "p1"}}},
        },
        {
            "type": "product_deductible",
            "id": "pd3",
            "attributes": {"amount": "250.00"},
            "relationships": {"product": {"data": {"type": "product", "id": "p1"}}},
        },
        {
            "type": "product_coverage",
            "id": "pc1",
            "attributes": {"label": "Unscheduled Jewelry"},
            "relationships": {
                "product": {"data": {"type": "product", "id": "p1"}},
                "limits": {"data": [{"type": "limit", "id": "l4"}]},
                "deductibles": {"data": []},
                "depends_on": {"data": None},
            },
        },
        {
            "type": "product_coverage",
            "id": "pc2",
            "attributes": {"label": "Tenants Plus"},
            "relationships": {
                "product": {"data": {"type": "product", "id": "p1"}},
                "limits": {"data": []},
                "deductibles": {"data": []},
                "depends_on": {"data": None},
            },
        },
        {
            "type": "product_coverage",
            "id": "pc3",
            "attributes": {"label": "Water Backup"},
            "relationships": {
                "product": {"data": {"type": "product", "id": "p1"}},
                "limits": {"data": []},
                "deductibles": {"data": []},
                "depends_on": {"data": None},
            },
        },
        {
            "type": "product_coverage",
            "id": "pc4",
            "attributes": {"label": "Pet Damage"},
            "relationships": {
                "product": {"data": {"type": "product", "id": "p1"}},
                "limits": {"data": [{"type": "limit", "id": "l6"}]},
                "deductibles": {"data": []},
                "depends_on": {"data": None},
            },
        },
        {
            "type": "product_coverage",
            "id": "pc5",
            "attributes": {"label": "Coverage F - Medical Payments"},
            "relationships": {
                "product": {"data": {"type": "product", "id": "p1"}},
                "limits": {
                    "data": [
                        {"type": "limit", "id": "l9"},
                        {"type": "limit", "id": "l1"},
                        {"type": "limit", "id": "l3"},
                    ]
                },
                "deductibles": {"data": []},
                "depends_on": {"data": None},
            },
        },
        {
            "type": "product_coverage",
            "id": "pc6",
            "attributes": {"label": "Coverage E - Liability"},
            "relationships": {
                "product": {"data": {"type": "product", "id": "p1"}},
                "limits": {
                    "data": [
                        {"type": "limit", "id": "l8"},
                        {"type": "limit", "id": "l2"},
                        {"type": "limit", "id": "l10"},
                    ]
                },
                "deductibles": {"data": []},
                "depends_on": {"data": None},
            },
        },
        {
            "type": "product_coverage",
            "id": "pc7",
            "attributes": {"label": "Coverage D - Loss of Use"},
            "relationships": {
                "product": {"data": {"type": "product", "id": "p1"}},
                "limits": {"data": [{"type": "limit", "id": "l5"}]},
                "deductibles": {"data": []},
                "depends_on": {"data": {"type": "product_coverage", "id": "pc8"}},
            },
        },
        {
            "type": "product_coverage",
            "id": "pc8",
            "attributes": {"label": "Coverage C - Property"},
            "relationships": {
                "product": {"data": {"type": "product", "id": "p1"}},
                "limits": {"data": [{"type": "limit", "id": "l7"}]},
                "deductibles": {"data": []},
                "depends_on": {"data": None},
            },
        },
        {
            "type": "limit",
            "id": "l4",
            "attributes": {"amount": "500.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc1"}}},
        },
        {
            "type": "limit",
            "id": "l6",
            "attributes": {"amount": "500.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc4"}}},
        },
        {
            "type": "limit",
            "id": "l9",
            "attributes": {"amount": "2000.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc5"}}},
        },
        {
            "type": "limit",
            "id": "l1",
            "attributes": {"amount": "1000.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc5"}}},
        },
        {
            "type": "limit",
            "id": "l3",
            "attributes": {"amount": "500.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc5"}}},
        },
        {
            "type": "limit",
            "id": "l8",
            "attributes": {"amount": "300000.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc6"}}},
        },
        {
            "type": "limit",
            "id": "l2",
            "attributes": {"amount": "100000.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc6"}}},
        },
        {
            "type": "limit",
            "id": "l10",
            "attributes": {"amount": "50000.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc6"}}},
        },
        {
            "type": "limit",
            "id": "l5",
            "attributes": {"amount": "2000.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc7"}}},
        },
        {
            "type": "limit",
            "id": "l7",
            "attributes": {"amount": "10000.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc8"}}},
        },
    ],
}
JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER = st.ProductTransformer(
    id="p1",
    attributes={"name": "Rentsure"},
    relationships={
        "terms": [
            st.TermTransformer(
                id="t1",
                attributes={"term_length_max": 12},
                relationships={"product": reference_placeholder},
            ),
            st.TermTransformer(
                id="t2",
                attributes={"term_length_max": 6},
                relationships={"product": reference_placeholder},
            ),
        ],
        "deductibles": [
            st.ProductDeductibleTransformer(
                id="pd1",
                attributes={"amount": "1000.00"},
                relationships={"product": reference_placeholder},
            ),
            st.ProductDeductibleTransformer(
                id="pd2",
                attributes={"amount": "500.00"},
                relationships={"product": reference_placeholder},
            ),
            st.ProductDeductibleTransformer(
                id="pd3",
                attributes={"amount": "250.00"},
                relationships={"product": reference_placeholder},
            ),
        ],
        "coverages": [
            st.ProductCoverageTransformer(
                id="pc1",
                attributes={"label": "Unscheduled Jewelry"},
                relationships={
                    "product": reference_placeholder,
                    "limits": [
                        st.LimitTransformer(
                            id="l4",
                            attributes={"amount": "500.00"},
                            relationships={"coverage": reference_placeholder},
                        )
                    ],
                    "deductibles": [],
                    "depends_on": None,
                },
            ),
            st.ProductCoverageTransformer(
                id="pc2",
                attributes={"label": "Tenants Plus"},
                relationships={
                    "product": reference_placeholder,
                    "limits": [],
                    "deductibles": [],
                    "depends_on": None,
                },
            ),
            st.ProductCoverageTransformer(
                id="pc3",
                attributes={"label": "Water Backup"},
                relationships={
                    "product": reference_placeholder,
                    "limits": [],
                    "deductibles": [],
                    "depends_on": None,
                },
            ),
            st.ProductCoverageTransformer(
                id="pc4",
                attributes={"label": "Pet Damage"},
                relationships={
                    "product": reference_placeholder,
                    "limits": [
                        st.LimitTransformer(
                            id="l6",
                            attributes={"amount": "500.00"},
                            relationships={"coverage": reference_placeholder},
                        )
                    ],
                    "deductibles": [],
                    "depends_on": None,
                },
            ),
            st.ProductCoverageTransformer(
                id="pc5",
                attributes={"label": "Coverage F - Medical Payments"},
                relationships={
                    "product": reference_placeholder,
                    "limits": [
                        st.LimitTransformer(
                            id="l9",
                            attributes={"amount": "2000.00"},
                            relationships={"coverage": reference_placeholder},
                        ),
                        st.LimitTransformer(
                            id="l1",
                            attributes={"amount": "1000.00"},
                            relationships={"coverage": reference_placeholder},
                        ),
                        st.LimitTransformer(
                            id="l3",
                            attributes={"amount": "500.00"},
                            relationships={"coverage": reference_placeholder},
                        ),
                    ],
                    "deductibles": [],
                    "depends_on": None,
                },
            ),
            st.ProductCoverageTransformer(
                id="pc6",
                attributes={"label": "Coverage E - Liability"},
                relationships={
                    "product": reference_placeholder,
                    "limits": [
                        st.LimitTransformer(
                            id="l8",
                            attributes={"amount": "300000.00"},
                            relationships={"coverage": reference_placeholder},
                        ),
                        st.LimitTransformer(
                            id="l2",
                            attributes={"amount": "100000.00"},
                            relationships={"coverage": reference_placeholder},
                        ),
                        st.LimitTransformer(
                            id="l10",
                            attributes={"amount": "50000.00"},
                            relationships={"coverage": reference_placeholder},
                        ),
                    ],
                    "deductibles": [],
                    "depends_on": None,
                },
            ),
            st.ProductCoverageTransformer(
                id="pc7",
                attributes={"label": "Coverage D - Loss of Use"},
                relationships={
                    "product": reference_placeholder,
                    "limits": [
                        st.LimitTransformer(
                            id="l5",
                            attributes={"amount": "2000.00"},
                            relationships={"coverage": reference_placeholder},
                        )
                    ],
                    "deductibles": [],
                    "depends_on": st.ProductCoverageTransformer(
                        id="pc8",
                        attributes={"label": "Coverage C - Property"},
                        relationships={
                            "product": reference_placeholder,
                            "limits": [
                                st.LimitTransformer(
                                    id="l7",
                                    attributes={"amount": "10000.00"},
                                    relationships={"coverage": reference_placeholder},
                                )
                            ],
                            "deductibles": [],
                            "depends_on": None,
                        },
                    ),
                },
            ),
            st.ProductCoverageTransformer(
                id="pc8",
                attributes={"label": "Coverage C - Property"},
                relationships={
                    "product": reference_placeholder,
                    "limits": [
                        st.LimitTransformer(
                            id="l7",
                            attributes={"amount": "10000.00"},
                            relationships={"coverage": reference_placeholder},
                        )
                    ],
                    "deductibles": [],
                    "depends_on": None,
                },
            ),
        ],
        "states": [],
        "limits": [],
        "company": st.CompanyTransformer(id="c1", attributes={}, relationships={}),
        "agency": st.AgencyTransformer(
            id="fcd74b40-a110-4f59-b88b-a3fa17146891", attributes={}, relationships={}
        ),
        "parent": None,
        "product_type": st.ProductTypeTransformer(id="pt1", attributes={}, relationships={}),
        "installment_plans": [
            st.InstallmentPlanTransformer(id="ip1", attributes={}, relationships={}),
            st.InstallmentPlanTransformer(id="ip2", attributes={}, relationships={}),
            st.InstallmentPlanTransformer(id="ip3", attributes={}, relationships={}),
        ],
    },
)
for relationship in ("coverages", "deductibles", "terms"):
    for item in JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER[relationship]:
        item.relationships["product"] = JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER
# fmt: off
JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][6]["depends_on"].relationships["product"] = JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER
JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][0]["limits"][0].relationships["coverage"] = JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][0]
JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][3]["limits"][0].relationships["coverage"] = JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][3]
JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][4]["limits"][0].relationships["coverage"] = JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][4]
JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][4]["limits"][1].relationships["coverage"] = JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][4]
JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][4]["limits"][2].relationships["coverage"] = JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][4]
JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][5]["limits"][0].relationships["coverage"] = JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][5]
JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][5]["limits"][1].relationships["coverage"] = JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][5]
JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][5]["limits"][2].relationships["coverage"] = JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][5]
JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][6]["limits"][0].relationships["coverage"] = JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][6]
JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][6]["depends_on"]["limits"][0].relationships["coverage"] = JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][7]
JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][7]["limits"][0].relationships["coverage"] = JSONAPI_COMPLEX_RECURSIVE_TRANSFORMER["coverages"][7]
# fmt: on

# TO JSONAPI TESTS
TO_JSONAPI_COMPLEX_TRANSFORMER = st.ProductTransformer(
    id="p1",
    attributes={"is_admitted": True},
    relationships={
        "terms": [
            st.TermTransformer(
                id="t1",
                attributes={"term_length_unit": "months"},
                relationships={"product": st.ProductTransformer(id="p1")},
            )
        ],
        "states": [],
        "coverages": [
            st.ProductCoverageTransformer(
                id="pc1",
                attributes={"base_premium": "100.00"},
                relationships={
                    "limits": [
                        st.LimitTransformer(
                            id="l1",
                            attributes={"amount": "2000.00"},
                            relationships={"coverage": st.ProductCoverageTransformer(id="pc1")},
                        )
                    ],
                    "product": st.ProductTransformer(id="p1"),
                    "deductibles": [
                        st.DeductibleTransformer(
                            id="d1",
                            attributes={"amount": "500.00"},
                            relationships={"coverage": st.ProductCoverageTransformer(id="pc1")},
                        )
                    ],
                    "depends_on": None,
                },
            ),
            st.ProductCoverageTransformer(
                id="pc2",
                attributes={"base_premium": "200.00"},
                relationships={
                    "limits": [
                        st.LimitTransformer(
                            id="l2",
                            attributes={"amount": "5000.00"},
                            relationships={"coverage": st.ProductCoverageTransformer(id="pc2")},
                        )
                    ],
                    "product": st.ProductTransformer(id="p1"),
                    "deductibles": [
                        st.DeductibleTransformer(
                            id="d2",
                            attributes={"amount": "100.00"},
                            relationships={"coverage": st.ProductCoverageTransformer(id="pc2")},
                        )
                    ],
                    "depends_on": None,
                },
            ),
        ],
        "deductibles": [
            st.ProductDeductibleTransformer(
                id="d3",
                attributes={"amount": "500.00"},
                relationships={"product": st.ProductTransformer(id="p1")},
            )
        ],
        "company": st.CompanyTransformer(id="c1"),
        "product_type": st.ProductTypeTransformer(id="pt1"),
        "installment_plans": [
            st.InstallmentPlanTransformer(id="ip1", attributes={"name": "MONTH"}),
            st.InstallmentPlanTransformer(id="ip2", attributes={"name": "QUARTER"}),
            st.InstallmentPlanTransformer(id="ip3", attributes={"name": "SEMI-ANNUAL"}),
        ],
    },
)
TO_JSONAPI_COMPLEX_TRANSFORMER_EXP_JSONAPI = {
    "data": {
        "type": "product",
        "id": "p1",
        "attributes": {"is_admitted": True},
        "relationships": {
            "terms": {"data": [{"type": "term", "id": "t1"}]},
            "states": {"data": []},
            "coverages": {
                "data": [
                    {"type": "product_coverage", "id": "pc1"},
                    {"type": "product_coverage", "id": "pc2"},
                ]
            },
            "deductibles": {"data": [{"type": "product_deductible", "id": "d3"}]},
            "company": {"data": {"type": "company", "id": "c1"}},
            "product_type": {"data": {"type": "product_type", "id": "pt1"}},
            "installment_plans": {
                "data": [
                    {"type": "installment_plan", "id": "ip1"},
                    {"type": "installment_plan", "id": "ip2"},
                    {"type": "installment_plan", "id": "ip3"},
                ]
            },
        },
    },
    "included": [
        {
            "type": "term",
            "id": "t1",
            "attributes": {"term_length_unit": "months"},
            "relationships": {"product": {"data": {"type": "product", "id": "p1"}}},
        },
        {
            "type": "product_coverage",
            "id": "pc1",
            "attributes": {"base_premium": "100.00"},
            "relationships": {
                "limits": {"data": [{"type": "limit", "id": "l1"}]},
                "product": {"data": {"type": "product", "id": "p1"}},
                "deductibles": {"data": [{"type": "deductible", "id": "d1"}]},
                "depends_on": {"data": None},
            },
        },
        {
            "type": "product_coverage",
            "id": "pc2",
            "attributes": {"base_premium": "200.00"},
            "relationships": {
                "limits": {"data": [{"type": "limit", "id": "l2"}]},
                "product": {"data": {"type": "product", "id": "p1"}},
                "deductibles": {"data": [{"type": "deductible", "id": "d2"}]},
                "depends_on": {"data": None},
            },
        },
        {
            "type": "product_deductible",
            "id": "d3",
            "attributes": {"amount": "500.00"},
            "relationships": {"product": {"data": {"type": "product", "id": "p1"}}},
        },
        {"type": "installment_plan", "id": "ip1", "attributes": {"name": "MONTH"}},
        {"type": "installment_plan", "id": "ip2", "attributes": {"name": "QUARTER"}},
        {"type": "installment_plan", "id": "ip3", "attributes": {"name": "SEMI-ANNUAL"}},
        {
            "type": "limit",
            "id": "l1",
            "attributes": {"amount": "2000.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc1"}}},
        },
        {
            "type": "deductible",
            "id": "d1",
            "attributes": {"amount": "500.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc1"}}},
        },
        {
            "type": "limit",
            "id": "l2",
            "attributes": {"amount": "5000.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc2"}}},
        },
        {
            "type": "deductible",
            "id": "d2",
            "attributes": {"amount": "100.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": "pc2"}}},
        },
    ],
}


JSONAPI_RECURSIVE_WITH_IDS_AS_INTEGERS = {
    "data": {
        "type": "product",
        "id": 1,
        "attributes": {"is_admitted": True},
        "relationships": {
            "terms": {"data": [{"type": "term", "id": 2}]},
            "states": {"data": []},
            "coverages": {
                "data": [
                    {"type": "product_coverage", "id": 3},
                    {"type": "product_coverage", "id": 4},
                ]
            },
            "deductibles": {"data": [{"type": "product_deductible", "id": 5}]},
            "company": {"data": {"type": "company", "id": 5}},
            "product_type": {"data": {"type": "product_type", "id": 6}},
            "installment_plans": {
                "data": [
                    {"type": "installment_plan", "id": 7},
                    {"type": "installment_plan", "id": 8},
                    {"type": "installment_plan", "id": 9},
                ]
            },
        },
    },
    "included": [
        {
            "type": "deductible",
            "id": 10,
            "attributes": {"amount": "500.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": 3}}},
        },
        {
            "type": "deductible",
            "id": 11,
            "attributes": {
                "created_date": "2018-05-31T01:07:04.123219",
                "modified_date": "2018-05-31T01:07:04.123233",
                "amount": "100.00",
            },
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": 4}}},
        },
        {"type": "installment_plan", "id": 9, "attributes": {"name": "SEMI-ANNUAL"}},
        {"type": "installment_plan", "id": 8, "attributes": {"name": "QUARTER"}},
        {"type": "installment_plan", "id": 7, "attributes": {"name": "MONTH"}},
        {
            "type": "limit",
            "id": 12,
            "attributes": {"amount": "2000.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": 3}}},
        },
        {
            "type": "limit",
            "id": 13,
            "attributes": {"amount": "5000.00"},
            "relationships": {"coverage": {"data": {"type": "product_coverage", "id": 4}}},
        },
        {
            "type": "product_coverage",
            "id": 4,
            "attributes": {"base_premium": "200.00"},
            "relationships": {
                "limits": {"data": [{"type": "limit", "id": 13}]},
                "product": {"data": {"type": "product", "id": 1}},
                "deductibles": {"data": [{"type": "deductible", "id": 11}]},
                "depends_on": {"data": None},
            },
        },
        {
            "type": "product_coverage",
            "id": 3,
            "attributes": {"base_premium": "100.00"},
            "relationships": {
                "limits": {"data": [{"type": "limit", "id": 12}]},
                "product": {"data": {"type": "product", "id": 1}},
                "deductibles": {"data": [{"type": "deductible", "id": 10}]},
                "depends_on": {"data": None},
            },
        },
        {
            "type": "product_deductible",
            "id": 5,
            "attributes": {"amount": "500.00"},
            "relationships": {"product": {"data": {"type": "product", "id": 1}}},
        },
        {
            "type": "term",
            "id": 2,
            "attributes": {"term_length_unit": "months"},
            "relationships": {"product": {"data": {"type": "product", "id": 1}}},
        },
    ],
}
JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS = st.ProductTransformer(
    id="1",
    attributes={"is_admitted": True},
    relationships={
        "terms": [
            st.TermTransformer(
                id="2",
                attributes={"term_length_unit": "months"},
                relationships={"product": reference_placeholder},
            )
        ],
        "states": [],
        "coverages": [
            st.ProductCoverageTransformer(
                id="3",
                attributes={"base_premium": "100.00"},
                relationships={
                    "limits": [
                        st.LimitTransformer(
                            id="12",
                            attributes={"amount": "2000.00"},
                            relationships={"coverage": reference_placeholder},
                        )
                    ],
                    "product": reference_placeholder,
                    "deductibles": [
                        st.DeductibleTransformer(
                            id="10",
                            attributes={"amount": "500.00"},
                            relationships={"coverage": reference_placeholder},
                        )
                    ],
                    "depends_on": None,
                },
            ),
            st.ProductCoverageTransformer(
                id="4",
                attributes={"base_premium": "200.00"},
                relationships={
                    "limits": [
                        st.LimitTransformer(
                            id="13",
                            attributes={"amount": "5000.00"},
                            relationships={"coverage": reference_placeholder},
                        )
                    ],
                    "product": reference_placeholder,
                    "deductibles": [
                        st.DeductibleTransformer(
                            id="11",
                            attributes={
                                "created_date": "2018-05-31T01:07:04.123219",
                                "modified_date": "2018-05-31T01:07:04.123233",
                                "amount": "100.00",
                            },
                            relationships={"coverage": reference_placeholder},
                        )
                    ],
                    "depends_on": None,
                },
            ),
        ],
        "deductibles": [
            st.ProductDeductibleTransformer(
                id="5",
                attributes={"amount": "500.00"},
                relationships={"product": reference_placeholder},
            )
        ],
        "company": st.CompanyTransformer(id="5"),
        "product_type": st.ProductTypeTransformer(id="6"),
        "installment_plans": [
            st.InstallmentPlanTransformer(id="7", attributes={"name": "MONTH"}),
            st.InstallmentPlanTransformer(id="8", attributes={"name": "QUARTER"}),
            st.InstallmentPlanTransformer(id="9", attributes={"name": "SEMI-ANNUAL"}),
        ],
    },
)
# fmt: off
JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS["terms"][0].relationships["product"] = JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS
JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS["deductibles"][0].relationships["product"] = JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS
JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS["coverages"][0].relationships["product"] = JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS
JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS["coverages"][1].relationships["product"] = JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS
JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS["coverages"][0]["limits"][0].relationships["coverage"] = JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS["coverages"][0]
JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS["coverages"][0]["deductibles"][0].relationships["coverage"] = JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS["coverages"][0]
JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS["coverages"][1]["limits"][0].relationships["coverage"] = JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS["coverages"][1]
JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS["coverages"][1]["deductibles"][0].relationships["coverage"] = JSONAPI_RECURSIVE_TRANSFORMER_WITH_IDS_AS_INTEGERS["coverages"][1]
# fmt: on
