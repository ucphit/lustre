# Lustre site replication
A role that configures zfs replication from primary to secondary site.

## Usage

---
- name: Setup snapshot backup on lustre filesystem
  hosts: role_mgs
  become: yes
  gather_facts: yes

  roles:
    - role: ucphit.lustre.lsnapreplication
      vars:
        filesystem: dstor
        primary_mgs: mgsserver01
        secondary_mgs: mgsserver02