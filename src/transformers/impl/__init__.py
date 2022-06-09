from typing import Any, MutableMapping

JsonapiResource = MutableMapping[str, Any]
"""The contents of a JSONAPI object's "data" object."""

AttributesDict = MutableMapping[str, Any]
"""The contents of a JSONAPI object's "attributes" object."""

RelationshipsDict = MutableMapping[str, Any]
"""The contents of a JSONAPI object's "relationships" object."""

JsonapiDict = MutableMapping[str, Any]
"""The full JSONAPI object, including the top-level "data" field."""
