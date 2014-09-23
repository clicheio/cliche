from cliche.celery import app as celery_app


def get_celery_always_eager_app():
    celery_app.conf['CELERY_ALWAYS_EAGER'] = True
    return celery_app
