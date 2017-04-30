FROM python:2-onbuild
MAINTAINER avoid3d@gmail.com

EXPOSE 5000

CMD python manage.py runserver --host 0.0.0.0 --debug
