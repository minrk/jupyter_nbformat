from __future__ import print_function
import json
import os

from IPython.external.jsonschema import Draft3Validator, SchemaError
import IPython.external.jsonpointer as jsonpointer
from IPython.utils.py3compat import iteritems


from .current import nbformat, nbformat_schema
schema_path = os.path.join(
    os.path.dirname(__file__), "v%d" % nbformat, nbformat_schema)


def isvalid(nbjson, verbose=False):
    """Checks whether the given notebook JSON conforms to the current
    notebook format schema. Returns True if the JSON is valid, and
    False otherwise.

    If `verbose` is set, then print out each error that is detected.

    """

    errors = validate(nbjson, verbose=verbose)
    return errors == 0


def validate(nbjson, verbose=False):
    """Checks whether the given notebook JSON conforms to the current
    notebook format schema, and returns the number of errors.

    If `verbose` is set, then print out each error that is detected.

    """

    # load the schema file
    with open(schema_path, 'r') as fh:
        schema_json = json.load(fh)

    # resolve internal references
    v3schema = resolve_ref(schema_json)
    v3schema = jsonpointer.resolve_pointer(v3schema, '/notebook')

    # count how many errors there are
    errors = 0
    v = Draft3Validator(v3schema)
    for error in v.iter_errors(nbjson):
        errors = errors + 1
        if verbose:
            print(error)

    return errors


def resolve_ref(json, schema=None):
    """Resolve internal references within the given JSON. This essentially
    means that dictionaries of this form:

    {"$ref": "/somepointer"}

    will be replaced with the resolved reference to `/somepointer`.
    This only supports local reference to the same JSON file.

    """

    if not schema:
        schema = json

    # if it's a list, resolve references for each item in the list
    if type(json) is list:
        resolved = []
        for item in json:
            resolved.append(resolve_ref(item, schema=schema))

    # if it's a dictionary, resolve references for each item in the
    # dictionary
    elif type(json) is dict:
        resolved = {}
        for key, ref in iteritems(json):

            # if the key is equal to $ref, then replace the entire
            # dictionary with the resolved value
            if key == '$ref':
                if len(json) != 1:
                    raise SchemaError(
                        "objects containing a $ref should only have one item")
                pointer = jsonpointer.resolve_pointer(schema, ref)
                resolved = resolve_ref(pointer, schema=schema)

            else:
                resolved[key] = resolve_ref(ref, schema=schema)

    # otherwise it's a normal object, so just return it
    else:
        resolved = json

    return resolved
