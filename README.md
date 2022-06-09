# jsonapi-transformer

**jsonapi-transformer** is a Python library for producing, consuming, and manipulating JSON:API data. It makes developing with JSON:API more manageable by converting from and to JSON:API-formatted data.

This library follows the [JSON:API v1.1 **release candidate** specification](https://jsonapi.org/format/1.1/).

# Quick Start
The following example is based on [Example 7.2.2.4](https://jsonapi.org/format/1.1/#document-resource-object-linkage) of the JSON:API v1.1 specification.
```python
import json
from transformers import JSONAPITransformer, from_jsonapi_generic
```

Data can be manually set on a `JSONAPITransformer` instance...

```python
transformer = JSONAPITransformer(
    type_name="articles",
    id="1",
    attributes={
        "title": "Rails is Omakase",
    },
    relationships={
        "author": JSONAPITransformer(
            type_name="people",
            id="9",
        )
    }
)
```
... and then converted to jsonapi.
```python
>>> jsonapi = transformer.to_jsonapi()
>>> print(json.dumps(jsonapi, indent=4))
{
    "data": {
        "type": "articles",
        "id": "1",
        "attributes": {
            "title": "Rails is Omakase"
        },
        "relationships": {
            "author": {
                "data": {
                    "type": "people",
                    "id": "9"
                }
            }
        }
    }
}
```
If you already have jsonapi data, you can load that into a `JSONAPITransformer` instance as well.
```python
>>> transformer = from_jsonapi_generic(jsonapi)
>>> print(transformer.id)
1

>>> print(transformer.type_name)
articles
```

# Installation
**jsonapi-transformer** is available on PyPI.
```shell
pip install --upgrade pip
pip install jsonapi-transformer
```
**jsonapi-transformer** supports Python 3.7+.

# Notable Features
Code snippets in this section use the Quick Start example above as a starting point.

1. Support for both `id` and `lid`.
2. The `included` list is generated automatically from items in `relationships` when `to_jsonapi()` is called -- there's no need to manipulate an item in both the `included` list *and* an object's `relationships`.
3. Convenience method to *get* an `attribute` or `relationship` or a default if the key is not found.
    ```python
    # First, try `transformer.attributes["greeting"]` -- greeting is not found!
    # Next, try `transformer.relationships["greeting"]` -- greeting is not found!
    # Finally, the default is returned.
    >>> default = "hello"
    >>> greeting = transformer.get("greeting", default)
    >>> print(greeting)
    hello
    ```
4. Convenience accessor for *getting* `attributes` and `relationships` using `[]` notation.
    ```python
    # First, try `transformer.attributes["title"]` -- title is found!
    >>> print(transformer["title"])
    Rails is Omakase

    # First, try `transformer.attributes["author"]` -- author is not found!
    # Next, try `transformer.relationships["author"]` -- author is found!
    >>> author = transformer["author"]
    >>> print(author.to_jsonapi())
    {"data": {"type": "people", "id": "9"}}
    ```
5. Convenience accessor for *setting* `attributes` using `[]` notation.
    ```python
    >>> transformer["my_new_attribute"] = "hello"
    ```
6. Convenience accessor for *deleting* `attributes` using `[]` notation.
    ```python
    >>> del transformer["my_new_attribute"]
    ```
7. Convenience accessor for *contains* in `attributes` and `relationships` using the `in` keyword.
    ```python
    >>> "title" in transformer
    True

    >>> "author" in transformer
    True

    >>> "book" in transformer
    False
    ```
8. Deep equality test between transformers, comparing all of:
    * `type_name`
    * `id`
    * `lid`
    * `attributes`
    * `relationships`
    * `included`
    ```python
    >>> book = JSONAPITransformer(type_name="book", id="1")
    >>> article = JSONAPITransformer(type_name="article", id="1")
    >>> book == article
    False
    ```
9. Derived transformer classes can contain business logic.
    ```python
    from transformers import JSONAPITransformer, JSONAPITransformerFactory


    class People(JSONAPITransformer):
        type_name = "people"

        @property
        def full_name(self):
            """Custom business logic for this class, keyed on `type_name`."""
            return f"{self['last_name'], self['first_name']}"


    jsonapi = {
        "data": {
            "type": "articles",
            "id": "1",
            "attributes": {
                "title": "Rails is Omakase"
            },
            "relationships": {
                "author": {
                    "data": {
                        "type": "people",
                        "id": "9"
                    }
                }
            }
        },
        "included": [
            {
                "type": "people",
                "id": "9",
                "attributes": {
                    "first_name": "Jon",
                    "last_name": "George"
                }
            }
        ]
    }

    # By using a factory instead of `from_jsonapi_generic(...)`, we can provide a list
    # of classes that are instantiated based on the `type` field in the jsonapi data.
    # Since we didn't provide a class for the "articles" type, setting `allow_generic`
    # to True allows the "articles" object to load as a generic JSONAPITransformer
    factory = JSONAPITransformerFactory([People], allow_generic=True)
    ```
    ```python
    >>> transformer = factory.from_jsonapi(jsonapi)
    >>> print(type(transformer))
    <class 'JSONAPITransformer'>

    >>> author = transformer["author"]
    >>> print(type(author))
    <class 'People'>

    # Access business logic unique to the `People` class.
    >>> print(author.full_name)
    George, Jon
    ```
10. Lists of JSON:API objects can reside in the same document, and any shared relationships are de-duplicated in the `included` list.
    ```python
    from transformers import JSONAPIListTransformer, JSONAPITransformer, from_jsonapi_generic


    article1 = JSONAPITransformer(
        type_name="articles",
        id="1",
        attributes={
            "title": "Rails is Omakase",
        },
        relationships={
            "author": JSONAPITransformer(
                type_name="people",
                id="9",
                attributes={
                    "first_name": "Jon",
                    "last_name": "George"
                }
            )
        }
    )

    article2 = JSONAPITransformer(
        type_name="articles",
        id="2",
        attributes={
            "title": "Now is better than never.",
        },
        relationships={
            "author": JSONAPITransformer(
                type_name="people",
                id="9",
                attributes={
                    "first_name": "Jon",
                    "last_name": "George"
                }
            )
        }
    )
    ```
    ```python
    >>> transformer = JSONAPIListTransformer([article1, article2])
    >>> print(type(transformer))
    <class 'JSONAPIListTransformer'>

    # The `included` section is deduplicated.
    >>> jsonapi = transformer.to_jsonapi()
    >>> print(json.dumps(jsonapi, indent=4))
    {
        "data": [
            {
                "type": "articles",
                "id": "1",
                "attributes": {
                    "title": "Rails is Omakase"
                },
                "relationships": {
                    "author": {
                        "data": {
                            "type": "people",
                            "id": "9"
                        }
                    }
                }
            },
            {
                "type": "articles",
                "id": "2",
                "attributes": {
                    "title": "Now is better than never."
                },
                "relationships": {
                    "author": {
                        "data": {
                            "type": "people",
                            "id": "9"
                        }
                    }
                }
            }
        ],
        "included": [
            {
                "type": "people",
                "id": "9",
                "attributes": {
                    "first_name": "Jon",
                    "last_name": "George"
                }
            }
        ]
    }

    # Convert back to transformers.
    >>> transformers = from_jsonapi_generic(jsonapi)
    >>> print(type(transformers))
    <class 'list'>

    >>> for x in transformers:
    ...     print(type(x))
    <class 'JSONAPITransformer'>
    <class 'JSONAPITransformer'>
    ```


# Unsupported
These [top-level members](https://jsonapi.org/format/1.1/#document-top-level) of the JSON:API specification are unsupported:
* `errors`
* `jsonapi`
* `links`
* `meta`


# Development Locally
Contributors to **jsonapi-transformer** can install an editable version of this library after cloning the repository:

```shell
pip install --upgrade pip
pip install -e .[tests,dev]
```

# Development with Docker
Contributors to **jsonapi-transformer** can do all development tasks within a Docker container:

### Build
Don't forget the trailing `.`!!!
```shell
docker build -f Dockerfile.testing \
    --build-arg PYTHON_VERSION=3.10 \
    -t jsonapi-transformer:latest \
    .
```

### Run Tests with Coverage
```shell
docker run --rm -it \
    --entrypoint pytest \
    jsonapi-transformer:latest \
    --cov --cov-report=term-missing
```

### Run Type Checking
```shell
docker run --rm -it \
    --entrypoint mypy \
    jsonapi-transformer:latest \
    --show-error-context \
    --show-error-codes \
    --strict \
    src
```
