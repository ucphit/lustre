# Lustre site replication
A role that configures zfs replication from primary to secondary site.

The systemd service lreplication initiates replication from the primary to the secondary cluster. If /var/log/last_snapshot.log exists, an incremental replication is performed; otherwise, a full snapshot replication is executed. Replication occurs at the zpool level, with a separate process spawned for each zpool in parallel.

## Usage

Implementing the lreplication service

```
  ---
  - name: Setup snapshot backup on lustre filesystem
    hosts: role_mgs
    become: yes
    gather_facts: yes

    roles:
      - role: ucphit.lustre.lsnapreplication
        vars:
          mode: daemon
          fixup: False 
          primary_mgs: mgsserver01
          secondary_mgs: mgsserver02

```

Fixing a failed lreplication service due inconsistency in snapshot history.

### Dry-run

```
---
  - name: Setup snapshot backup on lustre filesystem
    hosts: role_mgs
    become: yes
    gather_facts: yes

    roles:
      - role: ucphit.lustre.lsnapreplication
        vars:
          mode: fixup
          fixup: False 
          primary_mgs: mgsserver01
          secondary_mgs: mgsserver02

```

### Fixing snapshot inconsistency and start replication service

```
---
  - name: Setup snapshot backup on lustre filesystem
    hosts: role_mgs
    become: yes
    gather_facts: yes

    roles:
      - role: ucphit.lustre.lsnapreplication
        vars:
          mode: fixup
          fixup: False 
          primary_mgs: mgsserver01
          secondary_mgs: mgsserver02

```