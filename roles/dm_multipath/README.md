# dm\_multipath

This roles installs and configures Linux `dm_multipath` driver to access 

## Example Playbook

Install dm-multipath and configure with defaults and ensure it's started:

```
...
    - hosts: all
      roles:
         - ucphit.lustre.dm_multipath
```


Gather information about SAS controllers and JBODs 
and let Ansible name the DM multipath devices depending on their jbods.
This prevents the autodiscovery+naming of multipath devices and
instead creates multipath devices named like: `/dev/mapper/primary-<WWID>`.

```
...
    - hosts: all
      vars:
        dm_multipath_sas_jbods:
          primary: "3500c0ff06711383c"
          secondary: "3500c0ff06711d93c"
        dm_multipath_daemon_readonly_bindings: true
        dm_multipath_defaults_find_multipaths: "no"
        dm_multipath_defaults_user_friendly_names: "no"
      roles:
         - ucphit.lustre.dm_multipath
```

## License

BSD-3-Clause

## Origin

This role is forked from [Cambridge Research Computing Services DM-Multipath Role](https://gitlab.developers.cam.ac.uk/rcs/platforms/infrastructure/ansible-roles/ansible-dm-multipath)
