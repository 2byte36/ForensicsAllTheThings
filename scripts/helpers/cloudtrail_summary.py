#!/usr/bin/env python3
"""Summarize a CloudTrail Records-array JSON export; no remote API access."""
import argparse
import json
from _common import cli, read_small


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', help='uncompressed JSON export, at most 64 MiB')
    args = parser.parse_args()
    data = json.loads(read_small(args.input))
    if not isinstance(data, dict) or not isinstance(data.get('Records'), list):
        raise ValueError('expected an object containing a Records array')
    for index, event in enumerate(data['Records']):
        if not isinstance(event, dict):
            raise ValueError(f'record {index} is not an object')
        identity = event.get('userIdentity') or {}
        if not isinstance(identity, dict):
            raise ValueError(f'record {index} has invalid userIdentity')
        print(json.dumps({'index': index, 'time': event.get('eventTime'), 'event_id': event.get('eventID'),
                          'source': event.get('eventSource'), 'action': event.get('eventName'),
                          'identity': identity.get('arn') or identity.get('principalId'),
                          'source_ip': event.get('sourceIPAddress'), 'region': event.get('awsRegion'),
                          'error': event.get('errorCode')}))


if __name__ == '__main__':
    cli(main)
