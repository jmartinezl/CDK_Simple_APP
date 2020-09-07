import json
from datetime import datetime
import pytz

def handler(event, context):

    # getting utc timezone
    utc_time = pytz.utc
    print('request: {}'.format(json.dumps(event)))
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/plain'
        },
        'body': 'Datetime of UTC Time-zone: ' + datetime.now(tz=utc_time).strftime("%Y/%m/%d, %H:%M:%S")
    }
