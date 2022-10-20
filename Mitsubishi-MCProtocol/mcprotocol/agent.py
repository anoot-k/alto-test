"""
Agent documentation goes here.
"""

__docformat__ = 'reStructuredText'

import logging
import sys
from volttron.platform.agent import utils
from volttron.platform.vip.agent import Agent, Core, RPC
import pymcprotocol
import json

_log = logging.getLogger(__name__)
utils.setup_logging()
__version__ = "0.1"


def mcprotocol(config_path, **kwargs):
    """
    Parses the Agent configuration and returns an instance of
    the agent created using that configuration.

    :param config_path: Path to a configuration file.
    :type config_path: str
    :returns: Mcprotocol
    :rtype: Mcprotocol
    """
    try:
        config = utils.load_config(config_path)
    except Exception:
        config = {}

    if not config:
        _log.info("Using Agent defaults for starting configuration.")

    setting1 = int(config.get('setting1', 1))
    setting2 = config.get('setting2', "some/random/topic")

    return Mcprotocol(setting1, setting2, **kwargs)


class Mcprotocol(Agent):
    """
    Document agent constructor here.
    """

    def __init__(self, type, registers, host='192.168.0.1', port=1025, commtype='binary',topic='devices/altotest/test/plc/mitsubishi' **kwargs):
        super(Mcprotocol, self).__init__(**kwargs)
        _log.debug("vip_identity: " + self.core.identity)

        self.type_list = ["Q", "L", "iQ-L", "iQ-R"]

        self.host = host
        self.port = int(port)
        if type in self.type_list:  # Check for PLC CPU type
            self.type = type
        else:
            raise pymcprotocol.type3e.PLCTypeError
        self.commtype = commtype
        self.registers = registers
        self.topic = topic

        self.default_config = {"host": self.host,
                               "port": self.port,
                               "type": self.type,
                               "commtype": self.commtype,
                               "registers": self.registers,
                               "topic": topic}

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
            host = config["host"]
            port = int(config["port"])
            type = config["type"]
            commtype = config["commtype"]
            registers = config["registers"]
            topic = topic["topic"]
        except ValueError as e:
            _log.error("ERROR PROCESSING CONFIGURATION: {}".format(e))
            return

        self.host = host
        self.port = port
        if type in self.type_list:
            self.type = type
        else:
            raise pymcprotocol.type3e.PLCTypeError
        self.commtype = commtype
        self.registers = registers
        self.topic = topic

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
        pass

    @Core.periodic(10)
    def cron_job(self):
        pymc3e = pymcprotocol.Type3E(plctype=self.type)  # Initialize connection to PLC
        pymc3e.setaccessopt(commtype=self.commtype)
        try :  # Put everything inside try block to avoid unexpected error
            pymc3e.connect(self.host, self.port)
            dict = {}
            for device, length in self.registers.items():
                if str(device)[0] == 'D':  # For PLC, D will store 16 bit WORD data and X will store bit data
                    dict[device] =  pymc3e.batchread_wordunits(headdevice=device, readsize=length)
                elif str(device)[0] == 'X':
                    dict[device] =  pymc3e.batchread_bitunits(headdevice=device, readsize=length)
                else:
                    _log.error(f'Wrong device type input')
                    pass
            self.vip.pubsub.publish('pubsub', self.topic, message=json.dumps(dict))
            pymc3e.close()
        except Exception as ex:
            _log.error(f'Operation failed with exception : {ex}')  # There are many exceptions that might be able to occur here.
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
    utils.vip_main(mcprotocol, 
                   version=__version__)


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
