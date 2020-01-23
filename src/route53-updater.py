#!/usr/local/bin/python

import boto3
import time
import os
from kubernetes import client, config

hosted_zone_id = os.getenv('HOSTED_ZONE_ID', 'none')
base_url = os.getenv('DNS_RECORD', 'none')
ttl = int(os.getenv('TTL', 60))
run_interval = int(os.getenv('RUN_INTERVAL', 60))
create_health_checks = os.getenv('CREATE_HEALTH_CHECKS', 'False')


def remove_hc(ip, healthcheck):
    response = route53_client.delete_health_check(HealthCheckId=healthcheck)

    print("Removing healthcheck: ip=", ip, ", id=", healthcheck,
          ", response=", str(response), sep='')


def get_cluster_ips():
    # it works only if this script is run by K8s as a POD
    config.load_incluster_config()
    ips = list()
    v1 = client.CoreV1Api()

    nodes = v1.list_node(watch=False)
    for node in nodes.items:
        for addr in node.status.addresses:
            if addr.type == 'ExternalIP':
                ips.append(addr.address)

    return ips


def remove_rs(ip, healthcheck=None):
    change_batch = {
        'Changes': [
            {
                'Action': 'DELETE',
                'ResourceRecordSet': {
                    'Name': base_url,
                    'Type': 'A',
                    'TTL': ttl,
                    'SetIdentifier': ip,
                    'Weight': 1,
                    'ResourceRecords': [
                        {
                            'Value': ip
                        },
                    ],
                }
            },
        ]
        }
    if healthcheck:
        change_batch['Changes'][0]['HealthCheckId'] = healthcheck

    response = route53_client.change_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        ChangeBatch=change_batch)

    print("Removing recordSet: ip=" + ip + ", response=" + str(response))


def create_hc(ip):

    response = route53_client.create_health_check(
        CallerReference=ip + "." + str(time.time()),
        HealthCheckConfig={
            'IPAddress': ip,
            'Port': 80,
            'Type': 'HTTP',
            'RequestInterval': 30,
            'FailureThreshold': 2,
            'MeasureLatency': False,
            'Inverted': False,
            'Disabled': False,
            'EnableSNI': False
        }
    )

    print("Creating healthcheck: ip=" + ip + ", response=" + str(response))

    return response


def create_rs(ip, healthcheck=None):
    change_batch = {
        'Changes': [
            {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': base_url,
                    'Type': 'A',
                    'SetIdentifier': ip,
                    'Weight': 1,
                    'TTL': ttl,
                    'ResourceRecords': [
                        {
                            'Value': ip
                        },
                    ],
                }
            },
        ]
    }
    if healthcheck:
        change_batch['Changes'][0]['HealthCheckId'] = healthcheck

    response = route53_client.change_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        ChangeBatch=change_batch)

    print("Creating recordSet: ip=", ip, ", healthcheck=", healthcheck,
          ", response=", str(response))


if hosted_zone_id != 'none' and base_url != 'none':
    while True:
        print("Running route53-updater")
        ips = get_cluster_ips()

        route53_client = boto3.client('route53')
        r = route53_client.list_resource_record_sets(
            HostedZoneId=hosted_zone_id)

        for i in r['ResourceRecordSets']:
            if i['Type'] == 'A':
                print("Checking existing recordSet: " + str(i))
                if i['Name'] == base_url + ".":
                    if i['SetIdentifier'] not in ips:
                        if create_health_checks == 'True':
                            remove_rs(i['SetIdentifier'], i['HealthCheckId'])
                            remove_hc(i['SetIdentifier'], i['HealthCheckId'])
                        else:
                            remove_rs(i['SetIdentifier'])
                    else:
                        ips.remove(i['SetIdentifier'])

        for ip in ips:
            if create_health_checks == 'True':
                hc = create_hc(ip)
                create_rs(ip, hc['HealthCheck']['Id'])
            else:
                create_rs(ip)

        time.sleep(run_interval)
else:
    print("ERROR: Hosted zone ID and DNS record name variables not configured")
