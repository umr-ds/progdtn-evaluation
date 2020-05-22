### ENV string routing "Routing algorithm"

import os
import time
import logging

import framework

from core.emulator.coreemu import CoreEmu, Session
from core.emulator.enumerations import EventTypes
from core.services import ServiceManager

from log_files import *


if __name__ in ["__main__", "__builtin__"]:
    seed: int = {{seed}}
    print(f"Seed: {seed}")

    # write seed to file so that core services can use it
    with open("/tmp/seed", "wb") as f:
        f.write(seed.to_bytes(4, byteorder="little", signed=False))

    with open("/tmp/routing", "w") as f:
        f.write({{routing}})

    framework.start()
    logging.basicConfig(level=logging.DEBUG)

    # Prepare experiment
    coreemu = CoreEmu()
    session: Session = coreemu.create_session(_id={{simInstanceId}})
    session.set_state(EventTypes.CONFIGURATION_STATE)

    ServiceManager.add_services("/root/.core/myservices")

    session.open_xml(
        file_name="/dtn_routing/scenarios/wanderwege/wanderwege.xml", start=True
    )
    time.sleep(10)

    # Run the experiment
    time.sleep(300)

    # When the experiment is finished, we set the session to
    # DATACOLLECT_STATE and collect the logs.
    # After that, we shutdown the session, cleanup the generated payloads
    # and manually make sure, that all remaining files of the experiments
    # are gone.
    # Finally, we wait another 10 seconds to make sure everyhing is clean.
    session.set_state(EventTypes.DATACOLLECT_STATE)
    time.sleep(2)
    collect_logs(session.session_dir)
    coreemu.shutdown()
    os.system("core-cleanup")
    time.sleep(10)

    framework.stop()
