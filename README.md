This repo is intended to sbmit assignment by altotech.

The main branch of this repo stored the same set of code with this branch, only README is difference.


![Untitled Diagram-Page-2 drawio (4)](https://user-images.githubusercontent.com/78077500/196720082-48fef0c7-aaf2-4050-bd90-b5fd8ac35b4d.png)


## System Architecture
As shown in above picture, this system has 2 sides, data polling and data transfer.
Data polling was implemented in 2 ways : using platform driver to poll from a dummy modbus devices and using TuyaPoller agent to poll from Tuya API.
Data from poller will be published to VOLTTRON's message bus and trigger a callback function implemented in CloudCrateAgent.
The callback function will send data into transaction table which is logging topic of data subscription, timestamp and data which provided by each poller.


## Design Decision

1. Modbus scraper is not developed since Platform Driver agent has already been built inside VOLTTRON's [modbus platform driver](https://volttron.readthedocs.io/en/stable/agent-framework/driver-framework/modbus/modbus-driver.html).
2. However, CloudCrateAgnet was developed even if [Crate Historian](https://volttron.readthedocs.io/en/main/agent-framework/historian-agents/crate/crate-historian.html#crate-historian) has been already implemented inside Historian Framework. The reason behind this was becuase the          built-in one seems to not support cloud authentication function need to transfer data up to cloud CrateDB.
3. Same decision was made with TuyaCaller agent. Since Tuya cloud API needs authentication which [External Data Publisher Agent](https://volttron.readthedocs.io/en/main/agent-framework/core-service-agents/external-data/external-data.html) cannot provided. [Tuya connector](https://github.com/tuya/tuya-connector-python) was used in the development to help solve authentication issue.
4. [diagslave](https://www.modbusdriver.com/diagslave.html) was used as a modbus slave blueprint to help with initilize process of modbus dummy device. After initialization, the [python script](https://github.com/anoot-k/alto-test/blob/main/alto-test/dummy/meter/modbus_device.py) for writing register to said device was run to populate dummy data with my CPU usage data.
5. Development was setup on WSL2 with Ubuntu 20.04 image. See how to setup the same environment [Here](https://ubuntu.com/tutorials/install-ubuntu-on-wsl2-on-windows-10#1-overview)


## Get started
Clone this repositry.
```sh
cd ~
git clone 
cd alto-test
```
Now you will be in `$VOLTTRON_HOME` directory
Setup all of the volttron dependencies using builtin bootstrap. For this portion, you can follow volttron get start document also.
```sh
python bootstrap.py
```
activate voltron virtual environment.
```sh
source ~/alto-test/volttron/env/bin/activate
```

## Setup modbus dummy device

### Setup diagslave
Download
```sh
wget https://www.modbusdriver.com/downloads/diagslave.tgz
```
unpack tarball and cd into working directory
```sh
tar xzf diagslave-3.2.tgz
cd diagslave
```
run. Select the appropriate CPU architecture to run. In this case x64 CPU was used.
```sh
sudo ./x86_64-linux-gnu/diagslave -m tcp -a 1
```
`-m tcp` was specified to run modbus tcp slave
`-a 1` was specified to run slave on unit id 1 (as this will be set everywhere)

### Setup modbus writer
Setup dependencies needed
```sh
cd <volttron_home_directory>
python bootstrap.py --drivers
```
Run python script
```sh
python alto-test/alto-test/dummy/meter/modbus_device.py
```
This script default setting was set to bind the ip address as localhost, default port on 502 and default slave on salve id 1.
If any configuration needs to be changed, edit under __main__ entry point in the script then rerun it.

```py
if __name__ == '__main__':
    ModDummySlave(host=<host>, port=<port>, slaveId=<slaveId>).run()
```

## Setup Tuya dummy device

## CrateDB table structure
Crate on cloud was setup following this [guideline](https://crate.io/blog/visualizing-time-series-data-with-grafana-and-cratedb)

To create the same schema. After configuration above is finished, go to the console and run this script to create table.
```
create table obj_cpu_transaction(
  ts timestamp with time zone default NOW(),
  topic text,
  obj object);
```
## Setup configuration file for TuyaPoller agent

## Setup configuration file for CloudCrateAgent agent

## Deploy





