#!/usr/bin/env python2.7

import sys
import argparse
import boto3
# import datetime
# import os


def cmd_cw(args):
    print("CW Command")
    if args.action == 'list':
        do_cw_list_metrics(args.profile, args.region)
        sys.exit(0)


def cmd_ec2(args):
    print("EC2 Command")
    if args.action == 'list':
        do_ec2_list(args.profile, args.region)
        sys.exit(0)
    if args.action == 'spotlist':
        do_ec2_spot_list(args.profile, args.region)
        sys.exit(0)


def cmd_sg(args):
    print("SG Command")
    if args.action == 'show':
        do_sg_show(args.profile, args.region, args.id)
        sys.exit(0)
    if args.action == 'list':
        do_sg_list(args.profile, args.region)
        sys.exit(0)


def cmd_ami(args):
    print("AMI Command")
    if args.action == 'list':
        do_ami_list(args.profile, args.region, args.id)
        sys.exit(0)


def do_cw_list_metrics(profile, region):
    session = boto3.Session(profile_name=profile, region_name=region)
    cw_con = session.client('cloudwatch')
    paginator = cw_con.get_paginator('list_metrics')
    for response in paginator.paginate(Dimensions=[{'Name': 'InstanceId'}],
                                       Namespace='AWS/EC2'):
        for metric in response['Metrics']:
            print(metric['Dimensions'])
            # start_time = datetime.date(2017, 10, 01)
            # end_time = datetime.date(2017, 10, 13)
            # response = cw_con.get_metric_statistics(Namespace='AWS/EC2', MetricName='CPUCreditBalance',
            #                                         StartTime=start_time, EndTime=end_time, Period=15)


def do_ami_list(profile, region, ami_id):
    session = boto3.Session(profile_name=profile, region_name=region)
    ec2_con = session.client('ec2')
    response = ec2_con.describe_images(Filters=[{"Name": 'owner-id', 'Values': [ami_id]}])
    for image in response['Images']:
        print(image['ImageId'] + " : " + image['Name'])


def do_sg_show(profile, region, sg_id):
    session = boto3.Session(profile_name=profile, region_name=region)
    ec2_con = session.client('ec2')
    response = ec2_con.describe_security_groups(GroupIds=[sg_id])
    for sg in response['SecurityGroups']:
        show_security_group(sg)
        
        
def do_sg_list(profile, region):
    session = boto3.Session(profile_name=profile, region_name=region)
    ec2_con = session.client('ec2')
    response = ec2_con.describe_security_groups()
    print(response)
    for sg in response['SecurityGroups']:
        show_security_group(sg)
        show_rules_in_response(sg['IpPermissionsEgress'])


def show_security_group(sg):
    if 'Tags' in sg:
        name = get_name_from_tags(sg['Tags'])
    else:
        name = "NO NAME"
    print(name + ": " + sg['GroupId'])
    print("  " + sg['Description'])
    print("  Ingress:")
    show_rules_in_response(sg['IpPermissions'])
    print("  Egress:")


def do_ec2_list(profile, region):
    session = boto3.Session(profile_name=profile, region_name=region)
    ec2_con = session.client('ec2')
    response = ec2_con.describe_instances()
    for reservation in response['Reservations']:
        name = ""
        for i in reservation['Instances']:
            if 'Tags' in i:
                name = get_name_from_tags(i['Tags'])
            print("%s\t\t%s\t\t%s\t\t%s - %s" % (
                i['InstanceId'], i['InstanceType'], i['State']['Name'],
                i['PrivateIpAddress'] if 'PrivateIpAddress' in i else "", name))


def do_ec2_spot_list(profile, region):
    session = boto3.Session(profile_name=profile, region_name=region)
    ec2_con = session.client('ec2')
    response = ec2_con.describe_spot_instance_requests()
    for sir in response['SpotInstanceRequests']:
        print(sir['Status']['Code'] + " " + sir[''])


def show_rules_in_response(response):
    for rule in response:
        target = ""
        if 'IpRanges' in rule:
            for ip in rule['IpRanges']:
                target = target + " " + ip['CidrIp']
        if 'UserIdGroupPairs' in rule:
            for pair in rule['UserIdGroupPairs']:
                target = target + " " + pair['GroupId']
        if 'FromPort' in rule:
            print("    %s - %s %s : %s" % (
                rule['FromPort'], rule['ToPort'], rule['IpProtocol'], target
            ))
        else:
            print("    Any - Any %s : %s" % (
                rule['IpProtocol'], target
            ))


def get_name_from_tags(tags):
    for tag in tags:
        if tag['Key'] == 'Name':
            return tag['Value']
    else:
        return ""


def main(arguments):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers()

    parser.add_argument('-r', '--region', help="AWS Region", default="eu-west-2")
    parser.add_argument('-p', '--profile', help="Boto profile name", default="default")
    parser.add_argument('-i', '--id', help='Item ID')

    parser_ec2 = subparsers.add_parser('ec2')
    parser_ec2.add_argument('-a', '--action', choices=['list', 'show', 'spotlist'])
    parser_ec2.set_defaults(func=cmd_ec2)

    parser_sg = subparsers.add_parser('sg')
    parser_sg.add_argument('-a', '--action', choices=['list', 'show', 'add_rule', 'del_rule'])
    parser_sg.set_defaults(func=cmd_sg)

    parser_ami = subparsers.add_parser('ami')
    parser_ami.add_argument('-a', '--action', choices=['list', 'show', 'delete'])
    parser_ami.set_defaults(func=cmd_ami)

    parser_cw = subparsers.add_parser('cw')
    parser_cw.add_argument('-a', '--action', choices=['list', 'show'])
    parser_cw.set_defaults(func=cmd_cw)

    args = parser.parse_args(arguments)
    args.func(args)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
