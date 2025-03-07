#!/bin/python3

import argparse, shared
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Delete snapshots for a filesystem")
    parser.add_argument("-f", "--filesystem", required=True, help="Filesystem name")
    parser.add_argument("-l", "--label", required=True, choices=["hour_local", "day_local", "week_local"], help="Snapshot class (hour, day or week)")

    args = parser.parse_args()
    lsnapcreate(args.filesystem,args.filesystem+'_'+args.label)

def lsnapcreate(fs,name):
    timestamp = datetime.now().strftime("%a%b%d%H%M%Y")
    command = f'/sbin/lctl snapshot_create -F {fs} -b off -n {timestamp}_{name}'
    shared.run_command(command)

if __name__ == '__main__':
    main()