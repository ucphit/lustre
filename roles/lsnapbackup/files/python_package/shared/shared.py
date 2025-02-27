"""
- run_command: takes a command string to process in subprocess
- get_zfs_snapshots: Returns a list of zfs snapshots for a dataset
- make_zfs_snapshot: Makes a zfs snapshot on a dataset
- ldevInfo: Returns ordered information from ldev.conf
- log: Sets up logging to /var/log/llustre.log
"""

import subprocess, logging, sys

class ServiceFilter(logging.Filter):
    def __init__(self, service):
        super().__init__()
        self.service = service

    def filter(self, record):
        record.service = self.service
        return True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(service)s] %(message)s",
    handlers=[
        logging.FileHandler("/var/log/llustre.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

def log(service, message, level="info"):
    logger = logging.getLogger(service)
    service_filter = ServiceFilter(service)
    logger.addFilter(service_filter)
    if level.lower() == "debug":
        logger.debug(message)
    elif level.lower() == "warning":
        logger.warning(message)
    elif level.lower() == "error":
        logger.error(message)
    elif level.lower() == "critical":
        logger.critical(message)
    else:
        logger.info(message)

def run_command(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if result.returncode != 0:
        return [0,result.stderr]
    else:
        return [1,result.stdout]
    
def get_zfs_snapshots(host, dataset):
    snapshots = []
    command = f"ssh {host} zfs list -t snapshot {dataset}"
    result = run_command(command)
    if result[0] == 0:
        snapshots = [0,result[1]]
    else:
        lines = result[1].strip().split('\n')
        snapshots.append(1)
        for item in lines[1:]:
            snapshots.append(item.split()[0])
    return snapshots

def make_zfs_snapshot(node,dataset,name):
    cmd = f'ssh {node} zfs snapshot {dataset}@{name}'
    run_command(cmd)

def ldevInfo(node, path='/etc/ldev.conf'):
    column_pairs=[]
    command = f'ssh { node } cat { path }'
    result = run_command(command)
    if result[0] == 0:
        column_pairs = [0,result[1]]
    else:
        column_pairs.append(1)
        for item in result[1].splitlines():
            columns = item.split()
            if len(columns) >= 4:
                column_pairs.append([columns[0],columns[2],columns[3].split(':')[1]])
    return column_pairs  

def stop_service(service_name):
    try:
        cmd = f"systemctl stop {service_name}"
        result = run_command(cmd)
        return 0 if result[0] == 0 else 1
    except subprocess.CalledProcessError as e:
        return 0

def start_service(service_name):
    try:
        cmd = f"systemctl start {service_name}"
        result = run_command(cmd)
        return 0 if result[0] == 0 else 1
    except subprocess.CalledProcessError as e:
        return 0

def write_last_snapshot(file, snapshot_name):
    with open(file, "w") as f:
        f.write(snapshot_name)

def read_last_snapshot(file):
    try:
        with open(file, "r") as f:
            last_snapshot = f.read().strip()
            return last_snapshot
    except FileNotFoundError:
        return None