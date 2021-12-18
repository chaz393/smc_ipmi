# My changes
This is a great script for monitoring IPMI with Telegraf, but it didn't quite fit my needs

I allowed for dmci power values, because this is what the Supermicro implementation of IPMI uses (on my boards at least)

I allowed for chassis with redundant PSUs to tag each one. This was so I could read power, temp, and fan values from each PSU

I added the ability to pass in multiple IPs of hosts. Small change but made my life a bit easier when implementing this in Telegraf


# smc_ipmi Telegraf input plugin
Python script to parse the output of [SMCIPMITool](https://www.supermicro.com/en/solutions/management-software/ipmi-utilities) into the [InfluxDB line protocol](https://docs.influxdata.com/influxdb/latest/reference/syntax/line-protocol/). Intended to be run via Telegraf's [exec](https://github.com/influxdata/telegraf/tree/master/plugins/inputs/exec) input plugin.

## Requirements
The SMCIPMITool [[download]](https://www.supermicro.com/SwDownload/SwSelect_Free.aspx?cat=IPMI) must be installed on the Telegraf host.

## Install
Clone this repo to the Telegraf host and configure Telegraf as shown below.

## Configuration

`/etc/telegraf/telegraf.conf`
```
[[inputs.exec]]
   commands["/path/to/smc_ipmi.py /path/to/SCMIPMITool '192.168.1.2' 'ipmi_user' 'ipmi_pw' 'F'"]

   data_format = "influx"
```

## Usage
```
usage: smc_ipmi.py [-h] path ip user password {C,F}

SMCIpmi input plugin

positional arguments:
  path        Path to SMCIpmi utility
  ip          IP address of Supermicro host
  user        Username
  password    Password
  {C,F}       Temperature unit to use

optional arguments:
  -h, --help  show this help message and exit
```
