#!/bin/bash
# Script to prepare target for web deployment
# Web installation that must be run only once
# when deploying for the first time should be
# placed on this script.
set -e

prepare() {
    if [ ! "dpkg-query -W nginx | awk {'print $1'} = """ ]; then
		echo "Installing nginx."
		sudo apt-get install -y nginx
    fi

	# Web
	sudo sysv-rc-conf nginx on
	sudo sysv-rc-conf --list nginx
	sudo service nginx start
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
