# -*- encoding: utf-8 -*-
import os
from datetime import datetime
from fabric.api import run, env, put, sudo, get


############################################################
# MYSQL TASKS                                              #
############################################################
def mysql_db_create(dbuser, dbname):
    """
    Create a Mysql Database: db_create:dbuser,dbname

    Example: db_create:nossodesconto,nossodesconto

    The password will be randomly generated.
    *  Run once.
    ** This command must be executed by a sudoer.
    """
    password = run('makepasswd --chars 32')
    assert(len(password) == 32)  # Ouch!

    sudo("mysql --defaults-file=/root/.my.cnf -e \"CREATE DATABASE %(dbname)s;\"" % locals())

    sudo("mysql --defaults-file=/root/.my.cnf -e \"CREATE USER '%(dbuser)s'@'localhost' IDENTIFIED BY '%(password)s';\"" % locals())
    sudo("mysql --defaults-file=/root/.my.cnf -e \"GRANT ALL PRIVILEGES ON %(dbname)s.* TO '%(dbuser)s'@'localhost';\"" % locals())

    # Persist database password
    my_cfg = "[client]\ndatabase=%s\nuser=%s\npassword=%s" % (dbname, dbuser, password)
    sudo("echo '%s' > %s/.my.cnf" % (my_cfg, env.PROJECT_SHARE))
    sudo('chmod 640 %(PROJECT_SHARE)s/.my.cnf' % env)
    sudo('chgrp www-data %(PROJECT_SHARE)s/.my.cnf' % env)


def mysql_db_backup(dbname):
    '''
    Get dump from server MySQL database

    Usage: fab mysql_db_backup
    '''
    remote_dbfile = '/tmp/mysql_db_backup-%s.sql.bz2' % datetime.now().strftime("%Y-%m-%d-%Hh%Mm%Ss")

    sudo('mysqldump --defaults-extra-file=/root/.my.cnf --default-character-set=utf8 -R -c --lock-tables=FALSE %(dbname)s | bzip2 -c  > %(remote_dbfile)s' % locals())

    get(remote_dbfile, 'tmp/')

    #remove the temporary remote dump file
    sudo('rm ' + remote_dbfile)


def mysql_db_restore(dbname, local_file):
    remote_bz2file = os.path.join('/tmp', os.path.basename(local_file))
    remote_sqlfile = os.path.splitext(remote_bz2file)[0]

    put(local_file, remote_bz2file)
    run('bunzip2 ' + remote_bz2file)

    sudo('mysql --defaults-extra-file=/root/.my.cnf -e "DROP DATABASE %(dbname)s; CREATE DATABASE %(dbname)s;"' % locals())
    sudo('mysql --defaults-extra-file=/root/.my.cnf %(dbname)s < %(remote_sqlfile)s' % locals())

    # cleanup
    sudo('rm ' + remote_sqlfile)
