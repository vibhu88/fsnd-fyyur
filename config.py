import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):

    DEBUG = True

    # Connect to the database
    # Just change the names of database and credentials and all to connect to your local system
    DATABASE_NAME = "fsnd"
    username = 'postgres'
    password = 'postgres'
    url = 'localhost:5432'
    SQLALCHEMY_DATABASE_URI = "postgres://{}:{}@{}/{}".format(username, password, url, DATABASE_NAME)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.urandom(32)