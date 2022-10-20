"""
Agent documentation goes here.
"""

__docformat__ = 'reStructuredText'

import logging
import sys
from volttron.platform.agent import utils
from volttron.platform.vip.agent import Agent, Core, RPC

from crate import client  # python bootstrap.py --databases
import json

_log = logging.getLogger(__name__)
utils.setup_logging()
__version__ = "0.1"


def cloudcrateagent(config_path, **kwargs):
    """
    Parses the Agent configuration and returns an instance of
    the agent created using that configuration.

    :param config_path: Path to a configuration file.
    :type config_path: str
    :returns: Cloudcrateagent
    :rtype: Cloudcrateagent
    """
    try:
        config = utils.load_config(config_path)
    except Exception:
        config = {}

    if not config:
        _log.info("Using Agent defaults for starting configuration.")

    host = config.get('host', 'localhost:4200')
    user = config.get('user', None)
    password = config.get('password', None)
    topic = config.get('topic', 'devices/')

    '''
    Add in default parameter here incase nothing is parse on config file.
    Default parameters are specified on local crate and monitor topic for all devices agent.
    '''

    return Cloudcrateagent(host, user, password, topic, **kwargs)


class Cloudcrateagent(Agent):
    """
    Document agent constructor here.
    """

    def __init__(self, host, user, password, topic, **kwargs):
        super(Cloudcrateagent, self).__init__(**kwargs)
        _log.debug("vip_identity: " + self.core.identity)

        self.host = host
        self.topic = topic
        self.user = user
        self.password = password

        self.default_config = {"host": self.host,
                               "user": self.user,
                               "password": self.password,
                               "topic": self.topic}

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
            host = config.get('host', 'localhost:4200')
            user = config.get('user', None)
            password = config.get('password', None)
            topic = config.get('topic', 'devices/all')
        except ValueError as e:
            _log.error("ERROR PROCESSING CONFIGURATION: {}".format(e))
            return

        self.host = host
        self.topic = topic
        self.user = user
        self.password = password

        self._create_subscriptions(self.topic)

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
        Suspected message attribute will be created. storing topic and message only
        """
        _log.debug(f'logger getting value of message : {message} from topic : {topic}')
        '''
        Initialize connection to crate
        '''
        try:
            connection = client.connect(self.host, username=self.user, password=self.password)
        except ConnectionAbortedError as ce:
            _log.error(f'Connection cannot be established with CloudCrateDB : {ce}')
        '''
        Initilize cursor
        '''
        cursor = connection.cursor()
        # construc query string to insert only topic and content of message. timestamp column on data base used default value for NOW()
        query_string = 'INSERT INTO obj_cpu_transaction (topic, obj) VALUES (?, ?)'
        try:
            cursor.execute(query_string, (str(topic), json.dumps(message[0])))
        except Exception as ex:
            _log.error(f'INSERT failed with exception : {ex}')

        # Dont forget to close connections
        cursor.close()
        connection.close()
        


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
        pass

    @RPC.export
    def rpc_method(self, arg1, arg2, kwarg1=None, kwarg2=None):
        """
        RPC method

        May be called from another agent via self.core.rpc.call
        """
        return self.setting1 + arg1 - arg2


def main():
    """Main method called to start the agent."""
    utils.vip_main(cloudcrateagent, 
                   version=__version__)


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
