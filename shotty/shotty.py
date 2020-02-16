# Amazon Web Services (AWS) SDK for Python
import boto3

import botocore

# Click is a Python package for creating command line interfaces
import click

# Creates session and sets user
session = boto3.Session(profile_name='shotty')
ec2 = session.resource('ec2')

# filter_instances filters intances based on the tag, Project.
def filter_instances(project):
    instances =[]

    if project:
        filters = [{'Name':'tag:Project', 'Values':[project]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    return instances

def has_pending_snapshot(volume):
    snapshots = list(volume.snapshots.all())
    return snapshots and snapshots[0].state == 'pending'

@click.group()
def cli():
    """Shotty manages snapshots"""

# Commands for snapshots
@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option('--project', default=None,
    help="Only snapshots for project (tag:Project:<name>)")
# Another option to see all list_snapshots
@click.option('--all', 'list_all', default=False, is_flag=True,
    help="List all snapshots for each volume, not just the most recent")
def list_snapshots(project, list_all):
    "List EC2 snapshots"

    instances = filter_instances(project)

    for i in instances:
        for v in i.volumes.all():
            for s in v. snapshots.all():
                print(",".join((
                s.id,
                v.id,
                i.id,
                s.state,
                s.progress,
                s.start_time.strftime("%c")
                )))
                # Boto3 orders list of snapshot from most recent to oldest
                # So only show latest snapshot if list_all is not used
                if s.state == 'completed' and not list_all: break
    return


# Commands for volumes
@cli.group('volumes')
def volumes():
    """Commands for volumes"""

@volumes.command('list')
@click.option('--project', default=None,
    help="Only volumes for project (tag:Project:<name>)")
def list_volumes(project):
    "List EC2 volumes"

    instances = filter_instances(project)

    for i in instances:
        for v in i.volumes.all():
            print(",".join((
            v.id,
            i.id,
            v.state,
            str(v.size) + "GiB",
            v.encrypted and "Encrypted" or "Not Encrypted"
            )))

    return

# Commands for EC2 instances
@cli.group('instances')
def instances():
    """Commands for instances"""

# Command to create a snapshot of  EC2 instances
@instances.command('snapshot',
    help="Create snapshots of all volumes")
@click.option('--project', default=None,
    help="Only instances for project (tag:Project:<name>)")
def create_snapshots(project):
    """Create snapshots for EC2 instances"""
    instances = filter_instances(project)

    for i in instances:
        print("Stopping {0}...".format(i.id))

        i.stop()
        i.wait_until_stopped()

        for v in i.volumes.all():
            # Look for pending snapshot
            if has_pending_snapshot(v):
                print("Skipping {0}, snapshot already in progress".format(v.id))
                continue
            print("Creating snapshot of {0}".format(v.id))
            v.create_snapshot(Description="Created by SnapshotAlyzer 30000")

        print("Starting {0}...".format(i.id))

        i.start()
        i.wait_until_running()
    print("Job's done!")
    return

@instances.command('list')
@click.option('--project', default=None,
    help="Only instances for project (tag:Project:<name>)")
def list_instances(project):
    "List EC2 instances"

    instances = filter_instances(project)

    for i in instances:
        # Disctionary comprehension to find the tags of each instance.
        # Return empty list if there's no tag.
        tags = {t['Key']: t['Value'] for t in i.tags or []}

        # Get details for each EC2 instance.
        print(','.join((
        i.id,
        i.instance_type,
        i.placement['AvailabilityZone'],
        i.state['Name'],
        i.public_dns_name,
        tags.get('Project', '<no project>'))))

    return

# Command to Stop EC2 intances
@instances.command('stop')
@click.option('--project', default=None,
    help='Only instances for project')
def stop_instances(project):
    "Stop EC2 instances"

    instances = filter_instances(project)

    for i in instances:
        print("Stopping {0}...".format(i.id))
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print("Could not stop {0}. ".format(i.id) + str(e))
            continue

    return

# Command to start EC2 projects
@instances.command('start')
@click.option('--project', default=None,
    help='Only instances for project')
def start_instances(project):
    "Start EC2 instances"

    instances = filter_instances(project)

    for i in instances:
        print("Starting {0}...".format(i.id))
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
            print("Could not start {0}. ".format(i.id) + str(e))
            continue

    return

# Run script main block
if __name__ == '__main__':
    cli()
