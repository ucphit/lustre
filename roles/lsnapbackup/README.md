# Lustre snapshot backup

A role that configures lustre consistent snapshot backup.

It will start a systemd service lsnapbackup, that takes a snapshot every hour, a snapshot every day and a snapshot every week.

The snapshot retention is controlled by passing hourly, daily, weekly retention time in units of days to the role.

## Usage

---
- name: Setup snapshot backup on lustre filesystem
  hosts: role_mgs
  become: yes
  gather_facts: no

  roles:
    - role: ucphit.lustre.lsnapbackup
      vars:
        hours: 1
        days: 30
        weeks: 180
      when: system == primary_site

In thsi case the primary_site is defined in group_vars and hourly, daily and weekly snapshots are kept for respectively 1, 30 and 180 days (1 day, 1 month and 6 months)


