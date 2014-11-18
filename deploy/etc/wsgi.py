import pathlib

from cliche.web.app import app, setup_sentry
from cliche.config import read_config


config = read_config(filename=pathlib.Path('/home/cliche/etc/prod.cfg.py'))
app.config.update(config)
setup_sentry()


if __name__ == "__main__":
    app.run()
