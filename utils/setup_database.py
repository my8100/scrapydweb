# coding: utf-8
import os
import re
import sys


DB_APSCHEDULER = 'scrapydweb_apscheduler'
DB_TIMERTASKS = 'scrapydweb_timertasks'
DB_METADATA = 'scrapydweb_metadata'
DB_JOBS = 'scrapydweb_jobs'
DBS = [DB_APSCHEDULER, DB_TIMERTASKS, DB_METADATA, DB_JOBS]

PATTERN_MYSQL = re.compile(r'mysql://(.+?)(?::(.+?))?@(.+?):(\d+)')
PATTERN_POSTGRESQL = re.compile(r'postgres://(.+?)(?::(.+?))?@(.+?):(\d+)')
PATTERN_SQLITE = re.compile(r'sqlite:///(.+)$')

SCRAPYDWEB_TESTMODE = os.environ.get('SCRAPYDWEB_TESTMODE', 'False').lower() == 'true'


def test_database_url_pattern(database_url):
    m_mysql = PATTERN_MYSQL.match(database_url)
    m_postgres = PATTERN_POSTGRESQL.match(database_url)
    m_sqlite = PATTERN_SQLITE.match(database_url)
    return m_mysql, m_postgres, m_sqlite


def setup_database(database_url, database_path):
    database_url = re.sub(r'\\', '/', database_url)
    database_url = re.sub(r'/$', '', database_url)
    database_path = re.sub(r'\\', '/', database_path)
    database_path = re.sub(r'/$', '', database_path)

    m_mysql, m_postgres, m_sqlite = test_database_url_pattern(database_url)
    if m_mysql:
        setup_mysql(*m_mysql.groups())
    elif m_postgres:
        setup_postgresql(*m_postgres.groups())
    else:
        database_path = m_sqlite.group(1) if m_sqlite else database_path
        database_path = os.path.abspath(database_path)
        database_path = re.sub(r'\\', '/', database_path)
        database_path = re.sub(r'/$', '', database_path)
        if not os.path.isdir(database_path):
            os.mkdir(database_path)

    if m_mysql or m_postgres:
        APSCHEDULER_DATABASE_URI = '/'.join([database_url, DB_APSCHEDULER])
        SQLALCHEMY_DATABASE_URI = '/'.join([database_url, DB_TIMERTASKS])
        SQLALCHEMY_BINDS = {
            'metadata': '/'.join([database_url, DB_METADATA]),
            'jobs': '/'.join([database_url, DB_JOBS])
        }
    else:
        # db names for backward compatibility
        APSCHEDULER_DATABASE_URI = 'sqlite:///' + '/'.join([database_path, 'apscheduler.db'])
        # http://flask-sqlalchemy.pocoo.org/2.3/binds/#binds
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + '/'.join([database_path, 'timer_tasks.db'])
        SQLALCHEMY_BINDS = {
            'metadata': 'sqlite:///' + '/'.join([database_path, 'metadata.db']),
            'jobs': 'sqlite:///' + '/'.join([database_path, 'jobs.db'])
        }

    if SCRAPYDWEB_TESTMODE:
        print("DATABASE_PATH: %s" % database_path)
        print("APSCHEDULER_DATABASE_URI: %s" % APSCHEDULER_DATABASE_URI)
        print("SQLALCHEMY_DATABASE_URI: %s" % SQLALCHEMY_DATABASE_URI)
        print("SQLALCHEMY_BINDS: %s" % SQLALCHEMY_BINDS)
    return APSCHEDULER_DATABASE_URI, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_BINDS, database_path


def drop_database(cur, dbname):
    sql = "DROP DATABASE %s" % dbname
    print(sql)
    try:
        cur.execute(sql)
    except Exception as err:
        print(err)


def setup_mysql(username, password, host, port):
    """
    ModuleNotFoundError: No module named 'MySQLdb'
    pip install mysqlclient
    Python 2: pip install mysqlclient -> MySQLdb/_mysql.c(29) :
    fatal error C1083: Cannot open include file: 'mysql.h': No such file or directory
    https://stackoverflow.com/questions/51294268/pip-install-mysqlclient-returns-fatal-error-c1083-cannot-open-file-mysql-h
    https://www.lfd.uci.edu/~gohlke/pythonlibs/#mysqlclient
    pip install "path to the downloaded mysqlclient.whl file"
    """
    require_version = '0.9.3'  # Dec 18, 2018
    install_command = "pip install --upgrade pymysql"
    try:
        import pymysql
        assert pymysql.__version__ >= require_version, install_command
    except (ImportError, AssertionError):
        sys.exit("Run command: %s" % install_command)
    else:
        # Run scrapydweb: ModuleNotFoundError: No module named 'MySQLdb'
        pymysql.install_as_MySQLdb()

    conn = pymysql.connect(host=host, port=int(port), user=username, password=password,
                           charset='utf8', cursorclass=pymysql.cursors.DictCursor)
    cur = conn.cursor()
    for dbname in DBS:
        if SCRAPYDWEB_TESTMODE:
            drop_database(cur, dbname)
        # pymysql.err.ProgrammingError: (1007, "Can't create database 'scrapydweb_apscheduler'; database exists")
        # cur.execute("CREATE DATABASE IF NOT EXISTS %s CHARACTER SET 'utf8' COLLATE 'utf8_general_ci'" % dbname)
        try:
            cur.execute("CREATE DATABASE %s CHARACTER SET 'utf8' COLLATE 'utf8_general_ci'" % dbname)
        except Exception as err:
            if 'exists' in str(err):
                pass
            else:
                raise
    cur.close()
    conn.close()


def setup_postgresql(username, password, host, port):
    """
    https://github.com/my8100/notes/blob/master/back_end/the-flask-mega-tutorial.md
    When working with database servers such as MySQL and PostgreSQL,
    you have to create the database in the database server before running upgrade.
    """
    require_version = '2.7.7'  # Jan 23, 2019
    install_command = "pip install --upgrade psycopg2"
    try:
        import psycopg2
        assert psycopg2.__version__ >= require_version, install_command
    except (ImportError, AssertionError):
        sys.exit("Run command: %s" % install_command)

    conn = psycopg2.connect(host=host, port=int(port), user=username, password=password)
    conn.set_isolation_level(0)  # https://wiki.postgresql.org/wiki/Psycopg2_Tutorial
    cur = conn.cursor()
    for dbname in DBS:
        if SCRAPYDWEB_TESTMODE:
            # database "scrapydweb_apscheduler" is being accessed by other users
            # DETAIL:  There is 1 other session using the database.
            # To restart postgres server on Windonws -> win+R: services.msc
            drop_database(cur, dbname)

        # https://www.postgresql.org/docs/9.0/sql-createdatabase.html
        # https://stackoverflow.com/questions/9961795/
        # utf8-postgresql-create-database-like-mysql-including-character-set-encoding-a

        # psycopg2.ProgrammingError: invalid locale name: "en_US.UTF-8"
        # https://stackoverflow.com/questions/40673339/
        # creating-utf-8-database-in-postgresql-on-windows10

        # cur.execute("CREATE DATABASE %s ENCODING 'UTF8' LC_COLLATE 'en-US' LC_CTYPE 'en-US'" % dbname)
        # psycopg2.DataError: new collation (en-US) is incompatible with the collation of the template database
        # (Chinese (Simplified)_People's Republic of China.936)
        # HINT:  Use the same collation as in the template database, or use template0 as template.
        try:
            cur.execute("CREATE DATABASE %s ENCODING 'UTF8' LC_COLLATE 'en_US.UTF-8' LC_CTYPE 'en_US.UTF-8'" % dbname)
        except:
            try:
                cur.execute("CREATE DATABASE %s" % dbname)
            except Exception as err:
                # psycopg2.ProgrammingError: database "scrapydweb_apscheduler" already exists
                if 'exists' in str(err):
                    pass
                else:
                    raise
    cur.close()
    conn.close()
