import sys

if sys.version.startswith("3."):
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass

