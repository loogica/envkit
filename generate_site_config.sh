#!/bin/bash

SERVER=$1
APP=$2

sed "s/\$SERVER_NAME/$SERVER/g;s/\$APP_NAME/$APP/g" conf/templates/nginx_static_site.conf.tmpl >> static_conf.vhost
sed "s/\$SERVER_NAME/$SERVER/g;s/\$APP_NAME/$APP/g" conf/templates/nginx.vhost.tmpl >> app.vhost
sed "s/\$SERVER_NAME/$SERVER/g;s/\$APP_NAME/$APP/g" conf/templates/uwsgi.conf.tmpl >> app_wsgi.conf
sed "s/\$SERVER_NAME/$SERVER/g;s/\$APP_NAME/$APP/g" conf/templates/deploy.cfg.tmpl >> deploy.cfg
