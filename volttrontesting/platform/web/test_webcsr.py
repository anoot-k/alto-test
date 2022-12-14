import pytest

from volttrontesting.fixtures.volttron_platform_fixtures import volttron_instance_web
from volttrontesting.skip_if_handlers import skip_zmq


@pytest.mark.skip("proxy issues.")
def test_can_change_auto_allow_csr(volttron_instance_web):
    """ Test the functionality of the platform wrapper's enable_auto_csr

        This allows the turning on and off of the csr auto accept through
        the platform.web service.  The platform wrapper itself handles the
        assertion that the changes were made correctly.

        note this will only work with an rmq instance.
    """
    skip_zmq(volttron_instance_web)
    instance = volttron_instance_web

    # Should be off by default
    assert not instance.is_auto_csr_enabled()
    # Enable it
    instance.enable_auto_csr()
    assert instance.is_auto_csr_enabled()
    # Disable it
    instance.disable_auto_csr()
    assert not instance.is_auto_csr_enabled()
