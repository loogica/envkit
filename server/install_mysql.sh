#!/bin/bash
set -eux

apt-get -y -q install mysql-server
apt-get -y -q install mysql-client
apt-get -y -q install libmysqlclient-dev
