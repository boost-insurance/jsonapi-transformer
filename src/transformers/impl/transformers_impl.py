"""
The entirety of this file should be considered private implementation details for the public-facing
transformers.py.
"""

from collections import deque
from copy import deepcopy
from typing import TYPE_CHECKING, Iterator, List, MutableSet, Optional, Tuple, Type, Union

from transformers.exceptions import ContentValidationError
from transformers.impl import JsonapiResource, RelationshipsDict

if TYPE_CHECKING:
    from transformers.transformers import JSONAPITransformer


def object_identifier(obj: object) -> int:
    """
    Return the “identity” of an object. This is an integer which is guaranteed to be unique and
    constant for this object during its lifetime. Two objects with non-overlapping lifetimes may
    have the same identity value.

    Args:
        obj: An object.

    Returns:
        The object's "identity".
    """
    return id(obj)


def object_key(transformer: "JSONAPITransformer") -> Tuple[str, Optional[str], Optional[str]]:
    """
    Return the "key" of a transformer object.

    Args:
        transformer: A transformer object.

    Returns:
        The transformer's "key" for simple comparisons.
    """
    return transformer.type_name, transformer.id, transformer.lid


def apply_defaults_non_recursively(transformer: "JSONAPITransformer") -> None:
    """
    Utility method to apply defaults to this transformer only.

    Args:
        transformer: A transformer object.
    """
    for key, value in transformer.get_defaults_for_optional_attributes().items():
        transformer.attributes.setdefault(key, value)
    for key, value in transformer.get_defaults_for_optional_relationships().items():
        transformer.relationships.setdefault(key, value)


def iter_transformer_and_relationships_recursively(
    transformer: "JSONAPITransformer",
) -> Iterator["JSONAPITransformer"]:
    """
    Return the input transformer, all related transformers, all transformers related to them, etc.

    Each transformer will only be yielded once, even if attached in multiple relationships.
    Ordering is not defined.

    Args:
        transformer: A transformer object.

    Yields:
        A transformer. The transformer itself is yielded before looking at its relationships, in
            case the calling function wants to modify those relationships.
    """
    queue = deque([transformer])
    seen = set()

    while queue:
        candidate = queue.popleft()

        if candidate is None or object_identifier(candidate) in seen:
            continue

        seen.add(object_identifier(candidate))
        yield candidate

        for relationship in candidate.relationships.values():
            if isinstance(relationship, (list, tuple)):
                queue.extend(relationship)
            else:
                queue.append(relationship)


def to_jsonapi_data(transformer: "JSONAPITransformer") -> JsonapiResource:
    """
    Create a JSONAPI 'data' dictionary with the properties of this instance.

    Note that this does not include 'included'.

    Args:
        transformer: A transformer object.

    Returns:
        A 'data' dictionary with 'type'; and optionally 'id', 'lid', 'attributes', and/or
            'relationships'.
    """

    relationships = {
        name: {"data": get_relationship_data(rel_obj)}
        for name, rel_obj in transformer.relationships.items()
    }

    if not isinstance(transformer.type_name, str):
        raise ContentValidationError("`type_name` must be a string.")

    # At first glance, it would seem this is a good spot to validate that at least one of
    # `id` or `lid` is not `None`, as required by the spec. However, for request bodies, the
    # top-level object doesn't require either of them. We have no way of knowing whether the
    # transformer is for a request or a response, so we cannot enforce this rule.

    data: JsonapiResource = {"type": transformer.type_name}
    if transformer.id is not None:
        data["id"] = str(transformer.id)
    if transformer.lid is not None:  # user-provided, so don't assume they didn't put 0
        data["lid"] = str(transformer.lid)

    common_keys = set(transformer.attributes) & set(transformer.relationships)
    if common_keys:
        raise ContentValidationError(
            "Key names cannot be common to both `attributes` and `relationships`: "
            f"{sorted(common_keys)}"
        )

    if transformer.attributes:
        data["attributes"] = deepcopy(transformer.attributes)
    if relationships:
        data["relationships"] = relationships
    return data


def get_relationship_data(
    obj: Union[
        None,
        "JSONAPITransformer",
        List["JSONAPITransformer"],
        Tuple["JSONAPITransformer"],
    ]
) -> Union[None, RelationshipsDict, List[RelationshipsDict]]:
    """
    Convert the passed-in JSONAPITransformer instance or list of instances into JSONAPI
    relationships.

    Args:
        obj: JSONAPITransformer instance, list or tuple of them, or None.

    Returns:
        JSONAPI relationship 'data' dictionary or list of dictionaries, where the dictionary
            has only a 'type' and an 'id' or 'lid' (but not both). Or None. Examples:

            - {"type": "foobar", "id": "36acf528-8308-4520-9e8c-5d44555ba981"}
            - [{"type": "foobar", "lid": "LID-1"}, {"type": "foobar", "lid": "LID-2"}]
            - None
    """
    if obj is None:
        return None

    if isinstance(obj, (list, tuple)):
        return [get_relationship_data(this_obj) for this_obj in obj]  # type: ignore[misc]

    data = {"type": obj.type_name}
    if obj.id is not None:
        data["id"] = str(obj.id)
    elif obj.lid is not None:
        data["lid"] = str(obj.lid)
    return data


def to_includes(transformer: "JSONAPITransformer") -> Iterator["JSONAPITransformer"]:
    """
    Get objects related to this instance, and objects related to those, etc, to use as JSONAPI
    includes.

    Each include is, ahem, included once, no matter how many times it appears on the tree, and is
    only present if it contains keys besides 'type' and 'id' (as those can go in 'relationships').

    Args:
        transformer: A transformer object.

    Returns:
        Iterator of JSONAPITransformers representing related objects and their related objects,
            etc.
    """
    includes = {}
    to_process = deque([transformer])

    while to_process:
        obj = to_process.popleft()

        if obj is None:
            continue

        obj_key = object_key(obj)

        if obj_key in includes:
            # We've already seen this one
            continue

        if not obj.lid and not obj.attributes and not obj.relationships:
            # Does not need to be an include, and contains no relationships to go through.
            continue

        if obj is not transformer:
            # Top-level objects don't go into includes but they do contain relationships.
            includes[obj_key] = obj

        for rel_obj in obj.relationships.values():
            if isinstance(rel_obj, (list, tuple)):
                to_process.extend(rel_obj)
            else:
                to_process.append(rel_obj)

    yield from includes.values()


def eq_helper(
    lhs: "JSONAPITransformer",
    rhs: object,
    seen: MutableSet[Tuple[int, int]],
    cls: Type["JSONAPITransformer"],
) -> bool:
    """
    Helper function to support comparisons of recursive relationships.

    Args:
        lhs: JSONAPITransformer on the left-hand side of the equals sign.
        rhs: Object on the right-hand side of the equals sign.
        seen (set): set of memory ids that have already been processed by the eq helper.
        cls: The class of the object this equality comparison supports.

    Returns:
        Indication whether all values of the JSONAPITransformer are equal to the compared
            object. If ``other`` is not a JSONAPITransformer, `NotImplemented` is returned.
    """
    if not isinstance(rhs, cls):
        return NotImplemented

    # check if the instances have already been compared
    if (object_identifier(lhs), object_identifier(rhs)) in seen:
        return True

    # add the pair that will be compared
    seen.add((object_identifier(lhs), object_identifier(rhs)))

    # the base attributes
    base_case = (
        lhs.type_name == rhs.type_name
        and lhs.id == rhs.id
        and lhs.lid == rhs.lid
        and lhs.attributes == rhs.attributes
    )
    if not base_case:
        return False

    # if relationship keys are different then they are not equal
    if set(lhs.relationships) != set(rhs.relationships):
        return False

    # compare individual keys on the relationship, complicated by the different
    # types that are allowed
    for rel_key, rel_value in lhs.relationships.items():
        other_value = rhs.relationships[rel_key]

        # if it's an instance of the transformer, then it can be compared directly
        if isinstance(rel_value, cls):
            equal = eq_helper(rel_value, other_value, seen, cls)
            if equal is not True:
                return equal
            # look at the next item in the relationships
            continue

        # otherwise comparison will need to be made item by item
        if isinstance(rel_value, (list, tuple)) and isinstance(other_value, (list, tuple)):
            if len(rel_value) != len(other_value):
                return False

            rel_pairs = zip(rel_value, other_value)
            for rel_value_inst, other_value_inst in rel_pairs:
                equal = eq_helper(rel_value_inst, other_value_inst, seen, cls)
                if equal is not True:
                    return equal
            # both sequences are empty or equal, look at the next item in the relationships
            continue

        # None is an allowed value for a relationship
        if rel_value is None:
            return other_value is None

        # other values will not be supported for relationship comparisons
        return NotImplemented

    return True
