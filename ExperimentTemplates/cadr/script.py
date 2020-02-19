### ENV int node_num "How many nodes should be emulated"
### ENV int size "Size of payload to be sent in bytes"
### ENV string software "Which DTN software should be used"

import csv
import datetime
import json
import os
import random
import shutil
import struct
import time

import framework

from core.emulator.coreemu import CoreEmu
from core.emulator.enumerations import EventTypes
from core.emulator.emudata import IpPrefixes
from core.emulator.emudata import NodeOptions
from core.nodes.base import CoreNode
from core.services import ServiceManager

from dtn7 import DTN7
from log_files import *
from helpers import *


def create_session(topo_path, _id, dtn_software):
    coreemu = CoreEmu()
    session = coreemu.create_session(_id=_id)
    session.set_state(EventTypes.CONFIGURATION_STATE)

    ServiceManager.add_services('/root/.core/myservices')

    session.open_xml(topo_path)

    for obj in session.objects.values():
        if type(obj) is CoreNode:
            session.services.add_services(obj, obj.type, ['pidstat', 'bwm-ng', dtn_software])

    session.instantiate()

    return session


if __name__ in ["__main__", "__builtin__"]:
    framework.start()

    # Prepare experiment
    path = create_payload({{size}})
    session = create_session(
        "/topologies/chain/{}.xml".format({{node_num}}), {{simInstanceId}}, "{{software}}")
    time.sleep(10)

    # Run the experiment
    software = {{software}}(session)
    software.send_file("n1", path, "n{{node_num}}")
    software.wait_for_arrival("n{{node_num}}")
    time.sleep(10)

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
