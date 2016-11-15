# freeswitch_pri_did_indexer 

# Table of Contents

- [Description](#description)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Usage](#usage)

### description
An application in python to gather information like,
PRI Connectivity status PRI Signalling status Outgoing Caller ID.

### dependencies
python == 2.7
#### required python packages
  - argparse == 1.2.1
  - tornado == 4.3
  - pymongo == 3.2.2
  - paramiko == 1.16.0
  - redis == 2.10.5


#### other dependencies
  - a fully functional redis server (local or remote)
  - a fully functional mongodb server (local or remote)
  - a freeswitch server with dedicated destination number.

## deployment
after successfully meeting all software dependencies on the target server / machine,
  - create an xml entry like below on the dial plan of the destination freeswitch server with target server ip address mentioned in data url

```xml
<extension name="PRI_TEST">
	<condition field="destination_number" expression="39972019">
             <action application="ring_ready"/>
             <action application="set" data="ringback=/var/lib/viva/sounds/ringing.wav"/>
             <action application="sleep" data="2000"/>
             <action application="curl" data="http://<target server address>:8888/publish_did_number/${caller_id_number}"/>
             <action application="hangup" data="NORMAL_CLEARING"/>
	</condition>
</extension>

```

  - place all the repository files in a specific location
  - specify the mongo and redis server parameters in the `<project_directory>/components/conf/settings.py` and also set MONGODB_AUTH parameter and REDIS_AUTH parameter to true if using password authentication.

```python
MONGODB_AUTH = False
MONGODB_HOST = "localhost"
MONGODB_PORT = 27019
MONGODB_NAME = "pritesterdb"
MONGODB_COLLECTION = "pri_status_collection"
MONGODB_USER = ""
MONGODB_PASSWORD = ""
REDIS_AUTH = False
REDIS_HOST = "localhost"
REDIS_PORT = 6379
SUBSCRIBE_CHANNEL = "outgoing"
REDIS_PASSWORD = ""
```

  - set destination number of the freeswitch server which is used for consuming calls and provide did details in the /components/lib/tester.py PRITester class or leave it as it is for default number

```python
self.destination_number = "02039972019"
```

  - set the application log directory in the `<project_directory>/components/conf/settings.py` of the main project directory.

```python
LOG_DIR = ""
```
  - set the `<project_directory>/watcher/pri_tester_watcher.sh` in the specific server cron file like below:
```sh
* * * * * <user> /bin/bash <project_directory>/watcher/pri_tester_watcher.sh
```


## usage
The freeswitch-pri-tester requires that you have pri information consumer and did information subscriber and few other servers mentioned in the watcher file running before running tests on any server for functional PRIs.
 Assuming that the watcher is taking care of all the specific servers.

  - go to main directory of the project and run below command in shell to begin testing on the <target server>

```sh
python2.7 main.py -s <target server>
```

