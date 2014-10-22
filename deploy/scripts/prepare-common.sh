#!/bin/bash
# Script to prepare target for deployment
# Common installation that must be run only once
# (i.e. result does not change over time)
# when deploying for the first time should be
# placed on this script.
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

	if [[ `id -u cliche >/dev/null 2>cliche` ]]; then
		sudo useradd -m -G users cliche
	fi

	sudo -ucliche mkdir -p /home/cliche/etc
	sudo -ucliche mkdir -p /home/cliche/bin
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
