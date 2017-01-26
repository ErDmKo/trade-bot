import json
import yaml
from decimal import Decimal
from datetime import date as dateFormat

def load_config(fname):
    with open(fname, 'rt') as f:
        data = yaml.load(f)
    return data

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj) 
        if isinstance(obj, dateFormat):
            return obj.isoformat()
        return super(DecimalEncoder, self).default(obj)

def dumps(data):
    return json.dumps(data, cls=DecimalEncoder)
