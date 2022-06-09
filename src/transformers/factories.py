import itertools
from copy import deepcopy
from typing import TYPE_CHECKING, List, MutableMapping, Optional, Sequence, Type, Union

from transformers.impl import JsonapiDict, factories_impl

if TYPE_CHECKING:
    from transformers.transformers import JSONAPITransformer


class JSONAPITransformerFactory:
    """
    Factory to create JSONAPITransformer instances from a JSONAPI dictionary.

    Note that we assume the JSONAPI dictionary has already passed some sort of basic schema
    validation and has the required members.
    """

    # Implementation note: this factory exists fully so the available transformer_classes can be
    # bound to something. Otherwise these could be classmethods on the JSONAPITransformer.

    def __init__(
        self,
        transformer_classes: Optional[Sequence[Type["JSONAPITransformer"]]] = None,
        allow_generic: bool = False,
    ):
        """
        Initialize the factory with a sequence of transformer classes.

        Each transformer_class should correspond to a different JSONAPI 'type'. You probably only
        need to instantiate this class once per app.

        Args:
            transformer_classes: Iterable of JSONAPITransformer classes.
            allow_generic: Should a generic transformer be used when a matching one is not found?

        Raises:
            ValueError:
            - If no ``transformer_classes`` are provided and ``allow_generic`` is disabled.
            - If more than one transformer of the same ``type_name`` was found.
        """
        if transformer_classes is None:
            transformer_classes = []

        if not transformer_classes and not allow_generic:
            raise ValueError(
                "You must specify transformer_classes and/or set allow_generic to True."
            )

        # prevents duplicate type_name
        transformers_by_type_name = {}
        error_raise = False
        for transformer in transformer_classes:
            if transformer.type_name not in transformers_by_type_name:
                transformers_by_type_name[transformer.type_name] = [transformer.__name__]
            else:
                transformers_by_type_name[transformer.type_name].append(transformer.__name__)
                if not error_raise:
                    error_raise = True
        if error_raise:
            transformers_by_type_name = {
                k: v for k, v in transformers_by_type_name.items() if len(v) > 1
            }
            raise ValueError(
                f"More than one transformer of the same ''type_name'' was found."
                f" Duplicates: {transformers_by_type_name}"
            )

        self._transformers_by_type_name: MutableMapping[str, Type[JSONAPITransformer]] = {
            transformer.type_name: transformer for transformer in transformer_classes
        }

        self.allow_generic = allow_generic
        """
        If a JSONAPI 'type' is found without a corresponding class, should a generic
        ``JSONAPITransformer`` class be used?
        """

    def from_jsonapi(
        self, data_root: JsonapiDict
    ) -> Union["JSONAPITransformer", List["JSONAPITransformer"]]:
        """
        Convert the passed-in JSONAPI dictionary into a JSONAPITransformer instance.

        This is the main entry point for this class, as client code won't typically need to call
        other methods directly. Some light validation is done on the raw data, but it is the
        responsibility of the caller to pass in correct JSONAPI data.

        In the context of this function, and all internally called functions, the following
        definitions are applicable:
            resource/resource_dict - a JSONAPI dictionary object that contains the entirety of
                its content. A resource would thus mean a reference object that has attributes
                and relationships available.
            reference/reference_dict - A JSONAPI relationship object that is referenced by a
                resource object.
            data - JSONAPI resources that are the top level container for the other relationships.
            includes - JSONAPI resources that are referenced by data resources or other included
                resources.

        Args:
            data_root: Dictionary of JSONAPI data, with the keys 'data' and optionally 'included'.
                The data is expected to conform to JSONAPI standards.

        Returns:
            JSONAPITransformer instance(s) representing the passed-in data.

        Raises:
            ContentValidationError: Raised if any of these validations fail:
            - The included items that are in ``data_root.included`` have NOT been matched to any
              relationship from ``data_root``.
            - The relationship items in ``data_root`` WITH local ids (lid) have NOT been matched
              to the included items in ``data_root.include``.
            - Relationship items that have NEITHER ``id`` nor ``lid`` keys.
            - Relationship items that have EITHER ``attributes`` or ``relationships`` keys.
            - Data resources that contain duplicate id/lids.
        """
        data_root = deepcopy(data_root)
        data = data_root["data"]
        includes = list(data_root.get("included", []))
        data_list = list(data if isinstance(data, (list, tuple)) else [data])

        # resource is established to be the combination of data and included dicts
        resources = data_list + includes

        # validation to ensure resource keys are unique
        factories_impl.validate_resource_keys_uniqueness_for_data(resources)

        # create transformers for top level data resources
        data_map = factories_impl.ResourceIdentifierDict()
        for data_item in data_list:
            resource_key = factories_impl.get_resource_key(data_item)
            data_map[resource_key] = factories_impl.get_resource_node(self, data_item)

        # create transformer for included resources
        include_map = factories_impl.ResourceIdentifierDict()
        for include in includes:
            resource_key = factories_impl.get_resource_key(include)
            include_map[resource_key] = factories_impl.get_resource_node(self, include)

        # combine data and included resources into single dictionary of resources
        resource_node_map = factories_impl.ResourceIdentifierDict(
            itertools.chain(data_map.items(), include_map.items())
        )
        # create all relationships for the resources (data + included)
        relationships_map = factories_impl.create_relationships(self, resources, resource_node_map)

        # validations to ensure that relationships and includes are associated correctly
        factories_impl.validate_relationships_for_includes(relationships_map, include_map)
        factories_impl.validate_includes_for_relationships(include_map, relationships_map)

        # create a super dict of all reference-able transformers (resource + relationships)
        reference_map = factories_impl.ResourceIdentifierDict(
            itertools.chain(resource_node_map.items(), relationships_map.items())
        )

        # update the resource nodes with their relationship nodes
        for resource in resources:
            resource_node = resource_node_map[factories_impl.get_resource_key(resource)]
            resource_node_relationships = factories_impl.get_relationship_nodes(
                resource, reference_map
            )
            # Resource nodes can supply their own default relationships. The existing relationship
            # dictionary should only be updated and not replaced.
            resource_node.relationships.update(resource_node_relationships)

        # retrieve the resource node for the top level data items
        data_items = [
            resource_node_map[factories_impl.get_resource_key(data_inst)]
            for data_inst in data_list
        ]

        return data_items if isinstance(data, (list, tuple)) else data_items[0]


def from_jsonapi_generic(
    data_root: JsonapiDict,
) -> Union["JSONAPITransformer", List["JSONAPITransformer"]]:
    """
    Helper method to transform data to generic JSONAPI transformers.

    Args:
        data_root: Dictionary of JSONAPI data, with the keys 'data' and optionally 'included'. The
            data is expected to conform to JSONAPI standards.

    Returns:
        JSONAPITransformer instance(s) representing the passed-in data.
    """
    return JSONAPITransformerFactory(allow_generic=True).from_jsonapi(data_root)
