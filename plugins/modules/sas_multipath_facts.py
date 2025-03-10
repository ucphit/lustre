DOCUMENTATION = r'''
---
module: sas_multipath_facts
short_description: Return list of SAS disks sorted by controllers.
description:
     - Returns list of SAS disks sorted in groups by jbods.
     - If given by the user the jbods get roles assigned (primary, secondary).
version_added: "2.15"
requirements: ["Linux kernel with sysfs"]
attributes:
    check_mode:
        support: full
    diff_mode:
        support: none
    facts:
        support: full
    platform:
        platforms: linux
author:
  - Benedikt Braunger (@zsn342)
'''

EXAMPLES = r'''
- name: Populate SAS multipath facts
  sas_multipath_facts:
    # optinal roles
    primary: "3500c0ff06711383c"
    secondary: "3500c0ff06711d93c"

- name: Print service facts
  ansible.builtin.debug:
    var: ansible_facts.sas_multipath_facts
'''

RETURN = r'''
ansible_facts:
  description: Facts to add to ansible_facts about the sas devices on the system
  returned: always
  type: complex
  contains:
    sas_ctrls:
      description: Dict of SAS controllers with ports and attached jbods
      returned: always
      type: dict
      elements: dict
    sas_jbods:
      description: Dict of SAS JBODs and attached disks
      returned: always
      type: dict
      elements: dict
'''


import os
import glob
from ansible.module_utils.basic import AnsibleModule


class SAS_JBODS(object):

    def __init__(self, module):
        self.module = module
        self.ctrls = {}
        self.jbods = {}
        # the type of controllers this module was developed for
        self.ctrl_class = "0x010700"
        self.ctrl_glob = glob.glob("/sys/devices/*/*/*/", recursive=True)

    def gather_controllers(self):
        for path in self.ctrl_glob:
            try:
                with open(os.path.join(path, "class"), "r") as f:
                    device_class = f.readline().rstrip()
                    if device_class == self.ctrl_class:
                        self.ctrls[path] = {}
                    f.close()
            except FileNotFoundError:
                pass

    def gather_jbods(self):
        for ctrl in self.ctrls:
            for port in self.ctrls[ctrl]:
                for jbod in glob.glob(os.path.join(port, 'expander-*/port-*0/end_device*/target*/*:*/'), recursive=True):
                    try:
                        with open(os.path.join(jbod, "wwid"), "r") as f:
                            wwid = f.readline().rstrip().replace("naa.", "3")
                            self.ctrls[ctrl][port] = { "jbod": wwid }
                            self.jbods.setdefault(wwid, {"ports": []})
                            self.jbods[wwid]["ports"] += [jbod]
                            f.close()
                    except FileNotFoundError:
                        pass

    def add_controller_ports(self):
        for ctrl in self.ctrls:
            for port in glob.glob(os.path.join(ctrl, 'host*/port-*'), recursive=True):
                self.ctrls[ctrl][port] = {}

    def gather_disks_by_jbods(self):
        for jbod in self.jbods:
            disk_basepath = os.path.normpath(self.jbods[jbod]["ports"][0]).rsplit(os.sep, maxsplit=4)[0]
            disk_glob = os.path.join(disk_basepath, "port-*/expander*/port-*/end_device-*/target*/*:*/")
            for disk_path in glob.glob(disk_glob):
                try:
                    with open(os.path.join(disk_path, "wwid"), "r") as f:
                        wwid = f.readline().rstrip().replace("naa.", "3")
                        disk_type = self.disk_type(disk_path)
                        self.jbods[jbod].setdefault("disks", [])
                        self.jbods[jbod]["disks"].append({'wwid': wwid,
                                                         'type': disk_type,
                                                         'path': disk_path
                                                          })
                        f.close()
                except FileNotFoundError:
                    pass

    def assign_jbod_role(self, primary="xxx.0000000000000000", secondary="xxx.0000000000000000"):
        # check if JBOD present
        self.primary = primary
        self.secondary = secondary
        for jbod in self.jbods:
            if jbod == self.primary:
                self.jbods[jbod]["role"] = "primary"
            elif jbod == self.secondary:
                self.jbods[jbod]["role"] = "secondary"
            else:
                self.jbods[jbod]["role"] = "unknown"

    def disk_type(self, disk):
        ret="unknown"
        try:
            rot_path = glob.glob(os.path.join(disk, "block/*/queue/rotational"))[0]
            with open(rot_path, "r") as f:
                rot = f.readline().strip()
                if rot == "1":
                    ret="hdd"
                elif rot == "0":
                    ret="ssd"
        except (IndexError) as e:
            # glob return empty list if we hit the WWID of a enclosure
            # cause block/ doesn't exists for them
            pass
        return(ret)


def main():
    argument_spec = dict(
        primary=dict(type='str'),
        secondary=dict(type='str')
    )

    module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True,
            required_together=[
                ['primary', 'secondary'],
            ]
    )

    sas_jbods = SAS_JBODS(module)
    sas_jbods.gather_controllers()
    sas_jbods.add_controller_ports()
    sas_jbods.gather_jbods()
    if module.params['primary'] and module.params['secondary']:
        sas_jbods.assign_jbod_role(primary = module.params['primary'],
                                   secondary = module.params['secondary']
                                  )
    else:
        sas_jbods.assign_jbod_role()
    sas_jbods.gather_disks_by_jbods()

    if len(sas_jbods.ctrls) == 0:
        results = dict(skipped=True,
                       msg="Failed to find any SAS controllers. \
                            This can be due to privileges or some other configuration issue."
                        )
    else:
        results = dict(ansible_facts=dict(sas_jbods=sas_jbods.jbods, sas_ctrls=sas_jbods.ctrls))
    module.exit_json(**results)


if __name__ == '__main__':
    main()
