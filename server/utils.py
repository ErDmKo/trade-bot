import json
import yaml
from decimal import Decimal

def load_config(fname):
    with open(fname, 'rt') as f:
        data = yaml.load(f)
    return data

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        print(obj)
        if isinstance(obj, Decimal):
            return str(obj) 
        return super(DecimalEncoder, self).default(obj)

def dumps(data):
    return json.dumps(data, cls=DecimalEncoder)
