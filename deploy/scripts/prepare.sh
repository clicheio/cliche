#!/bin/bash
# Script to prepare target for deployment
set -e

prepare() {
	script_dir=$(dirname $0)
	deploy_root=$(cd $(dirname $0)/..; pwd)
	revision=$(cat $deploy_root/etc/revision.txt)
	echo "Installing prerequisities."
	sudo apt-get install -y python-software-properties
	sudo add-apt-repository ppa:fkrull/deadsnakes -y
	sudo apt-get update
	packages="$(cat $script_dir/apt-requirements.txt)"
	echo $packages
	sudo apt-get install -y $packages

	# Web
	sudo sysv-rc-conf nginx on
	sudo sysv-rc-conf --list nginx
	sudo service nginx start

	if [[ `id -u cliche >/dev/null 2>cliche` ]]; then
		sudo useradd -m -G users cliche
	fi

	sudo -ucliche mkdir -p /home/cliche/etc
	sudo -ucliche mkdir -p /home/cliche/bin

	sudo mv /tmp/cliche-deploy-$revision.tar.gz /home/cliche
	sudo -ucliche virtualenv -p `which python3.4` /home/cliche/venv_$revision
	sudo -ucliche /home/cliche/venv_$revision/bin/pip install /tmp/$revision/Cliche-*.whl
	sudo -ucliche mkdir -p /home/cliche/venv_$revision/etc
	sudo -ucliche cp $deploy_root/etc/* /home/cliche/venv_$revision/etc

	sudo -ucliche rm -f /home/cliche/bin/celery
	sudo -ucliche ln -s /home/cliche/venv_$revision/bin/celery /home/cliche/bin/celery

	sudo -ucliche rm -f /home/cliche/etc/prod.cfg.yml /home/cliche/etc/cliche-celery-beat.conf /home/cliche/etc/cliche.io
	sudo -ucliche ln -s /home/cliche/venv_$revision/etc/prod.cfg.yml /home/cliche/etc/prod.cfg.yml
	sudo -ucliche ln -s /home/cliche/venv_$revision/etc/cliche-celery-beat.conf /home/cliche/etc/cliche-celery-beat.conf
	sudo -ucliche ln -s /home/cliche/venv_$revision/etc/cliche.io /home/cliche/etc/cliche.io

	# Celery beat
	sudo rm -f /etc/init/cliche-celery-beat.conf
	sudo ln -s /home/cliche/etc/cliche-celery-beat.conf /etc/init/cliche-celery-beat.conf

	# Web
	sudo rm -f /etc/nginx/sites-available/cliche.io
	sudo ln -s /home/cliche/etc/cliche.io /etc/nginx/sites-available/cliche.io

	sudo rm -f /etc/nginx/sites-enabled/cliche.io
	sudo ln -s /etc/nginx/sites-available/cliche.io /etc/nginx/sites-enabled/cliche.io
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
