#!/bin/python3

import argparse , shared, sys, socket
from datetime import datetime,timedelta

#Get the primary datacenter
dc = socket.gethostname().split('.')[0][:5]

if shared.ldevInfo()[0] == 1:
    cluster_info = shared.ldevInfo()[1:]
else:
    shared.log("LSNAPRETENTION", f"Error in retrieving ldev info")

lists, full_lists_primary, full_lists_secondary = {}, {}, {}

mapping = {"pstor": "kstor", "kstor": "pstor"}
backup_dc = mapping.get(dc)
if not backup_dc:
    shared.log("LSNAPRETENTION", f"Error no backup dc")
    sys.exit("An error occurred")

def main():
    parser = argparse.ArgumentParser(description="Delete snapshots for a filesystem")
    parser.add_argument("-f", "--filesystem", required=True, help="Filesystem name")
    parser.add_argument("-c", "--snapshot_class", required=True, choices=["hour", "day", "week"], help="Snapshot class (hour, day or week)")
    parser.add_argument("-p", "--policy", required=True, help="Policy in the format #(number of days)")

    args = parser.parse_args()
    list = capture_snapshot_info(args.filesystem,args.snapshot_class,args.policy)
    for item in cluster_info:
        for i in list:
            #print(f"ssh {item[0]} zfs destroy {item[2]}@{i} >/dev/null 2>&1")
            delete_snapshot(item[0], f"{item[2]}@{i}")
            delete_snapshot(item[0].replace(dc,backup_dc), f"{item[2]}@{i}")

def capture_snapshot_info(fs,timestamp,snap_age):
    snap_list = []
    cmd = f"zfs list -t snapshot"
    result = shared.run_command(cmd)
    if result[0] == 1:
        lines = result[1].strip().split('\n')
        for snap in [(item.split(' ')[0]).split('@')[1] for item in lines if timestamp in item and fs in item]:
            date_string = snap.strip().split('_')[0]
            date_format = "%a%b%d%H%M%Y"
            datetime_object = datetime.strptime(date_string, date_format)
            age = datetime.now() - datetime_object
            if age > timedelta(days=int(snap_age)):
                snap_list.append(snap)
        return snap_list

def delete_snapshot(node, snapshot_name):
    cmd = f"ssh {node} zfs destroy {snapshot_name} >/dev/null 2>&1"
    shared.log("LSNAPRETENTION", f'Deleting snapshot {snapshot_name} on {node} due to retention')
    shared.run_command(cmd)

if __name__ == '__main__':
    main()