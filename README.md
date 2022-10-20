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
Install Listener agent to debug message on messsage bus
```sh
python scripts/install-agent.py -s examples/ListenerAgent --start
```
Check if the Listener agent is running normally
```sh
vctl status
```
This should be shown and you are good to go
```sh
UUID AGENT                    IDENTITY                   TAG STATUS          HEALTH
f listeneragent-3.3        listeneragent-3.3_1            running [9713]  GOOD
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

Tuya cloud IoT access is needed to setup Tuya virtual devices. Follow [this guideline](https://developer.tuya.com/en/docs/iot/quick-start1?id=K95ztz9u9t89n)
Recommendation : Select the region when you build the cloud project's region to be *India*. Choosing Chinese region will required you to do the account verification. If you are not a Chinese citizen, select other region will be a lot easire.
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

After finished setting up Tuya Dummy device following guideline above, you should get your device ID and your account access key. From your main console page, it should be in *Overview* and *Devices* tabs.

After that go to TuyaPoller agent's configuration file which locate at [~/TuyaPoller/config](https://github.com/anoot-k/alto-test/blob/main/TuyaPoller/config)

Edit the file
```sh
vim ~/TuyaPoller/cinfig
```
```
{
  # VOLTTRON config files are JSON with support for python style comments.
  "endpoint": "https://openapi.tuyain.com", # Your region endpoint. Other region can be found here :  
  "deviceId": "<YOUR_DEVICE_ID>",
  "accessId": "<YOUR_ACCESS_ID>",
  "accessKey": "<YOUR ACCESS_KEY>",
  "topic": "devices/altotest/test/tuya",  # topics for pub
  "interval": 20  # integer : polling interval
}
```
Exit vim
Install the agent
```sh
python scripts/install-agent.py -s TuyaPoller -c TuyaPoller/config
```
Check if the agent is installed correctly
```sh
vctl status
```
Something like this should show up
```sh
UUID AGENT                    IDENTITY                   TAG STATUS          HEALTH
4 tuyapolleragent-0.1      tuyapolleragent-0.1_1          0               
```
Run the agent and check status again
```sh
vctl start tuyapolleragent-0.1
vctl status
```
This should be shown
```sh
UUID AGENT                    IDENTITY                   TAG STATUS          HEALTH
4 tuyapolleragent-0.1      tuyapolleragent-0.1_1          running [1292]  GOOD
```

## Setup configuration file for CloudCrateAgent agent

The config file is located at [~/CloudCrateAgent/config]
```sh
{
  # VOLTTRON config files are JSON with support for python style comments.
  "host": "https://magenta-ben-quadinaros.aks1.eastus2.azure.cratedb.net:4200/",  # Hostname for crateDB instances
  "user": "writer", # user for accessing CloudCrate
  "password": "writer", # password for accessing CloudCrate
  "topic": "devices/altotest/test/"  # Sub topic
}
```
Install and run the agaent
```sh
python scripts/install-agent.py -s CloudCrateAgent -c CloudCrateAgent/config
vctl start cloudcrateagentagent-0.1
```
this should be shown
```sh
UUID AGENT                    IDENTITY                   TAG STATUS          HEALTH
0 cloudcrateagentagent-0.1 cloudcrateagentagent-0.1_1     running [1187]  GOOD
```


## Setup configuration file for modbus platform driver
For modbus platform driver configuration. 2 config files are needed to be configurated : [~/config/modbus.config]()

## Deploy





