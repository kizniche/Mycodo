#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
	setuid(0);
	char cmd[255];

	if (argc > 1) {
		sprintf(cmd, "/etc/init.d/mycodo %s", argv[1]);
		system(cmd);
	} else {
		printf("The command had no other arguments.\n");
	}

	return 0;
}