# coding=utf-8
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


def app_fixture_test(app):
    """verify that we can generate a flaks app fixture."""
    assert app and isinstance(app, Flask)


def db_fixture_test(db):
    """verify that we can create the db fixture."""
    assert db and isinstance(db, SQLAlchemy)


def testapp_fixture_test(testapp):
    """verify that we have a working testapp fixture."""
    resp = testapp.get('/').maybe_follow()
    assert resp.status_code == 200
