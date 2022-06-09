"""
JSONAPI serialization and deserialization library.
The implementation of the serialization and deserialization follows the specification indicated on
https://jsonapi.org/format/1.1/.
"""

import reprlib
from typing import Any, List, MutableMapping, Optional, Sequence

from transformers.exceptions import ContentValidationError
from transformers.impl import AttributesDict, JsonapiDict, RelationshipsDict, transformers_impl


class JSONAPITransformer:
    """
    Class to represent, work with, serialize and deserialize data.

    Can be used to represent any object. Attributes, relationships, ids, and local ids are tracked.
    Makes no assumptions about the nature of the data.
    """

    type_name: str = None  # type: ignore[assignment]
    """
    String representing the object's type.
        * Should match the JSONAPI 'type' field.
        * Should be unique and constant for each class.

    This value is normally either set in the definition of a derived class, or passed in at object
    instantiation.
    """

    def __init__(
        self,
        type_name: Optional[str] = None,
        id: Optional[str] = None,
        lid: Optional[str] = None,
        attributes: Optional[AttributesDict] = None,
        relationships: Optional[RelationshipsDict] = None,
    ):
        """
        Instantiate the class with the given data, using the class's default attributes and
        relationships for any data not given.

        All passed-in values correspond to public attributes on the initialized instance.
        See class Attributes documentation for more information.

        Args:
            type_name: String representing the object's type. Required if not defined on subclass.
            id: Persistant unique id.
            lid: Temporary "local" id.
            attributes: Dictionary of direct attributes.
            relationships: Dictionary of JSONAPITransformer subclasses or lists/tuples thereof.

        Raises:
            ValueError: if ``type_name`` not defined on this class or provided on init.
        """
        if attributes is None:
            attributes = {}
        if relationships is None:
            relationships = {}

        if type_name is not None:
            if self.type_name is None:
                self.type_name = type_name
            elif type_name != self.type_name:
                raise ValueError(f"Cannot override type name {self.type_name} defined on class.")

        if self.type_name is None:
            raise ValueError("type_name must be passed on init or defined as subclass attribute.")

        if not isinstance(self.type_name, str):
            raise ContentValidationError("`type_name` must be a string.")

        self.id: Optional[str] = id
        """Persistent unique id."""

        self.lid: Optional[str] = lid
        """Temporary "local" id."""

        self.attributes: AttributesDict = dict(attributes)
        """
        Dictionary of direct attributes. Values are not restricted. As a shortcut, items can be
        directly retrieved, added to, and removed from this dictionary by operating directly on the
        class instance.
        """

        self.relationships: RelationshipsDict = dict(relationships)
        """
        Dictionary of related objects. The values of this dictionary must be JSONAPITransformer
        subclasses or lists or tuples of them. As a shortcut, items can be retrieved from this
        dictionary (but not set or removed) by operating directly on the class instance. (Note that
        if the same key exists in ``self.attributes`` and ``self.relationships``, the
        ``self.attributes`` version will be returned.)
        """

    @classmethod
    def get_defaults_for_optional_attributes(cls) -> AttributesDict:
        """
        Get a dictionary of default attributes for this class. By default, this is empty.

        In order to make it impossible to accidentally change the class defaults, this is a method
        instead of a class variable.

        Returns:
            Default attributes.
        """
        return {}

    @classmethod
    def get_defaults_for_optional_relationships(cls) -> RelationshipsDict:
        """
        Get a dictionary of default relationships for this class. By default, this is empty.

        In order to make it impossible to accidentally change the class defaults, this is a method
        instead of a class variable.

        Returns:
            Default relationships.
        """
        return {}

    def apply_defaults(self) -> None:
        """
        Apply defaults to this transformer and all of its relationships, and their relationships,
        etc.

        Defaults are defined by `get_defaults_for_optional_attributes` and
        `get_defaults_for_optional_attributes` on each transformer.
        """
        for transformer in transformers_impl.iter_transformer_and_relationships_recursively(self):
            transformers_impl.apply_defaults_non_recursively(transformer)

    def to_jsonapi(self) -> JsonapiDict:
        """
        Convert this instance and its related instances into JSONAPI-formatted data.

        This is the opposite of ``JSONAPITransformerFactory.from_jsonapi``. Adds related items into
        an 'included' section, when necessary.

        Returns:
            A dict with 'data' and possibly 'included' attributes representing this instance.
        """

        data_root: JsonapiDict = {"data": transformers_impl.to_jsonapi_data(self)}

        includes = transformers_impl.to_includes(self)
        included = [transformers_impl.to_jsonapi_data(include) for include in includes]
        if included:
            data_root["included"] = included

        return data_root

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Get a value from this instance's ``attributes`` or ``relationships``.

        Args:
            key: Key to look for.
            default: Value to return if key is not found.

        Returns:
            Value of key in instance's attributes (checked first) or relationships, or default if
            neither exists.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key: str) -> Optional[Any]:
        """
        Shortcut for accessing this instance's ``attributes`` or ``relationships`` with
        ``self[key]``.

        Raises:
            KeyError: If key is not found in self.attributes or self.relationships.
            ContentValidationError: If key is in both attributes and relationships.

        Returns:
            Value of key in instance's attributes (checked first) or relationships.
        """
        if key in self.attributes and key in self.relationships:
            # This is not ideal. Ideally we'd prevent this from happening on
            #    * self.`__setitem__`
            #    * `attributes.__setitem__`
            #    * `relationships.__setitem__`
            raise ContentValidationError(
                f"Key `{key}` must not be in both attributes and relationships."
            )

        if key in self.attributes:
            return self.attributes[key]
        if key in self.relationships:
            return self.relationships[key]
        __tracebackhide__ = True  # Seeing this function in the main traceback is counterproductive
        raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set a value on this instance's attributes dictionary with
        ``this_object[key] = 'my_value'``.

        Args:
            key: Key to set value on.
            value: Value to set.

        Raises:
            ContentValidationError: If key already exists as a relationship.
        """
        if key in self.relationships:
            raise ContentValidationError(
                f"Cannot add `{key}` to attributes, it is already a relationship."
            )

        self.attributes[key] = value

    def __delitem__(self, key: str) -> None:
        """
        Delete a key and its value from this instance's ``attributes``.

        Args:
            key: Key to remove.

        Raises:
            KeyError: If key is not found in self.attributes.
            ValueError: If key is not found in self.attributes but is found in self.relationships,
                as a warning that keys cannot be deleted from self.relationships using this method.
        """
        try:
            del self.attributes[key]
        except KeyError:
            if key in self.relationships:
                raise ValueError(
                    "Direct item deletion only available for attributes. "
                    f"Try `del {self.__class__.__name__}.relationships['{key}']`."
                )
            raise

    def __contains__(self, key: str) -> bool:
        """
        Check to see if a value is ``in`` this instance's ``attributes`` or ``relationships``.

        Returns:
            Indication whether key was found.
        """
        try:
            _ = self[key]
            return True
        except KeyError:
            return False

    def __eq__(self, other: object) -> bool:
        """
        Equality check for JSONAPITransformer instances.

        Args:
            other: The other object instance we're comparing ``self`` against.

        Returns:
            Indication whether all values of the JSONAPITransformer are equal to the compared
            object.
        """
        return transformers_impl.eq_helper(self, other, set(), JSONAPITransformer)

    @reprlib.recursive_repr()
    def __repr__(self) -> str:
        """
        Python representation of this object.

        Returns:
            Python representation of this object.
        """
        attributes = dict(sorted((key, value) for key, value in self.attributes.items()))
        relationships = dict(sorted((key, value) for key, value in self.relationships.items()))
        return (
            f"{self.__class__.__name__}(type_name={self.type_name!r}, "
            f"id={self.id!r}, lid={self.lid!r}, attributes={attributes!r}, "
            f"relationships={relationships!r})"
        )

    @reprlib.recursive_repr()
    def __rich_repr__(self) -> "rich.repr.Result":  # type: ignore[name-defined]  # NOQA: F821
        """
        Pretty representation for the Rich library.

        Returns:
            Pretty representation for the Rich library.
        """
        attributes = dict(sorted((key, value) for key, value in self.attributes.items()))
        relationships = dict(sorted((key, value) for key, value in self.relationships.items()))
        yield "type_name", self.type_name
        yield "id", self.id
        yield "lid", self.lid
        yield "attributes", attributes
        yield "relationships", relationships


class JSONAPIListTransformer:
    """Class that provides conversion of a sequence of JSONAPITransformers into JSONAPI."""

    def __init__(self, transformers: Sequence[JSONAPITransformer]):
        """
        Initialize this instance with the provided transformers.

        Args:
            transformers: Transformers to be converted.
        """

        self.transformers: Sequence[JSONAPITransformer] = transformers
        """Transformers to be converted."""

    def to_jsonapi(self) -> JsonapiDict:
        """
        Convert transformers into JSONAPI, resulting in a list of data elements and includes.

        Returns:
            JSONAPI dictionary with JSONAPI `data` list and includes (if needed).
        """
        jsonapi_data: MutableMapping[str, List[JsonapiDict]] = {"data": []}
        jsonapi_included = []
        included_keys = set()

        # Convert each transformer to a JSONAPI dictionary
        for transformer in self.transformers:
            result = transformer.to_jsonapi()
            jsonapi_data["data"].append(result["data"])

            # Process the includes that this transformer may have generated. Only add to included
            # set if it does not already exist.
            if "included" in result:
                for include in result["included"]:
                    key = (include.get("type"), include.get("id"), include.get("lid"))
                    if key in included_keys:
                        continue
                    included_keys.add(key)
                    jsonapi_included.append(include)

        if jsonapi_included:
            jsonapi_data["included"] = jsonapi_included

        return jsonapi_data
