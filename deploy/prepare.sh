#!/bin/bash
# Script to prepare target for deployment
set -e

prepare() {
	echo "Installing prerequisities."
	sudo apt-get install -y python-software-properties
	sudo add-apt-repository ppa:fkrull/deadsnakes -y
	sudo apt-get update
	sudo apt-get install -y $(cat apt-requirements.txt)
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
