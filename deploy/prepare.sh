#!/bin/bash
# Script to prepare target for deployment
set -e

prepare() {
	echo "Installing prerequisities."
	sudo apt-get install -y python-software-properties
	sudo add-apt-repository ppa:fkrull/deadsnakes -y
	sudo apt-get update
	packages="$(cat $(dirname $0)/apt-requirements.txt)"
	echo $packages
	sudo apt-get install -y $packages
	sudo cp $(dirname $0)/cliche.io /etc/nginx/sites-available/cliche.io
	if [ ! -h /etc/nginx/sites-enabled/cliche.io  ]; then
		sudo ln -s /etc/nginx/sites-available/cliche.io /etc/nginx/sites-enabled/cliche.io
	fi
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
