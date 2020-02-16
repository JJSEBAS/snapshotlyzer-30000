# AWS CLI commands
import boto3

import click

# Creates session and sets user
session = boto3.Session(profile_name='shotty')
ec2 = session.resource('ec2')

# List all active instances
@click.command()
def list_instances():
    "List EC2 instances"
    for i in ec2.instances.all():
        print(i)

# Run script main block
if __name__ == '__main__':
    list_instances()
