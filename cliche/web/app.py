""":mod:`cliche.web.app` --- Flask application object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from flask import Flask

from .db import setup_session
from .ontology import ontology

__all__ = 'app',


#: (:class:`flask.Flask`) The Flask application object.
app = Flask(__name__)
setup_session(app)

app.register_blueprint(ontology)
