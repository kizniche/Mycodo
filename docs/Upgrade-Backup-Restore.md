## Upgrading

Page\: `[Gear Icon] -> Upgrade`

If you already have Mycodo installed, you can perform an upgrade to the latest [Mycodo Release](https://github.com/kizniche/Mycodo/releases) by either using the Upgrade option in the web interface (recommended) or by issuing the following command in a terminal. A log of the upgrade process is created at ``/var/log/mycodo/mycodoupgrade.log`` and is also available from the `[Gear Icon] -> Mycodo Logs` page.

```bash
sudo mycodo-commands upgrade-mycodo
```

## Backup-Restore

Page\: `[Gear Icon] -> Backup Restore`

A backup is made to /var/Mycodo-backups when the system is upgraded or instructed to do so from the web interface on the ``[Gear Icon] -> Backup Restore`` page.

If you need to restore a backup, this can be done on the ``[Gear Icon] -> Backup  Restore`` page (recommended). Find the backup
you would like restored and press the Restore button beside it. If you're unable to access the web interface, a restore can also be initialized through the command line. Use the following command to initialize a restore. The \[backup_location\] must be the full path to the backup to be restored (e.g. "/var/Mycodo-backups/Mycodo-backup-2018-03-11\_21-19-15-5.6.4/" without quotes).

```bash
sudo mycodo-commands backup-restore [backup_location]
```
