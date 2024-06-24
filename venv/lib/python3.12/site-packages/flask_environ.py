# -*- coding: utf-8 -*-
"""
    flask-environ
    ~~~~~~~~~~~~~

    A tiny wrapper around `os.environ` that provides a concise way of importing
    configuration from the environment.

    A quick example:

    ```

    from flask import Flask
    from flask_environ import get, collect, word_for_true

    app = Flask(__name__)

    app.config.update(collect(
        get('DEBUG', default=False, convert=word_for_true),
        get('HOST', default='127.0.0.1'),
        get('PORT', default=5000, convert=int),
        get('SECRET_KEY',
            'SQLALCHEMY_DATABASE_URI',
            'TWITTER_CONSUMER_KEY',
            'TWITTER_CONSUMER_SECRET',
        ),
    ))

    ```
"""

from os import environ as oenv


def get(*env_keys, **settings):
    """Grab strings from the operating system environment

    :param settings: one of:
        * default
        * convert
        * config_key

    :returns: a dictionary of the config you asked for.
    """

    config = {}
    convert = settings.get('convert', lambda thing: thing)
    config_key = settings.get('config_key')
    if config_key:
        assert len(env_keys) == 1, 'mapping to a new key only makes sense for'\
            ' a single environment variable. or my imagination failed, sorry.'

    if len(set(env_keys)) != len(env_keys):
        raise SyntaxError('config key repeated')

    for env_key in env_keys:
        try:
            env_string = oenv[env_key]
            value = convert(env_string)
        except KeyError as env_keyerror:
            try:
                value = settings['default']
            except KeyError:
                raise env_keyerror

        key = config_key or env_key
        config.update({key: value})

    return config


def collect(*dicts):
    merged = {}
    for d in dicts:
        if any(k in merged for k in d):
            raise SyntaxError('config key repeated')
        merged.update(d)
    return merged


word_for_true = lambda word: word.lower() in ['true', 'yes', 'on' '1']
