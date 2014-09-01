#!/bin/bash
# Script to upgrade deployment on the target
set -e

upgrade() {
	pyvenv $HOME/venv_$(cat revision.txt)
	$HOME/venv_$(cat revision.txt)/bin/pip install *.whl
}

not_compatible_with_os() {
	echo "This script can only be run on Debian GNU/Linux or Ubuntu."
	exit 1
}

main() {
	if [[ -f /etc/os-release ]]
	then
		. /etc/os-release
		if [[ $NAME = "Debian GNU/Linux" ]] || [[ $NAME = "Ubuntu" ]]; then
			upgrade "$@"
		else
			not_compatible_with_os
		fi
	else
		not_compatible_with_os
	fi
}

main "$@"
