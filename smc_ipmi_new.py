#!/usr/bin/python3
import argparse
import csv
import subprocess
import re


def get_ipmi_sensor(path, ip, user, password):
    ipmi_output = subprocess.run([path, ip, user, password, 'ipmi', 'sensor'], capture_output=True,
                                 universal_newlines=True)
    return ipmi_output.stdout


def parse_ipmi_sensor(ipmi_sensor_output: str, temp_unit: str, ip: str):
    csv_reader = csv.reader(ipmi_sensor_output.splitlines(), delimiter='|')
    points = []

    for i, row in enumerate(csv_reader):
        # skip non-data rows
        if len(row) != 6 or row[0].strip().lower() == 'status' or row[0].strip().startswith('-'):
            continue

        # status
        status = '1' if row[0].strip().lower() == 'ok' else '0'

        field = 'status=' + status

        # sensor id and name
        sensor_match = re.findall('(\(\d+\))\s(.*)', row[1])
        sensor_id = sensor_match[0][0].strip('()')
        sensor_name = sensor_match[0][1].strip()

        tag = 'sensor=' + sensor_name.replace(' ', '\ ') + ",ip=" + ip

        # reading
        reading = row[2].strip()
        # check for temp
        if re.match('\d+C/\d+F', reading):
            temps = reading.split('/')
            temp = temps[0][:-1] if temp_unit == 'C' else temps[1][:-1]
            field += ',value=' + temp
            field += ',unit="{}"'.format(temp_unit)
        elif reading.endswith('RPM') or reading.endswith('V'):
            value, unit = reading.split(' ')
            field += ',value=' + value
            field += ',unit="{}"'.format(unit)
        else:
            field += ',value=0'
            field += ',unit=""'

        points.append('smc_ipmi,{} {}'.format(tag, field))
    return points


def get_pminfo(path, ip, user, password):
    pminfo_output = subprocess.run([path, ip, user, password, 'pminfo'], capture_output=True, universal_newlines=True)
    return pminfo_output.stdout


def parse_pminfo(pm_output: str, temp_unit: str, ip: str):
    csv_reader = csv.reader(pm_output.splitlines(), delimiter='|')
    points = []
    module = ""
    for row in csv_reader:
        #skip empty rows
        if len(row) == 0 or row[0].strip().lower() == 'item' or row[0].strip().startswith('-') or \
                row[0].strip().lower().startswith('pmbus') or row[0].strip().lower().startswith('pws'):
            continue
        if "Module" in str(row):
            module = str(row).strip().split(" ")[1].split("]")[0]
            continue
        tag = 'sensor=PMBus_' + row[0].strip().replace(' ', '\ ') + ",ip=" + ip + ",module=" + module
        value = row[1].strip()
        if row[0].strip().lower() == 'status':
            status = '1' if row[1].strip().find('STATUS OK') > 0 else '0'
            field = 'value=' + status
        elif re.match('\d+C/\d+F', value):
            temps = value.split('/')
            temp = temps[0][:-1] if temp_unit == 'C' else temps[1][:-1]
            field = 'value={},unit="{}"'.format(temp, temp_unit)
        else:
            value = value.split(' ')
            field = 'value={},unit="{}"'.format(value[0], value[1])

        points.append('smc_ipmi,{} {}'.format(tag, field))

    return points

def get_dcmi(path, ip, user, password):
  dcmi_output = subprocess.run([path, ip, user, password, 'dcmi', 'powerStatus'], capture_output=True, universal_newlines=True)
  return dcmi_output.stdout

def parse_dcmi(dcmi_output: str, ip: str):
  csv_reader = csv.reader(dcmi_output.splitlines(), delimiter='|')
  points = []

  for row in csv_reader:
    # skip non-data rows
    if len(row) < 2 or row[0].strip().lower() == 'ipmi timestamp' or \
            row[0].strip().lower() == 'sampling period' or row[0].strip().lower() == 'power reading state':
        continue
    tag = 'sensor=DCMI_' + row[0].strip().replace(' ', '\ ') + ",ip=" + ip
    value = row[1].strip()[:-1]
    field = 'value={},unit="W"'.format(value)
    points.append('smc_ipmi,{} {}'.format(tag, field))
  return points


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SMCIpmi input plugin')
    parser.add_argument('path', help='Path to SMCIpmi utility')
    parser.add_argument('ip', help='IP address of Supermicro host')
    parser.add_argument('user', help='Username')
    parser.add_argument('password', help='Password')
    parser.add_argument('temp_unit', help='Temperature unit to use', choices=['C', 'F'])

    args = parser.parse_args()

    ipmi_out = get_ipmi_sensor(args.path, args.ip, args.user, args.password)
    pminfo_out = get_pminfo(args.path, args.ip, args.user, args.password)
    dcmi_out = get_dcmi(args.path, args.ip, args.user, args.password)

    ipmi_points = parse_ipmi_sensor(ipmi_out, args.temp_unit, args.ip)
    pmbus_points = parse_pminfo(pminfo_out, args.temp_unit, args.ip)
    dcmi_points = parse_dcmi(dcmi_out, args.ip)

    points = ipmi_points + dcmi_points + pmbus_points

    print(*points, sep='\n')
