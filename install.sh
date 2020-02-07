#! /bin/bash

if [[ ! -d "./virgo-htc-wrapper" ]]; then
    git clone https://github.com/gabrielefronze/virgo-htc-wrapper.git
fi

cd virgo-htc-wrapper
git pull

if [[ ! -d "./virgo-htc-wrapper" ]]; then
    git submodule init
    git submodule update
else
    git submodule update --init --force
fi

cd -