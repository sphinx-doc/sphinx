"""This module implements a simple JavaScript serializer."""
import json

from sphinx.deprecation import RemovedInSphinx60Warning, deprecated_alias

deprecated_alias(
    'sphinx.util.jsdump',
    {
        'dumps': lambda o, _key: json.dumps(o),
        'dump': json.dump,
        'loads': json.loads,
        'load': json.load,
    },
    RemovedInSphinx60Warning,
    {
        'dumps': 'json.dumps',
        'dump': 'json.dump',
        'loads': 'json.loads',
        'load': 'json.load',
    }
)
