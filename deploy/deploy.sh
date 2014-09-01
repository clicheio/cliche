#!/bin/bash
trap 'exit' ERR

deploy() {
	echo "This is a stub."
	echo "These are lists of parameters."
	echo "$@"
}

main() {
	for address in "$@"; do
		deploy $address
	done
}

main "$@"