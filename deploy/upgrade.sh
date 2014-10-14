#!/bin/bash
# Script to upgrade deployment on the target
set -e

upgrade() {
	# pyvenv-3.4 $HOME/venv_$(cat $(dirname $0)/revision.txt)
	virtualenv -p `which python3.4` $HOME/venv_$(cat $(dirname $0)/revision.txt)
	$HOME/venv_$(cat $(dirname $0)/revision.txt)/bin/pip install /tmp/$(cat $(dirname $0)/revision.txt)/Cliche-*.whl
	mkdir -p $HOME/venv_$(cat $(dirname $0)/revision.txt)/etc
	cp $(dirname $0)/prod.cfg.yml $HOME/venv_$(cat $(dirname $0)/revision.txt)/etc
	cp $(dirname $0)/revision.txt $HOME/venv_$(cat $(dirname $0)/revision.txt)/etc
	cp $(dirname $0)/cliche.io $HOME/venv_$(cat $(dirname $0)/revision.txt)/etc

	sudo cp $HOME/venv_$(cat $(dirname $0)/revision.txt)/etc/cliche.io /etc/nginx/sites-available/cliche.io
	if [ -h /etc/nginx/sites-enabled/cliche.io  ]; then
		sudo ln -s /etc/nginx/sites-available/cliche.io /etc/nginx/sites-enabled/cliche.io
	fi
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
# vim: set filetype=sh ts=4 sw=4 sts=4 noet
