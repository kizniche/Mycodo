#include <linux/limits.h>
#include <libgen.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

int upgrade_commands(char *argv, char *command) {
    char path[255];
    strncpy(path, argv, sizeof(path));
    dirname(path);

    char full_cmd[255];
    strncpy(full_cmd, "/bin/bash ", sizeof(full_cmd));
    strncat(full_cmd, path, sizeof(full_cmd));
    strncat(full_cmd, "/upgrade_commands.sh ", sizeof(full_cmd));
    strncat(full_cmd, command, sizeof(full_cmd));

    system(full_cmd);
}

int main(int argc, char *argv[]) {
	setuid(0);
	char cmd[255];

	if (argc > 1) {
		if (strcmp(argv[1], "backup-create") == 0) {
		    char path[255];
            strncpy(path, argv[0], sizeof(path));
            dirname(path);
			char restoreScript[255];
			strncpy(restoreScript, "/bin/bash ", sizeof(restoreScript));
			strncat(restoreScript, path, sizeof(restoreScript));
			strncat(restoreScript, "/upgrade_commands.sh backup-create", sizeof(restoreScript));
			system(restoreScript);
        } else if (strcmp(argv[1], "backup-delete") == 0 && (argc > 2)) {
			sprintf(cmd, "rm -rf /var/Mycodo-backups/Mycodo-backup-%s", argv[2]);
			system(cmd);
		} else if (strcmp(argv[1], "backup-restore") == 0 && (argc > 2)) {
		    char path[255];
            strncpy(path, argv[0], sizeof(path));
            dirname(path);
			char restoreScript[255];
			strncpy(restoreScript, "/bin/bash ", sizeof(restoreScript));
			strncat(restoreScript, path, sizeof(restoreScript));
			sprintf(cmd, "/upgrade_commands.sh backup-restore %s", argv[2]);
			strncat(restoreScript, cmd, sizeof(restoreScript));
			system(restoreScript);
        } else if (strcmp(argv[1], "restart") == 0) {
			sprintf(cmd, "sleep 10 && shutdown now -r");
			system(cmd);
		} else if (strcmp(argv[1], "shutdown") == 0) {
            sprintf(cmd, "sleep 10 && shutdown now -h");
            system(cmd);
		} else if (strcmp(argv[1], "daemon_restart") == 0) {
			sprintf(cmd, "service mycodo restart");
			system(cmd);
        } else if (strcmp(argv[1], "daemon_start") == 0) {
			sprintf(cmd, "service mycodo start");
			system(cmd);
		} else if (strcmp(argv[1], "daemon_stop") == 0) {
			sprintf(cmd, "service mycodo stop");
			system(cmd);
		} else if (strcmp(argv[1], "frontend_reload") == 0) {
			sprintf(cmd, "service mycodoflask reload");
			system(cmd);
        } else if (strcmp(argv[1], "influxdb_restart") == 0) {
			sprintf(cmd, "service influxdb restart");
			system(cmd);
        } else if (strcmp(argv[1], "influxdb_start") == 0) {
			sprintf(cmd, "service influxdb start");
			system(cmd);
		} else if (strcmp(argv[1], "influxdb_stop") == 0) {
			sprintf(cmd, "service influxdb stop");
			system(cmd);
		} else if (strcmp(argv[1], "influxdb_restore_metastore") == 0 && (argc > 2)) {
			sprintf(cmd, "influxd restore -metadir /var/lib/influxdb/meta %s", argv[2]);
			system(cmd);
		} else if (strcmp(argv[1], "influxdb_restore_database") == 0 && (argc > 2)) {
			sprintf(cmd, "influxd restore -database mycodo_db -datadir /var/lib/influxdb/data %s", argv[2]);
			system(cmd);
			sprintf(cmd, "chown -R influxdb.influxdb /var/lib/influxdb/data");
			system(cmd);
		} else if (strcmp(argv[1], "initialize") == 0) {
            upgrade_commands(argv[0], "initialize");
		} else if (strcmp(argv[1], "update_permissions") == 0) {
			upgrade_commands(argv[0], "update-permissions");
		} else if (strcmp(argv[1], "install_dependency") == 0 && (argc > 2)) {
		    char path[255];
            strncpy(path, argv[0], sizeof(path));
            dirname(path);
			char restoreScript[255];
			strncpy(restoreScript, "/bin/bash ", sizeof(restoreScript));
			strncat(restoreScript, path, sizeof(restoreScript));
			sprintf(cmd, "/dependencies.sh %s", argv[2]);
			strncat(restoreScript, cmd, sizeof(restoreScript));
			system(restoreScript);
        } else if (strcmp(argv[1], "install_pigpiod") == 0) {
			upgrade_commands(argv[0], "install-pigpiod");
		} else if (strcmp(argv[1], "disable_pigpiod") == 0) {
            upgrade_commands(argv[0], "disable-pigpiod");
		} else if (strcmp(argv[1], "enable_pigpiod_low") == 0) {
			upgrade_commands(argv[0], "enable-pigpiod-low");
		} else if (strcmp(argv[1], "enable_pigpiod_high") == 0) {
			upgrade_commands(argv[0], "enable-pigpiod-high");
		} else if (strcmp(argv[1], "enable_pigpiod_disabled") == 0) {
			upgrade_commands(argv[0], "enable-pigpiod-disabled");
		} else if (strcmp(argv[1], "uninstall_pigpiod") == 0) {
			upgrade_commands(argv[0], "uninstall-pigpiod");
		} else if (strcmp(argv[1], "upgrade") == 0) {
			upgrade_commands(argv[0], "upgrade");
		} else if (strcmp(argv[1], "upgrade-master") == 0) {
			upgrade_commands(argv[0], "upgrade-master");
		}
	} else {
		printf("mycodo-wrapper: A wrapper to allow the mycodo web interface\n");
		printf("                to stop and start the daemon and update the\n");
		printf("                mycodo system to the latest version.\n\n");
		printf("Usage: mycodo-wrapper start|restart|debug|update|restore [commit]\n\n");
		printf("Options:\n");
        printf("   backup-create:              Create Mycodo backup\n");
		printf("   backup-delete [DIRECTORY]:  Delete Mycodo backup [DIRECTORY]\n");
		printf("   backup-restore [DIRECTORY]: Restore Mycodo from backup [DIRECTORY]\n");
		printf("   daemon_restart:             Restart the mycodo daemon in normal mode\n");
		printf("   daemon_restart_debug:       Restart the mycodo daemon in debug mode\n");
		printf("   daemon_start:               Start the mycodo daemon\n");
		printf("   daemon_stop:                Stop the mycodo daemon\n");
		printf("   restart:                    Restart the computer after a 10 second pause\n");
		printf("   shutdown:                   Shutdown the computer after a 10 second pause\n");
		printf("   upgrade:                    Upgrade Mycodo to the latest version on github\n");
		printf("   upgrade-master:             Upgrade Mycodo to the latest master branch on github\n");
	}

	return 0;
}
