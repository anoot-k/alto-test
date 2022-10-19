"""
Agent documentation goes here.
"""

__docformat__ = 'reStructuredText'

import logging
import sys
from volttron.platform.agent import utils
from volttron.platform.vip.agent import Agent, Core, RPC
from tuya_connector import TuyaOpenAPI
import json
from crontab import CronTab as cron

_log = logging.getLogger(__name__)
utils.setup_logging()
__version__ = "0.1"


def tuyapoller(config_path, **kwargs):
    """
    Parses the Agent configuration and returns an instance of
    the agent created using that configuration.

    :param config_path: Path to a configuration file.
    :type config_path: str
    :returns: Tuyapoller
    :rtype: Tuyapoller
    """
    try:
        config = utils.load_config(config_path)
    except Exception:
        config = {}

    if not config:
        _log.info("Using Agent defaults for starting configuration.")

    endpoint = config.get('endpoint', None)
    accessId = config.get('accessId', None)
    accessKey = config.get('accessKey', None)
    deviceId = config.get('deviceId', None)
    topic = config.get('topic', None)
    interval = config.get('interval', None)

    return Tuyapoller(endpoint, accessId, accessKey, deviceId, topic, interval, **kwargs)


class Tuyapoller(Agent):
    """
    Document agent constructor here.
    """

    def __init__(self, endpoint, accessId, accessKey, deviceId, topic, interval, **kwargs):
        super(Tuyapoller, self).__init__(**kwargs)
        _log.debug("vip_identity: " + self.core.identity)

        self.endpoint = endpoint
        self.accessId = accessId
        self.accessKey = accessKey
        self.deviceIdList = deviceId
        self.pub_topic = topic
        self.pub_interval = interval

        self.openapi = TuyaOpenAPI(self.endpoint, self.accessId, self.accessKey)

        self.default_config = {"endpoint": self.endpoint,
                               "accessId": self.accessId,
                               "accessKey": self.accessKey,
                               "deviceId": self.deviceIdList,
                               "topic": self.pub_topic,
                               "interval": self.pub_interval}

        # Set a default configuration to ensure that self.configure is called immediately to setup
        # the agent.
        self.vip.config.set_default("config", self.default_config)
        # Hook self.configure up to changes to the configuration file "config".
        self.vip.config.subscribe(self.configure, actions=["NEW", "UPDATE"], pattern="config")

    def configure(self, config_name, action, contents):
        """
        Called after the Agent has connected to the message bus. If a configuration exists at startup
        this will be called before onstart.

        Is called every time the configuration in the store changes.
        """
        config = self.default_config.copy()
        config.update(contents)

        _log.debug("Configuring Agent")

        try:
            endpoint = config["endpoint"]
            accessId = config["accessId"]
            accessKey = config["accessKey"]
            deviceId = config["deviceId"]
            topic = config["topic"]
            interval = config["interval"]
        except ValueError as e:
            _log.error("ERROR PROCESSING CONFIGURATION: {}".format(e))
            return

        self.endpoint = endpoint
        self.accessId = accessId
        self.accessKey = accessKey
        self.deviceIdList = deviceId
        self.pub_topic = topic
        self.pub_interval = interval

        self._create_subscriptions(self.pub_topic)

    def _create_subscriptions(self, topic):
        """
        Unsubscribe from all pub/sub topics and create a subscription to a topic in the configuration which triggers
        the _handle_publish callback
        """
        self.vip.pubsub.unsubscribe("pubsub", None, None)

        self.vip.pubsub.subscribe(peer='pubsub',
                                  prefix=topic,
                                  callback=self._handle_publish)

    def _handle_publish(self, peer, sender, bus, topic, headers, message):
        """
        Callback triggered by the subscription setup using the topic from the agent's config file
        """
        pass

    @Core.receiver("onstart")
    def onstart(self, sender, **kwargs):
        """
        This is method is called once the Agent has successfully connected to the platform.
        This is a good place to setup subscriptions if they are not dynamic or
        do any other startup activities that require a connection to the message bus.
        Called after any configurations methods that are called at startup.

        Usually not needed if using the configuration store.
        """
        # Example publish to pubsub
        self.vip.pubsub.publish('pubsub', "some/random/topic", message="HI!")

        # Example RPC call
        # self.vip.rpc.call("some_agent", "some_method", arg1, arg2)
        pass

    @Core.receiver("onstop")
    def onstop(self, sender, **kwargs):
        """
        This method is called when the Agent is about to shutdown, but before it disconnects from
        the message bus.
        """
        self.vip.pubsub.publish('pubsub', "some/random/topic", message="BYE!")
        pass

    @Core.periodic(1)
    def cron_job(self):
        self.openapi.connect()
        responses = self.openapi.get("/v1.0/iot-03/devices/{}/status".format(self.deviceIdList))['result']
        self.vip.pubsub.publish('pubsub', self.pub_topic, message=json.dumps(responses))

    @RPC.export
    def rpc_method(self, arg1, arg2, kwarg1=None, kwarg2=None):
        """
        RPC method

        May be called from another agent via self.core.rpc.call
        """
        return self.setting1 + arg1 - arg2


def main():
    """Main method called to start the agent."""
    utils.vip_main(tuyapoller, 
                   version=__version__)


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
