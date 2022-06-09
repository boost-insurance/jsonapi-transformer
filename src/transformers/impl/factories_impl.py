"""
The entirety of this file should be considered private implementation details for the public-facing
factories.py.
"""

from collections import UserDict, defaultdict
from typing import (
    TYPE_CHECKING,
    Any,
    Iterable,
    Iterator,
    List,
    MutableMapping,
    Optional,
    Tuple,
    Type,
    Union,
)

from transformers.exceptions import ContentValidationError
from transformers.impl import JsonapiResource
from transformers.transformers import JSONAPITransformer

if TYPE_CHECKING:
    from transformers.factories import JSONAPITransformerFactory


ResourceKey = Tuple[str, Optional[str], Optional[str]]
"""
The type of the key used by `ResourceIdentifierDict`. Tuple items represent
    * type_name
    * id
    * lid
"""


if TYPE_CHECKING:
    ResourceIdentifierDictBase = UserDict[ResourceKey, JSONAPITransformer]
else:
    # Compatibility with Python <= 3.8
    ResourceIdentifierDictBase = UserDict


class ResourceIdentifierDict(ResourceIdentifierDictBase):
    """
    Dictionary override to encompass logic for fetching and setting values to identify a JSONAPI
    resource or relationship.

    The dictionary will attempt to use the given key or its derivative key
    `(key[type], key[id], None)` as the identifier for the value item.
    """

    _InitialData = Union[MutableMapping[ResourceKey, JSONAPITransformer], Iterable]
    """The type of the initial data."""

    def __init__(self, initialdata: Optional[_InitialData] = None, **kwargs: Any):
        super().__init__(initialdata, **kwargs)

    def __setitem__(self, key: ResourceKey, value: JSONAPITransformer) -> None:
        """
        Sets the item in the dictionary.

        If both the id and the lid are specified in the resource key, then just use the id as the
        main identifier for the resource.

        Args:
            key: The key for the resource item.
            value: The transformer to be associated with the key.
        """
        type_name, id_, lid = key
        if id_ is not None and lid is not None:
            super().__setitem__((type_name, id_, None), value)
        else:
            super().__setitem__(key, value)

    def __getitem__(self, key: ResourceKey) -> JSONAPITransformer:
        """
        Retrieves the JSONAPITransformer associated with the `key` or attempt to use the derivative
        key to fetch the resource instance.

        Args:
            key: The key for the resource item.

        Returns:
            The transformer.

        Raises:
            KeyError: If the given resource key, or the derivative key isn't found.
        """
        type_name, id_, lid = key

        if id_ is not None and lid is not None:
            return super().__getitem__((type_name, id_, None))
        else:
            return super().__getitem__(key)

    def __contains__(self, key: object) -> bool:
        """
        Checks to see if the key exists in the container.

        Args:
            key: The key for the resource item.

        Returns:
            Whether the key or its derivative key is found in the container.
        """
        if not isinstance(key, Iterable):
            return False
        try:
            type_name, id_, lid = key
        except ValueError:
            return False

        if id_ is not None and lid is not None:
            return super().__contains__((type_name, id_, None))
        else:
            return super().__contains__(key)


def get_class_for_type(
    factory: "JSONAPITransformerFactory",
    type_name: str,
) -> Type[JSONAPITransformer]:
    """
    Returns the JSONAPITransformer class corresponding to the given JSONAPI 'type'.

    Args:
        factory: Factory for instantiating transformers by their JSONAPI `type`.
        type_name: Value of JSONAPI 'type' field.

    Raises:
        ValueError: If there is no corresponding class for the given type and
            ``factory.allow_generic`` is ``False``.

    Returns:
        JSONAPITransformer subclass
    """
    try:
        return factory._transformers_by_type_name[type_name]
    except KeyError as error:
        if factory.allow_generic:
            return JSONAPITransformer
        raise ValueError(f"No known transformers for type {type_name}") from error


def validate_resource_keys_uniqueness_for_data(resources: Iterable[JsonapiResource]) -> None:
    """
    Validate that the data key has no duplicate resource ids.

    Args:
        resources: List of resources (data + includes).

    Raises:
        ContentValidationError: If there are duplicate resource ids.
    """
    resource_keys_count_map: MutableMapping[Tuple[Any, Any, str], int] = defaultdict(int)

    for resource in resources:
        if "id" in resource:
            key = (resource["type"], resource["id"], "id")
            resource_keys_count_map[key] += 1
        if "lid" in resource:
            key = (resource["type"], resource["lid"], "lid")
            resource_keys_count_map[key] += 1

    duplicate_resources = (k for k, _count in resource_keys_count_map.items() if _count > 1)
    error_message = "Resource {resource_type} has duplicate {key_type}: {key}."
    errors = [
        error_message.format(resource_type=resource_type, key_type=key_type, key=str(key))
        for resource_type, key, key_type in duplicate_resources
    ]
    if errors:
        raise ContentValidationError(errors)


def validate_relationships_for_includes(
    relationships_map: ResourceIdentifierDict,
    includes_map: ResourceIdentifierDict,
) -> None:
    """
    Validate that the included resources have a matching relationship that references it.

    Args:
        relationships_map: Dictionary of relationships.
        includes_map: Dictionary of included resources.

    Raises:
        ContentValidationError: If any expected relationships are missing.
    """
    includes_without_references = []
    for resource_key in includes_map:
        if resource_key not in relationships_map:
            includes_without_references.append(resource_key)

    if includes_without_references:
        missing_relationships = sorted(type_ for type_, _, _ in includes_without_references)
        missing_types = ", ".join(missing_relationships)
        raise ContentValidationError(
            f"Missing matching relationship for these included items: {missing_types}"
        )


def validate_includes_for_relationships(
    includes_map: ResourceIdentifierDict,
    relationships_map: ResourceIdentifierDict,
) -> None:
    """
    Validate that relationships with `lid`s each have an include that contains additional data.

    Args:
        includes_map: Dictionary of included resources.
        relationships_map: Dictionary of relationships.

    Raises:
        ContentValidationError: If any expected includes are missing.
    """
    missing_include_lids = []
    for resource_key in relationships_map:
        _type_name, _id, lid = resource_key
        if lid is not None and resource_key not in includes_map:
            missing_include_lids.append(lid)

    if missing_include_lids:
        missing_lids_str = ", ".join(sorted(missing_include_lids))
        raise ContentValidationError(
            f"Missing matching include for relationship in data.relationships: {missing_lids_str}"
        )


def get_resource_key(resource: JsonapiResource) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Return the identifier to be associated with the resource. The `id` and `lid` of the key will be
    converted to strings if they are not ``None``.

    Args:
        resource: Dictionary with key `type` and optionally `id` and `lid`.

    Returns:
        Tuple containing the resource's `type`, `id`, and `lid`.
    """
    res_id = resource.get("id")
    res_lid = resource.get("lid")

    if res_id is not None:
        res_id = str(res_id)
    if res_lid is not None:
        res_lid = str(res_lid)

    return resource["type"], res_id, res_lid


def iter_relationships(
    resource: JsonapiResource,
) -> Iterator[JsonapiResource]:
    """
    Recursively iterate the relationships of the resource using a depth first traversal method.

    Args:
        resource: Resource dictionary containing relationships.

    Yields:
        Resource reference in the resource's relationships.
    """
    for relation in resource.get("relationships", {}).values():
        if relation is None or relation["data"] is None:
            continue

        # yield the resource and all sub resource for the relationship
        if isinstance(relation["data"], (list, tuple)):
            for item in relation["data"]:
                yield item
                yield from iter_relationships(item)
        else:
            yield relation["data"]
            yield from iter_relationships(relation["data"])


def get_resource_node(
    factory: "JSONAPITransformerFactory",
    resource: JsonapiResource,
) -> JSONAPITransformer:
    """
    For all resources in the raw data, return transformer instance using the type, id, lid
    as the identifier.

    Args:
        factory: Factory for instantiating transformers by their JSONAPI `type`.
        resource: Dictionary containing resource data.

    Returns:
        JSONAPITransformer instantiated with the resource's data.
    """
    r_type, r_id, r_lid = get_resource_key(resource)
    resource_class = get_class_for_type(factory, r_type)
    return resource_class(
        type_name=r_type,
        id=r_id,
        lid=r_lid,
        attributes=resource.get("attributes", {}),
        relationships=resource.get("relationships", {}),
    )


def create_relationships(
    factory: "JSONAPITransformerFactory",
    resources: Iterable[JsonapiResource],
    resource_node_map: ResourceIdentifierDict,
) -> ResourceIdentifierDict:
    """
    Create a new relationship transformer instance or assign an existing relationship transformer
    for all provided resources.

    Args:
        factory: Factory for instantiating transformers by their JSONAPI `type`.
        resources: Iterable containing resource data.
        resource_node_map: Mapping of the resource key to the JSONAPITransformer that it is
            associated with.

    Returns:
        Mapping of all the relationship transformers that have been associated with the resources.

    Raises:
        ContentValidationError if the relationship:
            - contains NEITHER `id` nor `lid` key
            - contains EITHER `attributes` or `relationships` key
    """
    relationships_map = ResourceIdentifierDict()
    for resource in resources:
        for ref_relation in iter_relationships(resource):
            resource_key = (res_type, res_id, res_lid) = get_resource_key(ref_relation)
            if res_id is None and res_lid is None:
                raise ContentValidationError(
                    f"Relationship for type '{res_type}' must contain either 'id' or 'lid'"
                )
            if "attributes" in ref_relation:
                raise ContentValidationError(
                    f"Relationship '{res_type}' cannot contain the key 'attributes'"
                )
            if "relationships" in ref_relation:
                raise ContentValidationError(
                    f"Relationship '{res_type}' cannot contain the key 'relationships'"
                )
            # fetch or create transformer to be associated with the reference resource
            if resource_key in resource_node_map:
                relationships_map[resource_key] = resource_node_map[resource_key]
            else:
                relationships_map[resource_key] = get_resource_node(factory, ref_relation)

    return relationships_map


def get_relationship_nodes(
    resource: JsonapiResource,
    resource_node_map: ResourceIdentifierDict,
) -> MutableMapping[str, Optional[Union[JSONAPITransformer, List[JSONAPITransformer]]]]:
    """
    For the given resource, retrieve its relationship nodes from the `resource_node_map`.

    Args:
        resource: Dictionary containing resource data.
        resource_node_map: Mapping of the resource key to the JSONAPITransformer that it is
            associated with.

    Returns:
        Mapping of the relationship key to the resource node found in `resource_node_map`.
    """
    if TYPE_CHECKING:
        resource_relation_value: Optional[
            Union[JSONAPITransformer, List[JSONAPITransformer]]
        ] = None

    resource_relationships = {}
    for relation_key, relation_value in resource.get("relationships", {}).items():
        if relation_value is None or relation_value["data"] is None:
            # if the relation is empty
            resource_relation_value = None

        elif isinstance(relation_value["data"], (list, tuple)):
            # fetch each of the related nodes from the resource node map
            related_nodes = [
                resource_node_map[get_resource_key(item)] for item in relation_value["data"]
            ]
            resource_relation_value = related_nodes

        else:
            # directly retrieve the related node from the resource node map
            related_node = resource_node_map[get_resource_key(relation_value["data"])]
            resource_relation_value = related_node

        resource_relationships[relation_key] = resource_relation_value

    return resource_relationships
