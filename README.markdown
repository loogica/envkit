# Loogica Simple Environment Setup Tools

## Motivation

If you just want to easily setup a linux environment ready to run
Python wsgi compatible apps, this kit can help you.

**If you're not from Brasil, maybe you'll have to change `server/server_setup.sh`
  timezone, currently configured to America/Sao_Paulo**

## Django Apps

This kit is intended to work with Python WSGI Apps but currently we only use and test it against
Django apps.

This is how we bootstrap our Django Projects

```
django-admin.py startproject --template=https://github.com/loogica/loogica_project_template/archive/master.zip my_new_startup
cd my_new_startup\my_new_startup
django-admin.py startapp --template=https://github.com/loogica/loogica_app_template/archive/master.zip startup_app
```

You MUST modify 2 files: `Makefile` and project_root/settings/base.py and add your app to INSTALLED_APPS

## How it works?

There are 3 phases:

1. Setup your credentials and configure a Python Wsgi Friendly machine.
2. Install envkit in your project.
3. Setup a machine to run some specific app. This phase requires a `env/deploy.cfg` file.

## Bootstraping Machines

First of all you need to set up your credentials helper file:

### Preparing

```sh
fab config config_user
```

This task will ask for a `username` and `password`. This password will be the sudo password
for the user `username`.

### Creating 

This task will ask for a IP Address and at the end, the username picked in the previous
step will be able to connect with this machine using your public key. You'll also have
to choose between install or not Postgresql

```sh
fab config server_bootstrap:loogica,loogica.net,felipecruz@loogica.net
```

## Installing envkit on your projet

```sh
./install_kit.sh SERVERNAME_OR_IP APP_NAME /full/path/to/app/root
```

## Running per-project Tasks

After the previous phase, you should have `env/deploy.cfg` in your project root. Change
it if needed but the default file works fine for initial setups.

### Go to your project root

```sh
cd /full/path/to/app/root
```

### Setup App environment

```sh
fab prod setup_app
```

### Create App database

```sh
fab prod postgres_db_create:dbuser,dbname,password
```

### Setup Nginx Config

```sh
fab prod nginx_setup
```

## Deploy restrictions

Your project root must have a Makefile in order to make the deploy possible. Here's an example:

```Makefile
server_dbinitial:
	python manage.py syncdb --noinput && python manage.py createsuperuser --user admin --email admin@admin.com

migrate_no_input:
	python manage.py migrate --noinput $(APPS)

update_deps:
	sudo pip install -r requirements.txt
```

If you're running, for instance, a Flask app, some targets may be empty.

### First Deploy

```sh
fab prod first_deploy:HEAD
```

### Regular deploy

```sh
fab prod deploy:HEAD
```


## License

```
This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>
```
