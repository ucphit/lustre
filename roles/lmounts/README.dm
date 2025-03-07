# The lmounts role

A role that configures the Lustre mountpoints through /etc/fstab.


### Usage
The role will implement the following naming convention for the mountpoints:

```
            { role }{  }
```
In the example we end up with the following /etc/fstab entries for nodeoss01:
```
oss_1_fs/fs1 /lustre/fs1 lustre flock,x-systemd.mount-timeout=240,noauto 0 0
oss_1_fs/fs1 /lustre/fs1 lustre flock,x-systemd.mount-timeout=240,noauto 0 0
```
with a ldev.conf
```
nodemgs01	nodemgs02	MGS	zfs:p_mgs/mgs
nodemds01	nodemds02	fs-MDT0000	zfs:mds_0_fs/fs0
nodeoss01	nodeoss02	fs-OST0002	zfs:oss_2_fs/fs2
nodeoss01	nodeoss02	fs-OST0001	zfs:oss_1_fs/fs1
```


```
---
  - name: Setup lustre mountpoints
    hosts: role_mgs,role_oss,role_mds
    become: yes
    gather_facts: no

    roles:
      - role: ucphit.lustre.lmounts
        vars:
            mount_path: /lustre
            mount_opts: flock,x-systemd.mount-timeout=240,noauto

```