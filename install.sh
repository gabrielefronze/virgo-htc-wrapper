#! /bin/bash


git clone https://github.com/gabrielefronze/virgo-htc-wrapper.git
cd virgo-htc-wrapper
git pull
git submodule init
git submodule update
cd -