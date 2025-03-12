#!/bin/python3
DOCUMENTATION = r'''
---
module: lustre_manage

short_description: Module for working lustre filesystem
version_added: 1.0.0
description: Module for creating, deleting and changing lustre filesystems

options:
    name:
        description: Name of the lustre filesystem
        required: true
        type: str
    index: 
        description: Unique integer index
        type: int
    pool:
        description: The name of the zfs pool for the lustre fs
        required: true
        type: str
    type:
            -   mgs
            -   mdt
            -   ost
        required: true
        type: str
    fstype:
            -   zfs
        required: false
        type: str
    mgsnode:
        description: List of nodes that can host the mgs service (failover)
        type: list
    servicenode:
        description: List of nodes that can host the filesystem (failover)
        type: list
    state:
            -   present
            -   absent
        required: false
        type: str

author:
    - Henrik Ursin
'''

EXAMPLES = r'''
#Create lustre mgs filesystem
- name: Create lustre mgs fs on zfs
  kuit_lustre_module:
    name: mgspool/mgt
    type: mgs
    fstype: zfs
    servicenode: 
        -   10.0.2.10
        -   10.0.2.11
    state: present

#Create lustre mdt filesystem
- name: Create lustre mdt fs on zfs
  kuit_lustre_module:
    name: mdtpool/demo
    index: 0
    type: mdt
    fstype: zfs
    mgsnode: 
        -   10.0.2.10
        -   10.0.2.11
    servicenode:
        - 10.0.2.30
        - 10.0.2.31
    state: present

#Set new mgs node on lustre filesystem

#Reregister node to the mgs

#Update lustre version in existing lustre fs
'''

import subprocess
from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        fsname=dict(type='str', required=False),
        index=dict(type='int', required=False),
        type=dict(type='str', required=True, choices=['mgs', 'mdt', 'ost']),
        fstype=dict(type='str', choices=['zfs', 'ldiskfs'], default='zfs'),
        mgsnode=dict(type='list', elements='str', required=False),
        servicenode=dict(type='list', elements='str', required=True),
        state=dict(type='str', choices=['present', 'absent'], default='present')
    )

    result = dict(changed=False, message='')

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)
    module.warn(f"Running with params: {module.params}")
    if module.check_mode:
        module.exit_json(**result)

    params = module.params
    name, fsname, index, fs_type, node_type = params['name'], params['fsname'], params['index'], params['fstype'], params['type']
    mgs_nodes, service_nodes, state = params['mgsnode'], params['servicenode'], params['state']

    if node_type != 'mgs' and not fsname:
        module.fail_json(msg="'fsname' is required when type is not 'mgs'")

    if node_type != 'mgs' and index is None:
        module.fail_json(msg="'index' is required when type is not 'mgs")

    if state == 'present':
        if not check_for_lustre(name):
            success, msg = mk_fs(fs_type, node_type, fsname, index, mgs_nodes, service_nodes, name)
            if success:
                result['changed'] = True
                result['message'] = msg
                module.exit_json(**result)
            else:
                result['message'] = msg
                module.fail_json(msg=msg, **result)
        else:
            result['message'] = 'Lustre filesystem already exists. Nothing to do.'
            module.exit_json(**result)
    else:
        result['message'] = 'State "absent" not implemented yet.'
        module.fail_json(msg='State "absent" not implemented.', **result)

def mk_fs(fs_type, node_type, fs_name, index, mgs_nodes, service_nodes, name):
    try:
        command = ['mkfs.lustre', f'--backfstype={fs_type}', f'--{node_type}']

        if node_type in ('mdt', 'ost'):
            if fs_name is None:
                return False, f'fsname is required for {node_type.upper()}'
            command += ['--fsname', fs_name]
            if index is None:
                return False, f'Index is required for {node_type.upper()}'
            command += [f'--index={index}']
            if not mgs_nodes:
                return False, 'mgsnode is required for MDT and OST'
            mgs_list = ':'.join(f'{host}@tcp0' for host in mgs_nodes)
            command.append(f'--mgsnode={mgs_list}')

        if service_nodes:
            service_list = ':'.join(f'{host}@tcp0' for host in service_nodes)
            command.append(f'--servicenode={service_list}')

        # Add device name (ZFS volume)
        command.append(name)

        subprocess.run(command, check=True)
        return True, f'Lustre {node_type.upper()} filesystem created successfully.'
    except subprocess.CalledProcessError as e:
        return False, f'Failed to create Lustre filesystem: {e}'
    except Exception as e:
        return False, f'Unexpected error: {e}'

def check_for_lustre(name):
    try:
        result = subprocess.run(['tunefs.lustre', name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout_str = result.stdout.decode('utf-8') if result.stdout else ""

        if "checking for existing Lustre data: found" in stdout_str:
            return True
        else:
            return False
    except FileNotFoundError:
        print("tunefs.lustre command not found")
        return False

def main():
    run_module()

if __name__ == '__main__':

    main()