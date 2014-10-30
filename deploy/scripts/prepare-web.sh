#!/bin/bash
# Script to prepare target for web deployment
# Web installation that must be run only once
# when deploying for the first time should be
# placed on this script.
set -e

prepare() {
    if ! dpkg-query -Wf'${db:Status-abbrev}' nginx 2>/dev/null | grep -q '^i'; then
		echo "Installing nginx."
		sudo apt-get install -y nginx
    fi

	sudo ln -sf /home/cliche/etc/cliche.io /etc/nginx/sites-available/cliche.io
	sudo ln -sf /etc/nginx/sites-available/cliche.io /etc/nginx/sites-enabled/cliche.io

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
