# Lustre site replication
A role that configures zfs replication from primary to secondary site.

The systemd service lreplication initiates replication from the primary to the secondary cluster. If /var/log/last_snapshot.log exists, an incremental replication is performed; otherwise, a full snapshot replication is executed. Replication occurs at the zpool level, with a separate process spawned for each zpool in parallel.

## Usage

```
  ---
  - name: Setup snapshot backup on lustre filesystem
    hosts: role_mgs
    become: yes
    gather_facts: yes

    roles:
      - role: ucphit.lustre.lsnapreplication
        vars:
          replicate: False
          filesystem: dstor
          primary_mgs: mgsserver01
          secondary_mgs: mgsserver02

```
