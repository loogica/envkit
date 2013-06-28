# coding: utf-8
from fabric.api import env, run, require, abort, task, warn_only, put
from fabric.colors import red, yellow
from fabric.contrib.console import confirm
from fabric.contrib.files import exists
from .helpers import ask


@task
def server(hostname, fqdn, email):
    '''
    Setup a new server: server_setup:hostname,fqdn,email

    Example: server_setup:palmas,palmas.dekode.com.br,admin@dekode.com.br
    '''
    env.user = 'root'

    files = [
        'server/server_setup.sh',
        'server/postfix.sh',
        'server/watchdog.sh',
        'server/uwsgi.sh',
    ]

    # Choose database
    answer = ask('Which database to install? [Postgres, Mysql, None]',
        options={
            'P': ['server/pg_hba.conf', 'server/postgresql.sh'],
            'M': ['server/mysql.sh'],
            'N': []})

    files.extend(answer)

    # Upload files and fixes execution mode
    for localfile in files.items():
        put(localfile, '~root/', mirror_local_mode=True)

    run('~root/server_setup.sh %(hostname)s %(fqdn)s %(email)s' % locals())


@task
def application():
    """
    Setup application directories: fab stage setup.application

    We use 1 user for 1 app with N environments.
    This makes easy to give deploy access to different ssh keys.

    The project directory layout is:

      ~/user (rootdir)
      +---- /stage.myproject.com.br (appdir)
      |     +---- /releases
      |     |     +---- /current
      |     +---- /share
      +---- /logs
            +---- /stage.myproject.com.br (logs)
    """
    require('PROJECT', provided_by=['stage', 'production'])

    if exists(env.PROJECT.appdir):
        print(yellow('Application detected at: %(appdir)s' % env.PROJECT))
        if confirm(red('Rebuild application?'), default=False):
            run('rm -rf %(appdir)s' % env.PROJECT)
        else:
            abort('Application already exists.')

    # Create directory structure
    run('mkdir -m 755 -p %(appdir)s' % env.PROJECT)
    run('mkdir -m 755 -p %(releases)s' % env.PROJECT)
    run('mkdir -m 755 -p %(current)s' % env.PROJECT)
    run('mkdir -m 755 -p %(share)s' % env.PROJECT)
    run('mkdir -m 755 -p %(media)s' % env.PROJECT)
    run('mkdir -m 755 -p %(tmp)s' % env.PROJECT)

    with warn_only():
        run('mkdir -m 755 -p %(logs)s' % env.PROJECT)

    # Initialize environment settings file
    run('echo "[settings]\n" >> %(settings)s' % env.PROJECT)
    run('chmod 600 %(settings)s' % env.PROJECT)


@task
def delete_app():
    """
    Delete an application instance.
    """
    require('PROJECT', provided_by=['stage', 'production'])

    question = red('Do you want to DELETE the app at %(appdir)s ?' % env.PROJECT)

    if exists(env.PROJECT.appdir) and confirm(question, default=False):
        run('rm -rf %(appdir)s' % env.PROJECT)
