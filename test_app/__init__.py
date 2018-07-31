import sys

if sys.version.startswith("3."):
    import pymysql
    pymysql.install_as_MySQLdb()
