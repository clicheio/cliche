#!/bin/bash
# Script to prepare target for celery beat deployment
# Web installation that must be run only once
# when deploying for the first time should be
# placed on this script.
set -e

prepare() {
	sudo ln -fs /home/cliche/etc/cliche-celery-beat.conf /etc/init/cliche-celery-beat.conf
}

not_compatible_with_os() {
	echo "This script can only be run on Debian GNU/Linux or Ubuntu."
	exit 1
}

main() {
	if [[ -f /etc/os-release ]]; then
		. /etc/os-release
		if [[ $NAME = "Debian GNU/Linux" ]] || [[ $NAME = "Ubuntu" ]]; then
			prepare "$@"
		else
			not_compatible_with_os
		fi
	else
		not_compatible_with_os
	fi
}

main "$@"
# vim: set filetype=sh ts=4 sw=4 sts=4 noet
