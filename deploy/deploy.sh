#!/bin/bash
trap 'exit' ERR

deploy() {
	echo "This is a stub."
	echo "These are lists of parameters."
	echo "$@"
}

usage() {
	me=`basename $0`
	echo "usage: ./$me <list of ip address split by spaces>"
	exit 1
}

main() {
	if [[ $@ ]]; then
		for address in "$@"; do

			deploy $address
		done
	else
		usage
	fi
}

main "$@"