#include <linux/limits.h>
#include <libgen.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

int upgrade_commands(char *argv, char *command) {
  char path[256];
  strncpy(path, argv, sizeof(path));
  dirname(path);
  char full_cmd[512];
  strncpy(full_cmd, "/bin/bash ", sizeof(full_cmd) - 1);
  strncat(full_cmd, path, sizeof(full_cmd) - 1);
  strncat(full_cmd, "/upgrade_commands.sh ", sizeof(full_cmd) - 1);
  strncat(full_cmd, command, sizeof(full_cmd) - 1);
  system(full_cmd);
}

int main(int argc, char *argv[]) {
  setuid(0);
  char cmd[1024];

  if (argc > 1) {
    if (strcmp(argv[1], "backup-create") == 0) {
      char path[256];
      strncpy(path, argv[0], sizeof(path) - 1);
      dirname(path);
      char restoreScript[512];
      strncpy(restoreScript, "/bin/bash ", sizeof(restoreScript) - 1);
      strncat(restoreScript, path, sizeof(restoreScript) - 1);
      strncat(restoreScript, "/upgrade_commands.sh backup-create", sizeof(restoreScript) - 1);
      system(restoreScript);
    } else if (strcmp(argv[1], "backup-delete") == 0 && (argc > 2)) {
      sprintf(cmd, "rm -rf /var/Mycodo-backups/Mycodo-backup-%s", argv[2]);
      system(cmd);
    } else if (strcmp(argv[1], "backup-restore") == 0 && (argc > 2)) {
      char path[256];
      strncpy(path, argv[0], sizeof(path) - 1);
      dirname(path);
      char restoreScript[512];
      strncpy(restoreScript, "/bin/bash ", sizeof(restoreScript) - 1);
      strncat(restoreScript, path, sizeof(restoreScript) - 1);
      sprintf(cmd, "/upgrade_commands.sh backup-restore %s", argv[2]);
      strncat(restoreScript, cmd, sizeof(restoreScript) - 1);
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
    } else if (strcmp(argv[1], "delete_upload_dir") == 0) {
      sprintf(cmd, "rm -rf /var/mycodo-root/upload");
      system(cmd);
    } else if (strcmp(argv[1], "frontend_reload") == 0) {
      sprintf(cmd, "service mycodoflask reload");
      system(cmd);
    } else if (strcmp(argv[1], "frontend_restart") == 0) {
      sprintf(cmd, "service mycodoflask restart");
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
    } else if (strcmp(argv[1], "influxdb_restore_mycodo_db") == 0 && (argc > 2)) {
      sprintf(cmd, "influxd restore -portable -db mycodo_db -newdb mycodo_db_bak %s", argv[2]);
      system(cmd);
    } else if (strcmp(argv[1], "upgrade_database") == 0) {
      upgrade_commands(argv[0], "update-alembic");
    } else if (strcmp(argv[1], "initialize") == 0) {
      upgrade_commands(argv[0], "initialize");
    } else if (strcmp(argv[1], "update_dependencies") == 0) {
      upgrade_commands(argv[0], "update-dependencies");
    } else if (strcmp(argv[1], "update_permissions") == 0) {
      upgrade_commands(argv[0], "update-permissions");
    } else if (strcmp(argv[1], "install_dependency") == 0 && strcmp(argv[2], "pip-pypi") == 0 && (argc == 4)) {
      char path[256];
      strncpy(path, argv[0], sizeof(path) - 1);
      dirname(path);
      char restoreScript[1024];
      strncpy(restoreScript, "/bin/bash ", sizeof(restoreScript) - 1);
      strncat(restoreScript, path, sizeof(restoreScript) - 1);
      sprintf(cmd, "/dependencies.sh pip-pypi %s", argv[3]);
      strncat(restoreScript, cmd, sizeof(restoreScript) - 1);
      system(restoreScript);
    } else if (strcmp(argv[1], "install_dependency") == 0 && strcmp(argv[2], "apt") == 0 && (argc == 4)) {
      char path[256];
      strncpy(path, argv[0], sizeof(path) - 1);
      dirname(path);
      char restoreScript[1024];
      strncpy(restoreScript, "/bin/bash ", sizeof(restoreScript) - 1);
      strncat(restoreScript, path, sizeof(restoreScript) - 1);
      sprintf(cmd, "/dependencies.sh apt %s", argv[3]);
      strncat(restoreScript, cmd, sizeof(restoreScript) - 1);
      system(restoreScript);
    } else if (strcmp(argv[1], "install_dependency") == 0 && strcmp(argv[2], "internal") == 0 && (argc == 4)) {
      char path[256];
      strncpy(path, argv[0], sizeof(path) - 1);
      dirname(path);
      char restoreScript[1024];
      strncpy(restoreScript, "/bin/bash ", sizeof(restoreScript) - 1);
      strncat(restoreScript, path, sizeof(restoreScript) - 1);
      sprintf(cmd, "/dependencies.sh internal %s", argv[3]);
      strncat(restoreScript, cmd, sizeof(restoreScript) - 1);
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
    } else if (strcmp(argv[1], "upgrade-release-wipe") == 0 && (argc > 2)) {
      char path[256];
      strncpy(path, argv[0], sizeof(path) - 1);
      dirname(path);
      char restoreScript[256];
      strncpy(restoreScript, "/bin/bash ", sizeof(restoreScript) - 1);
      strncat(restoreScript, path, sizeof(restoreScript) - 1);
      sprintf(cmd, "/upgrade_commands.sh upgrade-release-wipe %s", argv[2]);
      strncat(restoreScript, cmd, sizeof(restoreScript) - 1);
      system(restoreScript);
    } else if (strcmp(argv[1], "upgrade-release-major") == 0 && (argc > 2)) {
      char path[256];
      strncpy(path, argv[0], sizeof(path) - 1);
      dirname(path);
      char restoreScript[256];
      strncpy(restoreScript, "/bin/bash ", sizeof(restoreScript) - 1);
      strncat(restoreScript, path, sizeof(restoreScript) - 1);
      sprintf(cmd, "/upgrade_commands.sh upgrade-release-major %s", argv[2]);
      strncat(restoreScript, cmd, sizeof(restoreScript) - 1);
      system(restoreScript);
    } else if (strcmp(argv[1], "upgrade-master") == 0) {
      upgrade_commands(argv[0], "upgrade-master");
    }
  } else {
    printf("Mycodo Wrapper: A wrapper to allow the mycodo web interface\n");
    printf("                to perform superuser actions.\n\n");
    printf("Usage: mycodo_wrapper [command]\n\n");
    printf("Commands:\n");
    printf("   backup-create:              Create Mycodo backup\n");
    printf("   backup-delete [DIRECTORY]:  Delete Mycodo backup [DIRECTORY]\n");
    printf("   backup-restore [DIRECTORY]: Restore Mycodo from backup [DIRECTORY]\n");
    printf("   daemon_restart:             Restart the mycodo daemon in normal mode\n");
    printf("   daemon_restart_debug:       Restart the mycodo daemon in debug mode\n");
    printf("   daemon_start:               Start the mycodo daemon\n");
    printf("   daemon_stop:                Stop the mycodo daemon\n");
    printf("   database_upgrade:           Upgrade the database\n");
    printf("   delete_upload_dir:          Delete the directory uploads are saved to from the UI\n");
    printf("   frontend_reload:            Reload the mycodo frontend\n");
    printf("   frontend_restart:           Restart the mycodo frontend\n");
    printf("   influxdb_start:             Start influxdb\n");
    printf("   influxdb_stop:              Stop influxdb\n");
    printf("   influxdb_restart:           Restart influxdb\n");
    printf("   influxdb_restore_mycodo_db  Restore influxdb database mycodo_db to mycodo_db_bak\n");
    printf("   initialize:                 Run the Mycodo initialization sequence\n");
    printf("   update_dependencies:        Install unmet dependencies and update installed dependencies\n");
    printf("   update_permissions:         Set the Mycodo file/folder permissions\n");
    printf("   restart:                    Restart the computer after a 10 second pause\n");
    printf("   shutdown:                   Shutdown the computer after a 10 second pause\n");
    printf("   upgrade-release-wipe:       Upgrade Mycodo to the latest major version on github and wipe database and virtualenv\n");
    printf("   upgrade-release-major:      Upgrade Mycodo to the latest major version on github\n");
    printf("   upgrade-master:             Upgrade Mycodo to the latest master branch on github\n");
  }

  return 0;
}
