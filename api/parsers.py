import json
from django.http import QueryDict
from rest_framework import parsers

# NOTE: This class is needed to work with auto-generated OpenAPI SDKs.
# It's important to mention that MultiParser from DRF needs from nested
# dotted notation, e.g: location.point.latitude, location.point.longitude
# But most OpenAPI SDKs (like openapi-generator) do not support that.
# They only support nested JSON objects (encoded to string!), e.g:
# location: '{"point": {"latitude": .., "longitude": ..} }'
# This class converts those JSON strings into dotted notation keys.
# If ever need to use bracket notation see: https://github.com/remigermain/nested-multipart-parser/
class MultiPartJsonNestedParser(parsers.MultiPartParser):
    """
    A custom multipart parser that extends MultiPartParser.

    It parses nested JSON strings found in the value of form data fields
    and converts them into dotted notation keys in the QueryDict.
    """
    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the multi-part request data and converts nested JSON to dotted notation.

        Returns a tuple of (QueryDict, MultiValueDict).
        """
        # Call the base parser to get the initial QueryDict (data) and MultiValueDict (files)
        result = super().parse(stream, media_type, parser_context)
        data = result.data
        files = result.files

        # Create a mutable copy of the data QueryDict for modification
        mutable_data = data.copy()
        new_data = {}

        # Iterate over all keys in the QueryDict
        for key, value_list in mutable_data.lists():
            # A value_list from QueryDict is always a list of strings
            
            # 1. Attempt to parse the first value as JSON if it seems like a dictionary
            # We assume non-list values (like 'created_at') are single-element lists.
            # If the list has multiple elements, we treat the field as a list of non-JSON strings
            # and leave it alone (e.g., 'tags': ['tag1', 'tag2']).
            if len(value_list) == 1 and isinstance(value_list[0], str) and value_list[0].strip().startswith('{'):
                try:
                    json_data = json.loads(value_list[0])
                    # 2. Flatten the JSON dictionary into dotted notation
                    flattened = self._flatten_dict(json_data, parent_key=key)
                    # 3. Add the flattened data to our new_data dictionary
                    new_data.update(flattened)
                    
                    # Remove the original key as it's been expanded
                    # This is implicitly done by building new_data, but for clarity:
                    # mutable_data.pop(key) 

                except json.JSONDecodeError:
                    # Not valid JSON, treat it as a regular string field
                    new_data[key] = value_list

            else:
                # Field is not a single JSON string, e.g., 'note': [''] or 'tags': ['tag1', 'tag2']
                # Keep the original data intact
                new_data[key] = value_list

        # Convert the resulting dictionary back into a QueryDict
        # We need to construct it carefully as QueryDict expects lists of values
        final_data = QueryDict('', mutable=True)
        for k, v in new_data.items():
            # v will be either a list (from original data) or a single value (from flattened json)
            if isinstance(v, list):
                final_data.setlist(k, v)
            else:
                final_data[k] = v

        return parsers.DataAndFiles(final_data, files)

    def _flatten_dict(self, d, parent_key='', sep='.'):
        """
        Recursively flattens a nested dictionary into a single-level dictionary
        with dotted keys.
        """
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, dict):
                # Recurse into nested dictionaries
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Handle lists by keeping the key and setting the value as the list
                # This is a simplification; a more complex parser might flatten lists too.
                items.append((new_key, v))
            else:
                # Add simple key-value pair
                items.append((new_key, v))
        
        # When converting back to QueryDict, simple values (not lists) should be
        # left as single values for the QueryDict to handle correctly.
        final_flat_dict = {}
        for k, v in items:
            # Important: QueryDict expects lists for multi-value fields. 
            # If the value is a list (from the JSON), keep it as a list.
            if isinstance(v, list):
                final_flat_dict[k] = v
            else:
                # For single values (str, int, float, bool, None), QueryDict will 
                # automatically wrap it in a list upon assignment.
                # However, for consistency with how QueryDict works in general, we 
                # store the single value.
                final_flat_dict[k] = str(v) # Convert to string for form data

        return final_flat_dict