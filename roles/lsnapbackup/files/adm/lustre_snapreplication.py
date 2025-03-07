#!/usr/bin/python3

"""
This script is doing the dirty work of replicating zpools
from priomary to seconday site with zfs send/receive.
It starts a send/receive for each zpool in parallel.
It is running running through systemd on lustre mgs and logging to
/var/log/llustre.log
"""


import time, signal, shared, socket, sys
from concurrent.futures import ThreadPoolExecutor
from threading import Event

running = Event()
running.set()
#running = True

filesystem = "dstor"

snapshot_file = "/var/log/last_snapshot.txt"

if shared.ldevInfo()[0] == 1:
    cluster_info = shared.ldevInfo()[1:]
else:
    shared.log("SNAPREPLICATION", "Error in retrieving ldev info")

#Get the primary datacenter
dc = socket.gethostname().split('.')[0][:5]

#Setting primary and secondary site
mapping = {"pstor": "kstor", "kstor": "pstor"}
backup_dc = mapping.get(dc)
if not backup_dc:
    shared.log("SNAPCLEAN", "An error occurred. No backup dc")
    sys.exit("An error occurred")

def snapshot_clean(snap_name):
    for i in cluster_info:
        if shared.get_zfs_snapshots(i[0],i[2])[0] == 1:
            list1 = [item.split('@')[1] for item in shared.get_zfs_snapshots(i[0],i[2])[1:]]
            for item in list1:
                if item.endswith('remote') and (item != snap_name):
                    cmd = f"ssh {i[0]} zfs destroy {i[2]}@{item}"
                    
                    shared.run_command(cmd)
                    shared.log("SNAPCLEAN", f"Deleting snapshot {i[2]}@{item} on {i[0]}")
        else:
            shared.log("SNAPCLEAN","Error in retrieving snapshots")

        if shared.get_zfs_snapshots(i[0].replace(dc,backup_dc),i[2])[0] == 1:
            list2 = [item.split('@')[1] for item in shared.get_zfs_snapshots(i[0].replace(dc,backup_dc),i[2])[1:]]
            for item in list2:
                if item.endswith('remote') and item != snap_name:
                    cmd = f"ssh {i[0].replace(dc,backup_dc)} zfs destroy {i[2]}@{item}"
                    
                    shared.run_command(cmd)
                    shared.log(f"SNAPCLEAN", f"Deleting snapshot {i[2]}@{item} on {i[0].replace(dc,backup_dc)}")
        else:
            shared.log("SNAPCLEAN", "Error in retrieving snapshots")

def replicate(i, new_snapshot_name, last_snapshot=None):
    if last_snapshot is None:
        cmd = f'ssh {i[0]} "zfs send {i[2]}@{new_snapshot_name} | ssh {i[0].replace("pstor","kstor")} zfs receive -F {i[2]}"'
    else:
        cmd = f'ssh {i[0]} "zfs send -R -I {i[2]}@{last_snapshot} {i[2]}@{new_snapshot_name} | ssh {i[0].replace("pstor","kstor")} zfs receive -F {i[2]}"'
    shared.log("SNAPREPLICATION", f"Executing replication command: {cmd}")
    result = shared.run_command(cmd)
    if result[0] == 0:
        shared.log("SNAPREPLICATION", f"Error: {result[1]}")

def replication():

    last_snapshot = shared.read_last_snapshot(snapshot_file)
    shared.log("SNAPREPLICATION", f"Last snapshot was: {last_snapshot}")

    new_snapshot_name = f"snapshot_{int(time.time())}_remote"
    shared.log("SNAPREPLICATION", f"Creating new snapshot: {new_snapshot_name}")
    shared.write_last_snapshot(snapshot_file, new_snapshot_name) 

    for i in cluster_info:
        shared.make_zfs_snapshot(i[0],i[2],new_snapshot_name)

    with ThreadPoolExecutor() as executor:
        if last_snapshot is None:
            shared.log("SNAPREPLICATION", "Performing full baseline replication")
            futures = [executor.submit(replicate, i, new_snapshot_name) for i in cluster_info]
        else:
            shared.log("SNAPREPLICATION", "Performing incremental replication")
            futures = [executor.submit(replicate, i, new_snapshot_name, last_snapshot) for i in cluster_info]

        for future in futures:
            future.result()

    shared.log("SNAPREPLICATION", "Replication task completed.")  

    shared.log("SNAPCLEAN", "Starting remote snapshot cleaning.")
    snapshot_clean(new_snapshot_name)
    shared.log("SNAPCLEAN", "Task snapshot cleaning completed.")

def signal_handler(sig, frame):
    print("Daemon is stopping...")
    running.clear()

#def signal_handler(sig, frame):
#    global running
#    print("Daemon is stopping...")
#    running = False 

def main():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    while running:
        replication()
        for _ in range(1200):
            if not running.is_set():
                sys.exit()
            time.sleep(1)
        #time.sleep(1200)

    shared.log("SNAPREPLICATION", "Daemon stopped.")

if __name__ == "__main__":

    main()