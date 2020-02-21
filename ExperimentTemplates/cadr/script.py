### ENV int payload_size "Size of payload to be sent in bytes"
### ENV string routing "Routing algorithm"

import os
import time
import logging

import framework

from core.emulator.coreemu import CoreEmu, Session
from core.emulator.enumerations import EventTypes
from core.nodes.base import CoreNode
from core.services import ServiceManager

from dtn7 import DTN7
from log_files import *
from helpers import *


def create_session(topo_path, _id):
    coreemu = CoreEmu()
    core_session: Session = coreemu.create_session(_id=_id)
    core_session.set_state(EventTypes.CONFIGURATION_STATE)

    ServiceManager.add_services('/root/.core/myservices')

    core_session.open_xml(topo_path)

    print(core_session.nodes)

    for node in core_session.nodes.values():
        if isinstance(node, CoreNode):
            node.startup()
            core_session.services.add_services(node, node.type, ['pidstat', 'bwm-ng', "DTN7"])

    core_session.instantiate()

    return core_session


if __name__ in ["__main__", "__builtin__"]:
    framework.start()
    logging.basicConfig(level=logging.DEBUG)

    # Prepare experiment
    path = create_payload({{payload_size}})
    session = create_session(
        "/dtn_routing/scenarios/wanderwege/wanderwege.xml", {{simInstanceId}})
    time.sleep(10)

    # Run the experiment
    software = DTN7(session)
    #software.send_file("n15", path, "n40")
    #software.wait_for_arrival("n40")
    #time.sleep(10)

    # When the experiment is finished, we set the session to
    # DATACOLLECT_STATE and collect the logs.
    # After that, we shutdown the session, cleanup the generated payloads
    # and manually make sure, that all remaining files of the experiments
    # are gone.
    # Finally, we wait another 10 seconds to make sure everyhing is clean.
    session.set_state(EventTypes.DATACOLLECT_STATE)
    time.sleep(2)
    collect_logs(session.session_dir)
    session.shutdown()
    cleanup_payloads()
    os.system("core-cleanup")
    time.sleep(10)

    framework.stop()
