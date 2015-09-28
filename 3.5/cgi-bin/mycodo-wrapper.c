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
		if ((strcmp(argv[1], "stop") == 0) || (strcmp(argv[1], "start") == 0) ||
			(strcmp(argv[1], "restart") == 0) || (strcmp(argv[1], "debug") == 0)) {
			sprintf(cmd, "/etc/init.d/mycodo %s", argv[1]);
			system(cmd);
		} else if (strcmp(argv[1], "restore") == 0 && strcmp(argv[1], "restore") == 0) {
			char updateScript[255];
			strncpy(updateScript, argv[0], sizeof(updateScript));
			dirname(updateScript);
			strncat(updateScript, "/../restore-mycodo.sh update", sizeof(updateScript));
			system(updateScript);
		} else if (strcmp(argv[1], "update") == 0) {
			char updateScript[255];
			strncpy(updateScript, argv[0], sizeof(updateScript));
			dirname(updateScript);
			strncat(updateScript, "/../update-mycodo.sh update", sizeof(updateScript));
			system(updateScript);
		} else if (strcmp(argv[1], "updatecheck") == 0) {
			char updateScript[255];
			strncpy(updateScript, argv[0], sizeof(updateScript));
			dirname(updateScript);
			strncat(updateScript, "/../update-mycodo.sh updatecheck", sizeof(updateScript));
			int status;
			if((status = system(updateScript)) != -1) {
                return WEXITSTATUS(status);
        	}
		}
	} else {
		printf("mycodo-wrapper: A wrapper to allow the mycodo web interface\n");
		printf("                to stop and start the daemon and update the\n");
		printf("                mycodo system to the latest version.\n\n");
		printf("Usage: mycodo-wrapper stop|start|restart|debug|update|restore [commit]\n\n");
		printf("Options:\n");
		printf("   stop:             Stop the mycodo daemon\n");
		printf("   start:            Start the mycodo daemon\n");
		printf("   restart:          Restart the mycodo daemon in normal mode\n");
		printf("   debug:            Restart the mycodo daemon in debug mode\n");
		printf("   update:           Update Mycodo to the latest version on github\n");
		printf("   restore [commit]: Restore Mycodo to a backed up version\n");
		printf("   updatecheck:      Check for a newer version of Mycodo on github\n\n");
	}

	return 0;
}