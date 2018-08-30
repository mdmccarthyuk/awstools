#!/usr/bin/env python3

import boto3
import sys
import argparse


def ec2_info(profile, region, instance_id):
    # If the profile is set to null ignore it.  Allows ec2 instance role to be used without
    # throwing an error.
    if profile is not 'null':
      s = boto3.Session(profile_name=profile, region_name=region)
    else:
      s = boto3.Session(region_name=region)
    c = s.client('ec2')
    res = c.describe_instances(
        Filters=[
            {
                'Name': 'instance-id',
                'Values': [
                    instance_id
                ]
            }
        ]
    )
    for r in res['Reservations']:
        for i in r['Instances']:
            name = "None"
            for tag in i['Tags']:
                if tag['Key'] == 'Name':
                    name = tag['Value']
            print(i['PrivateIpAddress'], name)


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--region', default='eu-west-2')
    parser.add_argument('-p', '--profile', default='null')
    parser.add_argument('-a', '--action', choices=['info'], default='info')
    parser.add_argument('-i', '--id', required=True)
    pargs = parser.parse_args(args)
    if pargs.action == 'info':
        ec2_info(pargs.profile, pargs.region, pargs.id)
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

