#!/bin/bash
# Script to upgrade deployment on the target
set -e

upgrade() {
	pyvenv-3.4 $HOME/venv_$(cat $(dirname $0)/revision.txt)
	$HOME/venv_$(cat $(dirname $0)/revision.txt)/local/bin/pip install *.whl
}

not_compatible_with_os() {
	echo "This script can only be run on Debian GNU/Linux or Ubuntu."
	exit 1
}

main() {
	if [[ -f /etc/os-release ]]; then
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
