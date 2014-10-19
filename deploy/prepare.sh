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
	sudo sysv-rc-conf nginx on
	sudo sysv-rc-conf --list nginx
	sudo service nginx start

	if [[ ! `id -u cliche >/dev/null 2>cliche` ]]; then
		sudo useradd -m -G users cliche
	fi

	sudo -ucliche mkdir $HOME/etc
	sudo -ucliche mkdir $HOME/bin

	sudo -ucliche virtualenv -p `which python3.4` $HOME/venv_$(cat $(dirname $0)/revision.txt)
	sudo -ucliche $HOME/venv_$(cat $(dirname $0)/revision.txt)/bin/pip install /tmp/$(cat $(dirname $0)/revision.txt)/Cliche-*.whl
	sudo -ucliche mkdir -p $HOME/venv_$(cat $(dirname $0)/revision.txt)/etc
	sudo -ucliche cp $(dirname $0)/prod.cfg.yml $HOME/venv_$(cat $(dirname $0)/revision.txt)/etc
	sudo -ucliche cp $(dirname $0)/revision.txt $HOME/venv_$(cat $(dirname $0)/revision.txt)/etc
	sudo -ucliche cp $(dirname $0)/cliche.io $HOME/venv_$(cat $(dirname $0)/revision.txt)/etc

	sudo -ucliche rm -f $HOME/bin/celery $HOME/etc/prod.cfg.py
	sudo -ucliche ln -s $HOME/venv_$(cat $(dirname $0)/revision.txt)/bin/celery $HOME/bin/celery
	sudo -ucliche ln -s $HOME/venv_$(cat $(dirname $0)/revision.txt)/bin/prod.cfg.py $HOME/etc/prod.cfg.py

	sudo rm -f /etc/nginx/sites-available/cliche.io /etc/nginx/sites-enabled/cliche.io
	sudo ln -s $HOME/venv_$(cat $(dirname $0)/revision.txt)/etc/cliche.io /etc/nginx/sites-available/cliche.io
	sudo ln -s $HOME/venv_$(cat $(dirname $0)/revision.txt)/etc/cliche.io /etc/nginx/sites-enabled/cliche.io
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
