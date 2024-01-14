## Cannot Access the Web UI Following an Upgrade

There are many reasons why the web UI would be inaccessible following an upgrade. Bugs are also continually fixed as they are discovered. Therefore, do not rely on old GitHub Issues or forum posts that have a solution for a similar effect, since the cause of the effect can be something completely different. The first thing that should be done is to review the upgrade log (/var/log/mycodo/mycodoupgrade.log) for any errors. Next, you can attempt to rerun the upgrade by issuing the following command:

```bash
sudo /opt/Mycodo/mycodo/scripts/upgrade_post.sh
```

## Daemon Not Running

- Check the color of the top left time/version text. Green indicates the daemon is running, while orange or red can indicate an issue.
- Determine if the Daemon is Running: Execute `ps aux | grep mycodo_daemon.py` in a terminal and look for an entry to be returned.
- Check the Logs: From the `[Gear Icon] -> Mycodo Logs` page or /var/log/mycodo/, check the daemon log for any errors. If the issue began after an upgrade, also check the upgrade log for indications of an issue.
- If a solution could not be found after investigating the above suggestions, search the GitHub issues for any open issues or the forum for any recent issues.

## Incorrect Database Version

- Check the `[Gear Icon] -> System Information` page.
- If the "Database Version" is green, it is the correct version. An incorrect version wil lbe colored red and indicate the version is incorrect.
- An incorrect database version means the version stored in the Mycodo settings database (`/opt/Mycodo/databases/mycodo.db`) is not correct for the latest version of Mycodo, determined in the Mycodo config file (`/opt/Mycodo/mycodo/config.py`).
- This can be caused by an error in the upgrade process from an older database version to a newer version, or from a database that did not upgrade during the Mycodo upgrade process.
- Check the Upgrade Log for any issues that may have occurred. The log is located at `/var/log/mycodo/mycodoupgrade.log` but may also be accessed from the web UI (if you're able to): select `[Gear Icon] -> Mycodo Logs -> Upgrade Log`.
- Sometimes issues may not immediately present themselves. It is not uncommon to be experiencing a database issue that was actually introduced several Mycodo versions ago, before the latest upgrade.
- Because of the nature of how many versions the database can be in, correcting a database issue may be very difficult.

It may be much easier to delete your database and start fresh without any configuration. Use the following commands to rename your database and restart the web UI. If both commands are successful, refresh your web UI page in your browser in order to generate a new database and create a new Admin user.

```bash
mv /opt/Mycodo/databases/mycodo.db /opt/Mycodo/databases/mycodo.db.backup
sudo service mycodoflask restart
```

## Restoring a Backup Without the UI

If the web UI is inaccessible, because of an error, for example, you can restore a backup from the command line. See [Backup and Restore](https://github.com/kizniche/Mycodo/wiki/Backup-and-Restore) for more information.

## More on Diagnosing issues

Check out the [Diagnosing Issues](https://github.com/kizniche/Mycodo/wiki/Diagnosing-Issues) for more information about diagnosing issues.
