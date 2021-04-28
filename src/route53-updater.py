#!/usr/local/bin/python

import boto3
import os
import yaml
import json
from kubernetes import client, config

hosted_zone_id = os.getenv('HOSTED_ZONE_ID', 'none')
base_url = os.getenv('DNS_RECORD', 'none')
ttl = int(os.getenv('TTL', 60))
tag = os.getenv('TAG', 'none')
config_file = os.getenv('CONFIG_PATH', '')
run_interval = int(os.getenv('RUN_INTERVAL', 60))
create_health_checks = os.getenv('CREATE_HEALTH_CHECKS', 'False')


def remove_hc(healthcheck):
    response = route53_client.delete_health_check(HealthCheckId=healthcheck)

    print("Removing healthcheck:", healthcheck,
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


def get_cluster_ips_test():
    ips = list()
    ips.append('34.90.163.32')

    return ips


def cleanup_recordsets(zone, cleanup_records):
    if len(cleanup_ips):
        for record in cleanup_records:
            change_batch = {
                'Changes': [
                    {
                        'Action': 'DELETE',
                        'ResourceRecordSet': {
                            'Name': record["Name"],
                            'Type': record["Type"],
                            'TTL': record["TTL"],
                            'SetIdentifier': record["SetIdentifier"],
                            'Weight': 1,
                            'ResourceRecords': record["ResourceRecords"],
                        }
                    },
                ]
            }
            if "HealthCheckId" in record:
                remove_hc(record["HealthCheckId"])
                change_batch['Changes'][0]['ResourceRecordSet']['HealthCheckId'] = record["HealthCheckId"]

            resp = route53_client.change_resource_record_sets(
                HostedZoneId=zone,
                ChangeBatch=change_batch)
            print("ZoneId:", zone, "# removed " +
                  record["Name"] + " -> " + json.dumps(record["ResourceRecords"]), "#", str(resp))
    else:
        print("ZoneId:", zone, "# nothing to cleanup")


def create_hc(ip):

    response = route53_client.create_health_check(
        CallerReference=ip,
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

    print("created healthcheck: ip=" + ip + ", response=" + str(response))

    return response


def create_cname(name, alias, zone_id):
    change_batch = {
        'Changes': [
            {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': name,
                    'Type': 'CNAME',
                    'SetIdentifier': tag + "-" + name,
                    'Weight': 1,
                    'TTL': ttl,
                    'ResourceRecords': [
                        {
                            'Value': alias
                        },
                    ],
                }
            },
        ]
    }

    response = route53_client.change_resource_record_sets(
        HostedZoneId=zone_id,
        ChangeBatch=change_batch)

    print("ZoneId:", zone_id, "# created CNAME " +
          name + " -> " + alias, "#", str(response))


def create_record_set(name, ip, zone_id):
    change_batch = {
        'Changes': [
            {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': name,
                    'Type': 'A',
                    'SetIdentifier': tag + "-" + name + "." + ip,
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
    if create_health_checks == 'True':
        change_batch['Changes'][0]['ResourceRecordSet']['HealthCheckId'] = healthchecks[ip]

    response = route53_client.change_resource_record_sets(
        HostedZoneId=zone_id,
        ChangeBatch=change_batch)

    print("ZoneId:", zone_id, "# created A " +
          name + " -> " + ip, "#", str(response))


print("running route53-updater")
if config_file == '':
    exit("CONFIG_PATH not defined")
ips = get_cluster_ips()
healthchecks = {}
with open(config_file) as f:
    data = yaml.load(f, Loader=yaml.FullLoader)
    print("config:", data)

    route53_client = boto3.client('route53')

    for zone in data:
        cleanup_ips = []
        zone_ips = ips.copy()
        response = route53_client.list_resource_record_sets(
            HostedZoneId=zone)

        managed_records = []
        for record in response["ResourceRecordSets"]:
            if "SetIdentifier" in record and tag in record["SetIdentifier"]:
                managed_records.append(record)

        for record in managed_records:
            if record["Type"] == "A":
                record_name = record["Name"][:-1]
                record_ip = record["ResourceRecords"][0]["Value"]

                if record_ip in zone_ips and record_name == data[zone]["A"]:
                    zone_ips.remove(record_ip)
                else:
                    cleanup_ips.append(record)

            if record["Type"] == "CNAME":
                record_value = record["ResourceRecords"][0]["Value"]
                record_name = record["Name"].replace("\\052", "*")[:-1]

                if record_name in data[zone]["C"]:
                    if record_value == data[zone]["A"]:
                        data[zone]["C"].remove(record_name)
                else:
                    cleanup_ips.append(record)

        if len(zone_ips):
            for ip in zone_ips:
                if create_health_checks == 'True':
                    hc = create_hc(ip)
                    healthchecks[ip] = hc['HealthCheck']['Id']
                create_record_set(data[zone]["A"], ip, zone)
        else:
            print("ZoneId:", zone, "# nothing to create")

        for alias in data[zone]["C"]:
            create_cname(alias, data[zone]["A"], zone)

        cleanup_recordsets(zone, cleanup_ips)

# for i in r['ResourceRecordSets']:
#     if i['Type'] == 'A':
#         print("Checking existing recordSet: " + str(i))
#         if i['Name'] == base_url + ".":
#             if i['SetIdentifier'] not in ips:
#                 if create_health_checks == 'True':
#                     remove_rs(i['SetIdentifier'], i['HealthCheckId'])
#                     remove_hc(i['SetIdentifier'], i['HealthCheckId'])
#                 else:
#                     remove_rs(i['SetIdentifier'])
#             else:
#                 ips.remove(i['SetIdentifier'])

# for ip in ips:
#     if create_health_checks == 'True':
#         hc = create_hc(ip)
#         create_rs(ip, hc['HealthCheck']['Id'])
#     else:
#         create_rs(ip)

# time.sleep(run_interval)
