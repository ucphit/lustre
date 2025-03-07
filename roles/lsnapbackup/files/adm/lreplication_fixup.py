#!/bin/python3

"""
This script will the set of snapshots in common across both sites.
It deletes not common snapshots and starts an incremental backup
from there. If no common snapshots, it starts a full replication.
When the replication processes are completed, it starts the
replication service through systed

One replication process for each zpool in /etc/ldev.conf
"""

import argparse, shared, socket, sys, time
from concurrent.futures import ThreadPoolExecutor

snapshot_file = "/var/log/last_snapshot.txt"

if shared.ldevInfo()[0] == 1:
    cluster_info = shared.ldevInfo()[1:]
else:
    shared.log("FIXUP", f"Error in retrieving ldev info")

#Get the primary datacenter
dc = socket.gethostname().split('.')[0][:5]

lists, full_lists_primary, full_lists_secondary = {}, {}, {}

mapping = {"pstor": "kstor", "kstor": "pstor"}
backup_dc = mapping.get(dc)
if not backup_dc:
    shared.log("FIXUP", f"Error no backup dc")
    sys.exit("An error occurred")

def main():
    parser = argparse.ArgumentParser(description="Checkin snapshot alignment")
    parser.add_argument("-f", "--fixup", default="False", help="True or False")
    args = parser.parse_args()

    create_lists()

    intersection = find_intersection(lists)

    if args.fixup == 'False':
        for key, list in full_lists_primary.items():
            for i in list:
                if i.split('@')[1] not in intersection:
                    shared.log("FIXUP", f"Require deleting {i} on {key.split('_')[0]}\n")
        for key, list in full_lists_secondary.items():
            for i in list:
                if i.split('@')[1] not in intersection:
                    shared.log("FIXUP", f"Require deleting {i} on {key.split('_')[0]}\n")

    #Deleting everything not in the intersection on a fixup
    if args.fixup == 'True':
        for key, list in full_lists_primary.items():
            for i in list:
                if i.split('@')[1] not in intersection:
                    shared.log("FIXUP", f"Deleting {i} on {key.split('_')[0]}\n")
                    cmd = f"ssh {key.split('_')[0]} zfs destroy {i} >/dev/null 2>&1"
                    shared.run_command(cmd)
        for key, list in full_lists_secondary.items():
            for i in list:
                if i.split('@')[1] not in intersection:
                    shared.log("FIXUP", f"Deleting {i} on {key.split('_')[0]}\n")
                    cmd = f"ssh {key.split('_')[0]} zfs destroy {i} >/dev/null 2>&1"
                    shared.run_command(cmd)

    create_lists()
    intersection = find_intersection(lists)

    for i in cluster_info:
        rc = 0
        if set(lists[f'{i[0]}_{i[2]}']) != set(intersection):
            rc =  1
        if set(lists[f"{i[0].replace(dc,backup_dc)}_{i[2]}"]) != set(intersection):
            rc =  1
    shared.log("FIXUP", f"rc is {rc}")

    if args.fixup == 'True' and rc == 0 and lists['pstormgs01_p_mgs/mgs']:
        baseline = lists['pstormgs01_p_mgs/mgs'][-1]
        shared.log("FIXUP", 'Here we go..')
        shared.stop_service('lsnapbackup.service')
        shared.stop_service('lreplication.service')
        shared.log("FIXUP", "Service is stopped")

        # Name of the new snapshot
        new_snapshot_name = f"snapshot_{int(time.time())}_remote"
        shared.log("FIXUP", f"Creating new snapshot: {new_snapshot_name}")

        # make new snapshot on all nodes
        for i in cluster_info:
            shared.make_zfs_snapshot(i[0],i[2],new_snapshot_name)
            shared.log("FIXUP", "Incremental replication")

        with ThreadPoolExecutor() as executor:

            shared.log("FIXUP", f"Performing incremental replication from {baseline}")
            futures = [executor.submit(replicate, i, new_snapshot_name, baseline) for i in cluster_info]
            for future in futures:
                future.result()

        shared.write_last_snapshot(snapshot_file,new_snapshot_name)

        shared.start_service('lreplication.service')

        shared.log("FIXUP", "Task completed. lreplication service started.") 
    else:
        shared.log("FIXUP", "Dry-run finished. Nothing touched!") 

def create_lists():
    global lists, full_lists_primary, full_lists_secondary
    #Making the lists of snapshots
    for i in cluster_info:
        lists[f'{i[0]}_{i[2]}'] = [item.split('@')[1] for item in shared.get_zfs_snapshots(i[0],i[2])[1:]]
        full_lists_primary[f'{i[0]}_{i[2]}'] = [item for item in shared.get_zfs_snapshots(i[0],i[2])[1:]]
        lists[f'{i[0].replace(dc,backup_dc)}_{i[2]}'] = [item.split('@')[1] for item in shared.get_zfs_snapshots(i[0].replace(dc,backup_dc),i[2])[1:]]
        full_lists_secondary[f'{i[0].replace(dc,backup_dc)}_{i[2]}'] = [item for item in shared.get_zfs_snapshots(i[0].replace(dc,backup_dc),i[2])[1:]]


def replicate(i, new_snapshot_name, baseline):

    ssh_command = f'ssh {i[0]} "zfs send -R -I {i[2]}@{baseline} {i[2]}@{new_snapshot_name} | ssh {i[0].replace("pstor","kstor")} zfs receive -F {i[2]}"'
    shared.log("FIXUP", f"Executing replication command: {ssh_command}")
    shared.run_command(ssh_command)

def find_intersection(lists_dict):
    if not lists_dict:
        return []

    all_values = (set(lst) for lst in lists_dict.values())
    intersection = set.intersection(*all_values)

    return list(intersection)

def list_difference(list1, list2):
    return [item for item in list1 if item not in list2]

if __name__ == "__main__":
    main()