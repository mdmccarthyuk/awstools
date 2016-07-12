#!/usr/bin/python

import sys
import argparse
import boto.ec2
import json
import time
import os.path 

def main():
  global args
  global configPath
  global configuration

  validTypes = [ 'm3.small', 'c1.medium','c3.large', 'm3.medium', 'm3.large' ]
  OSImages = { 
    'ubuntu': 'ami-f95ef58a',
    'amzn': 'ami-b0ac25c3'
  }

  if args.os not in OSImages: 
    print "ERROR: Invalid OS specified\n"
    sys.exit(1)

  if args.config:
    print "Generating a config file - "+configPath
    if ( os.path.isfile(configPath) ):
      print "Config file already exists.  Overwrite [y/n] "
      confirm = raw_input()
      if confirm != 'y':
        print "Aborted by user"
        sys.exit(1)
      config_keyname = raw_input('Enter ec2 root key name: ')
      config_subnet = raw_input('Enter default ec2 subnet: ')
      config_region = raw_input('Enter default region: ')
      config_profile = raw_input('Enter boto profile to use: ')
      config_secgroup = raw_input('Enter default security group: ')
      config_bidprice = raw_input('Enter default bid price: ')
      config = {
        "configfile": {
           "defaults": {
             "region": config_region,
             "key": config_keyname,
             "profile": config_profile,
             "subnet": config_subnet,
             "secgroup": config_secgroup,
             "bidprice": config_bidprice
           }
        }
      }
      with open(configPath, 'w') as outfile:
        json.dump(config, outfile, indent=2)
    print "Config file written"
    sys.exit(0)

  if not ( os.path.isfile(configPath) ):
    print "Config file not found. Run with --config to setup."
    sys.exit(1)
 
  ec2Con = boto.ec2.connect_to_region(args.region,profile_name=args.profile)

  spotReq = ec2Con.request_spot_instances(
    dry_run=False, 
    price=args.bid, 
    image_id=OSImages[args.os], 
    count=1, 
    key_name=args.keyname, 
    security_group_ids=[configuration['configfile']['defaults']['secgroup']], 
    instance_type=args.type,
    subnet_id=configuration['configfile']['defaults']['subnet']
  )[0]
  
  print "Requested spot. Please wait \n" 
  state = 'open'
  while state == 'open':
    time.sleep(3)
    spot = ec2Con.get_all_spot_instance_requests(spotReq.id)[0]
    state = spot.state

  if (state != 'active'):
    print 'Error with spot request - ' + spot.status.code + '\n'
    sys.exit(1)

  ec2Con.create_tags([spot.id,spot.instance_id],{"Name":args.name})

if __name__ == '__main__':
  configPath = os.path.expanduser("~") + "/.awstool/config"

  parser = argparse.ArgumentParser(description="AWS EC2 Instance launcher")

  if ( os.path.isfile(configPath) ):
    with open(configPath) as configFile:
      configuration = json.load(configFile)
   
    parser.add_argument('-o','--os',default='amzn',help='Type of instance (amzn/ubuntu)')
    parser.add_argument('-p','--profile',default=configuration['configfile']['defaults']['profile'],help='boto profile to use')
    parser.add_argument('-r','--region',default=configuration['configfile']['defaults']['region'],help='AWS region to use' )
    parser.add_argument('-k','--keyname',default=configuration['configfile']['defaults']['key'],help='EC2 root key')
    parser.add_argument('-t','--type',default='m3.medium',help='instance type to use')
    parser.add_argument('-b','--bid',default=configuration['configfile']['defaults']['bidprice'],help='bid price')
    parser.add_argument('-n','--name',help='instance name')
  else: 
    parser.add_argument('-o','--os',default='amzn',help='Type of instance (amzn/ubuntu)')
    parser.add_argument('-p','--profile',required=True,help='boto profile to use')
    parser.add_argument('-r','--region',default='eu-west-1',help='AWS region to use (default=eu-west-1)')
    parser.add_argument('-k','--keyname',help='EC2 root key')
    parser.add_argument('-t','--type',default='m3.medium',help='instance type to use')
    parser.add_argument('-b','--bid',default='0.015',help='bid price')
    parser.add_argument('-n','--name',help='instance name')
    
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument('--spot',help='Request a spot instance',action='store_true')
  group.add_argument('--config',help='Write configuration file',action='store_true')
  group.add_argument('--ondemand',help='Request on-demand instance',action='store_true')

  args = parser.parse_args()
  main()
  sys.exit(0)
