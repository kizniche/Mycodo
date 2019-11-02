#!/bin/sh
#
# Usage:
# 1. Put this script somewhere in your project
# 2. Edit "$1".crontab file, it should look like this,
#    but without the # in front of the lines
#0  *   *   *   *   stuff_you_want_to_do
#15 */5 *   *   *   stuff_you_want_to_do
#*  *   1,2 *   *   and_so_on
# 3. To install the crontab, run ./crontab.sh <nameOfCronTabfile>
# 4. To remove the crontab, run ./crontab.sh <nameOfCronTabfile> --remove

cd "$(dirname "$0")" || return

test "$2" = --remove && mode=remove || mode=add

cron_unique_label="# cmID:$1 #"

crontab="$1".crontab
crontab_bak=${crontab}.bak
test -f "${crontab}" || cp "${crontab}".sample "${crontab}"

crontab_exists() {
    crontab -l 2>/dev/null | grep -x "$cron_unique_label" >/dev/null 2>/dev/null
}

# if crontab is executable
if type crontab >/dev/null 2>/dev/null; then
    if test ${mode} = add; then
        if ! crontab_exists; then
            crontab -l > "${crontab_bak}"
            echo 'Appending to crontab:'
            echo '-----------------------------------------------'
            cat "${crontab}"
            crontab -l 2>/dev/null | { cat; echo "${cron_unique_label}"; cat "${crontab}"; echo "# cm~$1 #"; } | crontab -
        else
            echo 'Crontab entry already exists, skipping ...'
            echo
        fi
        echo '-----------------------------------------------'
        echo "To remove previously added crontab entry, run: $0 $1 --remove"
        echo
    elif test ${mode} = remove; then
        if crontab_exists; then
            echo 'Removing crontab entry ...'
            crontab -l 2>/dev/null | sed -e "\?^$cron_unique_label\$?,/^# cm~$1 #\$/ d" | crontab -
        else
            echo 'Crontab entry does not exist, nothing to do.'
        fi
    fi
fi
