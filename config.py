import os


class Config(object):
    """
    Basic app configuration object that will first attempt
    to load variables from the environment and fall back to
    pre-defined defaults. For security, do not put actual production
    values here, but define them outside of the application as
    environment variables, as this file is considered part of application
    source and may be posted in a public manner
    """

    ORACLE_SERVICE_NAME = os.environ.get("ORACLE_SERVICE_NAME", "ORCL")
    ORACLE_USER_NAME = os.environ.get("ORACLE_USER_NAME", "foo")
    ORACLE_PASSWORD = os.environ.get("ORACLE_PASSWORD", "bar")
    ORACLE_DB_HOST = os.environ.get("ORACLE_DB_HOST", "localhost")
    MYSQL_USER_NAME = os.environ.get("MYSQL_USER_NAME", 'foo')
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", 'bar')
    MYSQL_DB_HOST = os.environ.get("MYSQL_DB_HOST", 'localhost')
    MYSQL_DB_PORT = os.environ.get("MYSQL_DB_PORT", 3306)
    MYSQL_DB_NAME = os.environ.get("MYSQL_DB_NAME", 'mongoose')
    SECRET_KEY = os.environ.get('APP_SECRET', 'S00p3rs3cr3t')


class TestingConfig(Config):
    """
    Override Config values here if a testing environment
    requires different configuration than a development or
    production environment
    """
    pass


class DevelopmentConfig(Config):
    """
    Override Config values here if a development environment
    requires different configuration than a production or
    testing environment
    """
    pass


class ProductionConfig(Config):
    """
    Override Config values here if a production environment
    requires different configuration than a development or
    testing environment
    """
    pass
