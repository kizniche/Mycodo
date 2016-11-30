#include <linux/limits.h>
#include <libgen.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
	setuid(0);
	char cmd[255];

	if (argc > 1) {
		if (strcmp(argv[1], "start") == 0) {

			sprintf(cmd, "/../mycodo_daemon.py");
			system(cmd);

		} else if (strcmp(argv[1], "restart") == 0) {

			sprintf(cmd, "/../mycodo_client.py -t");
			system(cmd);
			sprintf(cmd, "/../mycodo_daemon.py");
			system(cmd);

		} else if (strcmp(argv[1], "debug") == 0) {

			sprintf(cmd, "/../mycodo_client.py -t");
			system(cmd);
			sprintf(cmd, "/../mycodo_daemon.py -d");
			system(cmd);

		} else if (strcmp(argv[1], "restore") == 0 && (argc > 2)) {

			char updateScript[255];
			strncpy(updateScript, argv[0], sizeof(updateScript));
			dirname(updateScript);
			sprintf(cmd, "/restore_mycodo.sh %s", argv[2]);
			strncat(updateScript, cmd, sizeof(updateScript));
			system(updateScript);

		} else if (strcmp(argv[1], "delete-backup") == 0 && (argc > 2)) {

			sprintf(cmd, "rm -rf /var/Mycodo-backups/%s", argv[2]);
			system(cmd);

		} else if (strcmp(argv[1], "backup") == 0) {

			char updateScript[255];
			strncpy(updateScript, argv[0], sizeof(updateScript));
			dirname(updateScript);
			strncat(updateScript, "/update_mycodo.sh backup", sizeof(updateScript));
			system(updateScript);

		} else if (strcmp(argv[1], "upgrade") == 0) {

			char updateScript[255];
			strncpy(updateScript, argv[0], sizeof(updateScript));
			dirname(updateScript);
			strncat(updateScript, "/update_mycodo_release.sh", sizeof(updateScript));
			system(updateScript);

		} else if (strcmp(argv[1], "updatecheck") == 0) {

			char updateScript[255];
			strncpy(updateScript, argv[0], sizeof(updateScript));
			dirname(updateScript);
			strncat(updateScript, "/update_mycodo.sh updatecheck", sizeof(updateScript));
			int status;
			if((status = system(updateScript)) != -1) {
                return WEXITSTATUS(status);
        	}

		}
	} else {

		printf("mycodo-wrapper: A wrapper to allow the mycodo web interface\n");
		printf("                to stop and start the daemon and update the\n");
		printf("                mycodo system to the latest version.\n\n");
		printf("Usage: mycodo-wrapper start|restart|debug|update|restore [commit]\n\n");
		printf("Options:\n");
		printf("   start:                  Start the mycodo daemon\n");
		printf("   restart:                Restart the mycodo daemon in normal mode\n");
		printf("   debug:                  Restart the mycodo daemon in debug mode\n");
		printf("   backup:                 Create a backup of Mycodo\n");
		printf("   delete-backup [folder]: Delete Mycodo backup folder named [folder]\n");
		printf("   upgrade:                Upgrade Mycodo to the latest release on github\n");
		printf("   restore [commit]:       Restore Mycodo to a backed up version\n");
		printf("   updatecheck:            Check for a newer version of Mycodo on github\n\n");
	}

	return 0;
}
