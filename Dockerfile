FROM python

RUN pip install boto3 kubernetes

ADD src/route53-updater.py /app/
