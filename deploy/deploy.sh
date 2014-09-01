#!/bin/bash
set -e

upload() {
	ssh $1 mkdir /tmp/$2
	scp deploy/prepare.sh deploy/promote.sh deploy/upgrade.sh dist/*.whl $1:/tmp/$2
	ssh $1 chmod +x /tmp/$2/prepare.sh /tmp/$2/promote.sh /tmp/$2/upgrade.sh
}

usage() {
	me=$(basename $0)
	echo "usage: ./$me <list of ip address split by spaces>"
	exit 1
}

main() {
	if [[ $@ ]]; then
		workdir=$(dirname $0)/..
		cd $workdir
		rm -rf dist/
		revision=$(cat .git/$(awk '{print $2}' .git/HEAD))
		python setup.py egg_info -b "_$revision" bdist_wheel
			for address in "$@"; do
				echo "Deploying to $address."
				temp=$(upload $address $revision)
				ssh $address /tmp/$revision/prepare.sh
				ssh $address /tmp/$revision/upgrade.sh
			done
			for address in "$@"; do
				ssh $address /tmp/$revision/promote.sh
			done
	else
		usage
	fi
}

main "$@"
