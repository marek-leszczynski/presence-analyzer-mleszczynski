# -*- coding: utf-8 -*-
"""
Flask app initialization.
"""
import os.path
from flask import Flask
from flask.ext.mako import MakoTemplates


app = Flask(__name__)  # pylint: disable-msg=C0103
mako = MakoTemplates(app)
