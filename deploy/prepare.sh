#!/bin/bash
# Script to prepare target for deployment
trap 'exit' ERR

prepare() {
	echo "This is a stub."
	echo "These are lists of parameters."
	echo "$@"
}

not_compatible_with_os() {
	echo "This script can only be run on Debian GNU/Linux."
	exit 1
}

main() {
	if [[ -f /etc/os-release ]]
	then
		. /etc/os-release
		if [[ $NAME = "Debian GNU/Linux" ]]
		then
			prepare "$@"
		else
			not_compatible_with_os
		fi
	else
		not_compatible_with_os
	fi
}

main "$@"
