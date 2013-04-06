#!/bin/bash

SERVER_NAME=$1
APP_NAME=$2
PROJECT_PATH=$3

rm -f app.vhost && rm -f app_wsgi.conf && rm -f static* && rm -f deploy.cfg
./generate_site_config.sh $SERVER_NAME $APP_NAME

mkdir $PROJECT_PATH/env/
cp app.vhost $PROJECT_PATH/env/
cp app_wsgi.conf $PROJECT_PATH/env/
cp deploy.cfg $PROJECT_PATH/env/
cp conf/postgresql.conf $PROJECT_PATH/env/
cp conf/nginx.conf $PROJECT_PATH/env/
cp fabfile.py $PROJECT_PATH
cp git-archive-all.sh $PROJECT_PATH
