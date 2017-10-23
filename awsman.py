#!/usr/bin/env python

import sys
import argparse
import boto3
# import datetime
# import os


def cw_list_metrics():
    session = boto3.Session(profile_name="ers-dev", region_name="eu-west-2")
    cw_con = session.client('cloudwatch')
    paginator = cw_con.get_paginator('list_metrics')
    for response in paginator.paginate(Dimensions=[{'Name': 'InstanceId'}],
                                       Namespace='AWS/EC2',
                                       MetricName='CPUCreditBalance'):
        for metric in response['Metrics']:
            print metric['Dimensions']
            # start_time = datetime.date(2017, 10, 01)
            # end_time = datetime.date(2017, 10, 13)
            # response = cw_con.get_metric_statistics(Namespace='AWS/EC2', MetricName='CPUCreditBalance',
            #                                         StartTime=start_time, EndTime=end_time, Period=15)


def cmd_ec2(args):
    print("EC2 Command")
    if args.list:
        do_ec2_list(args.profile, args.region)
        sys.exit(0)


def do_ec2_list(profile, region):
    session = boto3.Session(profile_name=profile, region_name=region)
    ec2_con = session.client('ec2')
    response = ec2_con.describe_instances()
    for reservation in response['Reservations']:
        for i in reservation['Instances']:
            if 'Tags' in i:
                for tag in i['Tags']:
                    if tag['Key'] == 'Name':
                        name = tag['Value']
                        break
                else:
                    name = ""
            print "%s\t\t%s\t\t%s\t\t%s - %s" % (
                i['InstanceId'], i['InstanceType'], i['State']['Name'],
                i['PrivateIpAddress'] if 'PrivateIpAddress' in i else "", name)


def main(arguments):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers()

    parser.add_argument('-r', '--region', help="AWS Region", default="eu-west-2")
    parser.add_argument('-p', '--profile', help="Boto profile name", default="default")

    parser_ec2 = subparsers.add_parser('ec2')
    parser_ec2.add_argument('-l', '--list', action='store_true')
    parser_ec2.set_defaults(func=cmd_ec2)

    args = parser.parse_args(arguments)
    args.func(args)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
