# -*- encoding: utf-8 -*-
import os
import pwd

from datetime import datetime
from ConfigParser import ConfigParser

from fabric.api import run, env, put, sudo, cd, local, lcd, settings, get, \
                       hide, abort, require, prompt
from fabric.contrib.files import exists
from fabric.colors import red

os.chdir(os.path.dirname(__file__))

REMOTE_ROOT = '/opt/'

env.update(
    ENV_ROOT     = REMOTE_ROOT,
    ENV_APPS     = REMOTE_ROOT + '/apps',
    ENV_LOG      = REMOTE_ROOT + '/log',
    ENV_RUN      = REMOTE_ROOT + '/run',
    ENV_BIN      = REMOTE_ROOT + '/bin',
    ENV_CONF     = REMOTE_ROOT + '/conf',
)


# Specify keys
# env.key_filename = [path]

SERVER_ADDRESS = ''
ADMIN_USER = ''
DEPLOY_USER = ''
APP_NAME = ''


def prod():
    global SERVER_ADDRESS, ADMIN_USER, DEPLOY_USER, APP_NAME

    config = ConfigParser()
    config.read('env/deploy.cfg')

    SERVER_ADDRESS = config.get('environment', 'address')
    ADMIN_USER = config.get('environment', 'admin_user')

    if ADMIN_USER == "%ASK%":
        ADMIN_USER = prompt("Admin username: ")

    DEPLOY_USER = config.get('environment', 'deploy_user')
    APP_NAME = config.get('application', 'name')

    env.hosts = [SERVER_ADDRESS]
    env.environment = 'prod'


def config():
    env.hosts = []
    pass


def config_user():
    '''
        fab config_user

        This command will use server/users.sh.tmpl to generate a custom
        server/users.sh
    '''
    username = prompt('Username or (s)kip:')

    if username == "s":
        return

    password = prompt("Password:")
    password = local('perl -e \'print crypt(\"%s\", \"password\")\'' % (password),
                     capture=True)

    key_file_name = os.path.join(pwd.getpwnam(os.getlogin())[5],
                                 ".ssh/id_rsa.pub")
    with open(key_file_name, "r") as ssh_file, \
         open("server/users.sh.tmpl", "r") as users_file, \
         open("server/users.sh", "w") as out_file:
        pub_key = ssh_file.read()
        users_script = users_file.read()
        out_file.write(users_script.replace("##PUBKEY##", pub_key)\
                                   .replace("##USERNAME##", username)
                                   .replace("##ENCPASSWD##", password))


def server_bootstrap(hostname, fqdn, email):
    '''
        Setup a new server: server_setup:hostname,fqdn,email
        Example: server_bootstrap:loogica,loogica.net,felipecruz@loogica.net
    '''
    env.user='root'

    install_db = prompt('Install Database? (Y)es or (N)o')
    if install_db not in ('y', 'n', 'Y', 'N'):
        raise Exception("Valid Answers Y or N")

    try:
        secret_file = open('secret_key', 'r')
    except:
        raise Exception("You must have a secret_key file in this path")


    scripts = {
        'server/server_setup.sh':   '/root/server_setup.sh',
        'server/postfix.sh':        '/root/postfix.sh',
        'server/users.sh':          '/root/users.sh',
        'server/uwsgi.sh':          '/root/uwsgi.sh',
        'server/server_db_setup.sh':'/root/server_db_setup.sh',
    }

    # Upload files and fixes execution mode
    for localfile, remotefile in scripts.items():
        put(localfile, remotefile, use_sudo=True)
        if remotefile.endswith('.sh'):
            sudo('chmod +x ' + remotefile)

    sudo('/root/server_setup.sh %(hostname)s %(fqdn)s %(email)s' % locals())

    sudo("mkdir -m 755 -p %(ENV_ROOT)s" % env)
    sudo("mkdir -m 755 -p %(ENV_APPS)s" % env)
    sudo("mkdir -m 755 -p %(ENV_LOG)s" % env)
    sudo("mkdir -m 755 -p %(ENV_RUN)s" % env)
    sudo("mkdir -m 755 -p %(ENV_BIN)s" % env)
    sudo("mkdir -m 755 -p %(ENV_CONF)s" % env)
    sudo("mkdir -m 755 -p %(ENV_LOG)s/nginx" % env)
    put('secret_key', '%(ENV_CONF)s/secret_key' % env, use_sudo=True)
    sudo("touch %(ENV_RUN)s/nginx.pid" % env)
    sudo("chown -R deploy:www-data %(ENV_ROOT)s" % env)

    if install_db in ('Y', 'y'):
        sudo('/root/server_db_setup.sh')


def server_db_install():
    '''
        Install PostgreSQL
    '''
    env.user=ADMIN_USER

    scripts = {
        'server/server_db_setup.sh':   '/root/server_db_setup.sh',
    }

    # Upload files and fixes execution mode
    for localfile, remotefile in scripts.items():
        put(localfile, remotefile, use_sudo=True)
        if remotefile.endswith('.sh'):
            sudo('chmod +x ' + remotefile)

    sudo('/root/server_db_setup.sh')


def setup_app():
    '''
        Initial app setup
    '''
    env.user=ADMIN_USER

    with cd("%s" % (env.ENV_APPS)):
        sudo('mkdir %s' % (APP_NAME))

    with cd("%s" % (env.ENV_LOG)):
        sudo('mkdir %s' % (APP_NAME))

    sudo("chown -R deploy:www-data %(ENV_ROOT)s" % env)


def create_meta_info():
    local(': > %s.meta' % (APP_NAME))
    local('git rev-parse HEAD > %s.meta' % (APP_NAME))
    local('git log  --oneline -20 --format="%h %s %an" >> {0}.meta'.format(APP_NAME))
    return "%s.meta" % (APP_NAME)


def _create_git_archive(revision):
    rev = local('git rev-parse %s' % revision, capture=True)
    archive = '/tmp/%s.tar.bz2' % rev

    local('./git-archive-all.sh -c %s | bzip2 -c > %s' % (rev, archive))

    return archive


def _upload_source(revision, project_dir):
    archive = _create_git_archive(revision)
    meta_file = create_meta_info()

    timestamp = run('date +%Y-%m-%d-%Hh%Mm%Ss')
    release_dir = os.path.join(project_dir, timestamp)

    put(archive, archive)
    put(meta_file, os.path.join(env.ENV_APPS, '%s.meta' % (APP_NAME)))

    run('mkdir -p %s' % release_dir)
    run('tar jxf %s -C %s' % (archive, release_dir))

    run('rm -v %s' % (archive))
    local('rm -f %s' % (meta_file))

    return release_dir


def deploy(revision, first=False):
    '''
    Make the application deploy.

    Example: fab production deploy:1.2
    '''
    env.user = DEPLOY_USER
    project_dir = os.path.join(env.ENV_APPS, APP_NAME)
    release_dir = _upload_source(revision, project_dir)

    with cd(project_dir):
        run('rm -rf current')
        run('ln -s %s current' % release_dir)

    with cd('/etc/nginx/sites-enabled/'):
        sudo('ln -sf %s/env/app.vhost %s.vhost' % (release_dir, APP_NAME))

    with cd('/etc/supervisor/conf.d'):
        sudo('ln -sf %s/env/app_wsgi.conf %s.conf' % (release_dir, APP_NAME))

    if first:
        # admin static ln
        pass

    with cd(release_dir):
        run("make update_deps")
        if first:
            run("make server_dbinitial")
        run("make migrate_no_input")

    run('sudo service nginx restart')
    run('sudo supervisorctl reload')


def first_deploy(revision):
    deploy(revision, first=True)


def postgres_db_create(dbuser, dbname, password):
    """
        Create a Psql Database: db_create:dbuser,dbname,password

    Example: db_create:username,databasename,password
    """
    env.user=ADMIN_USER

    prod_settings_file = local('find . | grep settings/production.py', capture=True)
    temp_prod_settings_file = prod_settings_file.replace('/p', '/_p')
    local('sed "s/\$PROD_USER/%s/g;s/\$PROD_PASS/%s/g" %s > %s' % (dbuser,
                                                                   password,
                                                                   prod_settings_file,
                                                                   temp_prod_settings_file))
    local('mv %s %s' % (temp_prod_settings_file, prod_settings_file))

    sudo('psql template1 -c "CREATE USER %s WITH CREATEDB ENCRYPTED PASSWORD \'%s\'"' % (dbuser, password), user='postgres')
    sudo('createdb "%s" -O "%s"' % (dbname, dbuser), user='postgres')
    sudo('psql %s -c "CREATE EXTENSION unaccent;"' % dbname, user='postgres')
    sudo('rm -f /etc/postgresql/9.1/main/postgresql.conf')
    put('env/postgresql.conf', '/etc/postgresql/9.1/main/postgresql.conf', use_sudo=True)

    sudo('service postgresql restart')


def add_ip_to_database(ip):
    sudo('echo "host    all    all    %s/32   md5" >> /etc/postgresql/9.1/main/pg_hba.conf' % ip)
    sudo('service postgresql restart')


def nginx_setup():
    '''
        Configure nginx conf file
    '''
    env.user=DEPLOY_USER

    confs = {
        'env/nginx.conf': '/opt/conf/nginx.conf',
    }

    for localfile, remotefile in confs.items():
        put(localfile, remotefile)

    with cd('/etc/nginx/'):
        sudo('ln -sf %s/nginx.conf nginx.conf' % env.ENV_CONF)
        sudo("chown -R deploy:www-data %(ENV_ROOT)s" % env)

    sudo('service nginx restart')


def log(basename=''):
    """
    fab log                      >> List available logs.
    fab log:nginx/access         >> Tail nginx_access.log
    fab log:nginx_access         >> Tail nginx_access.log
    fab log:uwsgi                 >> Tail uwsgi.log
    """
    # List available logs
    if not basename:
        with hide('running'):
            with cd(env.PROJECT_LOG):
                run('ls -1')
                exit()

    # Normaliza o basename
    if not basename.endswith('.log'):
        basename += '.log'

    logfile = env.PROJECT_LOG + '/' + basename

    if not exists(logfile):
        abort('Logfile: %s not found.' % logfile)

    run('tail -f ' + logfile)
