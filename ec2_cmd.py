#!/usr/bin/env python2.7

import boto3
import sys
import argparse
import paramiko
import subprocess
import os


def do_cmd(cmd, tags, region, profile, states):
    session = boto3.Session(profile_name=profile, region_name=region)
    ec2_con = session.client('ec2')
    response = ec2_con.describe_instances()
    tag_query = tags.split(";")
    match_count = 0
    states_list = states.split(',')
    for reservation in response['Reservations']:
        for i in reservation['Instances']:
            if 'Tags' in i:
                name = get_name_from_tags(i['Tags'])
                for tag in i['Tags']:
                    for qtag in tag_query:
                        qkey, qval = qtag.split("=")
                        if (qkey == tag['Key']) and (qval == tag['Value']):
                            if i['State']['Name'] in states_list:
                                print("%s\t\t%s\t\t%s\t\t%s - %s" % (
                                    i['InstanceId'], i['InstanceType'], i['State']['Name'],
                                    i['PrivateIpAddress'] if 'PrivateIpAddress' in i else "", name))
                                if cmd != 'null':
                                    do_ssh_command(i['PrivateIpAddress'], cmd)
                                match_count += 1
    if match_count is 0:
        print("No matches found")


def do_ssh_command(host, remote_cmd):
    ssh_config = paramiko.SSHConfig()
    ssh_config.parse(open(os.path.expanduser('~/.ssh/config-ec2cmd')))
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.RSAKey.from_private_key_file(os.path.expanduser('~/.ssh/id_rsa_l'))
    target_host = ssh_config.lookup(host)
    proxy_command = paramiko.ProxyCommand(
        subprocess.check_output(
            [os.environ['SHELL'], '-c', 'echo %s' % target_host['proxycommand']]
        ).strip()
    )
    client.connect(hostname=host, username="ec2-user", pkey=key, sock=proxy_command)
    (stdin, stdout, stderr) = client.exec_command(remote_cmd)
    stdout.channel.recv_exit_status()
    for line in stdout.readlines():
        print(line)


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

    parser.add_argument('-r', '--region', help="AWS Region", default="eu-west-2")
    parser.add_argument('-p', '--profile', help="Boto profile name", default="default")
    parser.add_argument('-t', '--tags', help='Tags to match on [key=val;key2=val2]')
    parser.add_argument('-c', '--command', help='Command to run', default='null')
    parser.add_argument('-s', '--states', help='States to check for',
                        default="running,stopped,terminated,starting,stopping")

    args = parser.parse_args(arguments)
    do_cmd(args.command, args.tags, args.region, args.profile, args.states)
    sys.exit(0)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
