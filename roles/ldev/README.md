# The ldev role

A role that compose the /etc/ldev.conf for a Lustre site.

### Usage

The role requires an lcfg dictionary that defines the node topology of the Lustre site.

Ensure that node names resolve correctly via /etc/hosts — refer to the hosts role for configuration.

Run the play on all nodes specified in lcfg. If the Lustre site topology changes, update lcfg and rerun the play.

Additionally, ensure that any modifications to /etc/ldev.conf are reflected in /etc/hosts.

The role will implement the following naming convention for the zpool and the overlaying Lustre dataset:

```
            { role }_{ index }_{ filesystem }/{ filesystem }{ index }
```
In the following example one would end up with:

```
nodemgs01	nodemgs02	MGS	zfs:p_mgs/mgs
nodemds01	nodemds02	dstor-MDT0000	zfs:mds_0_dstor/dstor0
nodeoss01	nodeoss02	dstor-OST0001	zfs:oss_1_dstor/dstor1
nodeoss01	nodeoss02	dstor-OST0002	zfs:oss_2_dstor/dstor2
nodeoss02	nodeoss01	dstor-OST0003	zfs:oss_3_dstor/dstor3
nodeoss02	nodeoss01	dstor-OST0004	zfs:oss_4_dstor/dstor4
```

```
  ---
  - name: Setup /etc/ldev.conf 
    hosts: role_mgs,role_oss,role_mds
    become: yes
    gather_facts: no

    roles:
      - role: ucphit.lustre.ldev
        vars:
            lcfg:
                nodemgs01:
                    failover: nodemgs02
                    role: mgs
                    zfs_pools: p_mgs
                nodemds01:
                    failover: nodemds02
                    role: mds
                    zfs_pools:
                    - filesystem: dstor
                        index: 0
                nodemds02:
                    failover: nodemds01
                    role: mds
                nodeoss01:
                    failover: nodeoss02
                    role: oss
                    zfs_pools:
                    - filesystem: dstor
                        index: 1
                    - filesystem: dstor
                        index: 2
                nodeoss02:
                    failover: nodeoss01
                    role: oss
                    zfs_pools:
                    - filesystem: dstor
                        index: 3
                    - filesystem: dstor
                        index: 4
          

```
