FROM python

ADD requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

ADD src/route53-updater.py /app/
