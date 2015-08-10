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
		if (argv[1] == "stop" || argv[1] == "start" ||
			argv[1] == "restart" || argv[1] == "debug") {
			sprintf(cmd, "/etc/init.d/mycodo %s", argv[1]);
			system(cmd);
		} else if (strcmp(argv[1], "update") == 0) {
			char updateScript[255];
			strncpy(updateScript, argv[0], sizeof(updateScript));
			dirname(updateScript);
			strncat(updateScript, "/../update-mycodo.sh", sizeof(updateScript));
			system(updateScript);
		}
	} else {
		printf("mycodo-wrapper: Allows web interface to stop and start the daemon and update the mycodo system to the latest version.\n");
	}

	return 0;
}