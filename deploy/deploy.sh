#!/bin/bash
trap 'exit' ERR

deploy() {
	echo "This is a stub."
	echo "These are lists of parameters."
	echo "$@"
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
		python setup.py egg_info -b "-$revision" bdist_wheel
			for address in "$@"; do
				deploy $address
			done
	else
		usage
	fi
}

main "$@"
