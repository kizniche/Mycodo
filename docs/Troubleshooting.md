## Daemon Not Running

-   Check the Logs: From the `[Gear Icon] -> Mycodo Logs` page, check the Daemon Log for any errors. If the issue began after an upgrade, also check the Upgrade Log for indications of an issue.
-   Determine if the Daemon is Running: Execute `ps aux | grep '/var/mycodo-root/env/bin/python /var/mycodo-root/mycodo/mycodo_daemon.py'` in a terminal and look for an entry to be returned. If nothing is returned, the daemon is not running.
-   Daemon Lock File: If the daemon is not running, make sure the daemon lock file is deleted at `/var/lock/mycodo.pid`. The daemon cannot start if the lock file is present.
-   If a solution could not be found after investigating the above suggestions, submit a [New Mycodo Issue](https://github.com/kizniche/Mycodo/issues/new) on github.

## Incorrect Database Version

-   Check the `[Gear Icon] -> System Information` page or select the mycodo logo in the top-left.
-   An incorrect database version error means the version stored in the Mycodo settings database (`~/Mycodo/databases/mycodo.db`) is not correct for the latest version of Mycodo, determined in the Mycodo config file (`~/Mycodo/mycodo/config.py`).
-   This can be caused by an error in the upgrade process from an older database version to a newer version, or from a database that did not upgrade during the Mycodo upgrade process.
-   Check the Upgrade Log for any issues that may have occurred. The log is located at `/var/log/mycodo/mycodoupgrade.log` but may also be accessed from the web UI (if you're able to): select `[Gear Icon] -> Mycodo Logs -> Upgrade Log`.
-   Sometimes issues may not immediately present themselves. It is not uncommon to be experiencing a database issue that was actually introduced several Mycodo versions ago, before the latest upgrade.
-   Because of the nature of how many versions the database can be in, correcting a database issue may be very difficult. It may be much easier to delete your database and let Mycodo generate a new one.
-   Use the following commands to rename your database and restart the web UI. If both commands are successful, refresh your web UI page in your browser in order to generate a new database and create a new Admin user.

```bash
mv ~/Mycodo/databases/mycodo.db ~/Mycodo/databases/mycodo.db.backup
sudo service mycodoflask restart
```

## More

Check out the [Diagnosing Mycodo Issues Wiki Page](https://github.com/kizniche/Mycodo/wiki/Diagnosing-Issues) on github for more information about diagnosing issues.
