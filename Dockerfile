FROM python

RUN pip install -r requirements.txt

ADD src/route53-updater.py /app/
