### ENV string routing "Routing algorithm"

import os
import time
import logging
import pathlib

from core.emulator.coreemu import CoreEmu, Session
from core.emulator.enumerations import EventTypes
from core.services import ServiceManager

import framework
from log_files import *
from movement_generation import generate_randomised_ns2


DATA_PATH = "/research_data"
WAYPOINT_FILE = "/dtn_routing/scenarios/wanderwege/waypoints.csv"
CORE_XML = "/dtn_routing/scenarios/wanderwege/minimal.xml"
JITTER = 30.0


if __name__ in ["__main__", "__builtin__"]:
    seed: int = {{seed}}
    print(f"Seed: {seed}")

    sim_id: str = {{simId}}
    sim_instance_id: str = {{simInstanceId}}

    sim_path: str = f"{DATA_PATH}/{sim_id}"
    pathlib.Path(sim_path).mkdir(parents=True, exist_ok=True)

    # write seed to file so that core services can use it
    with open("/tmp/seed", "wb") as f:
        f.write(seed.to_bytes(4, byteorder="little", signed=False))

    with open("/tmp/routing", "w") as f:
        f.write("{{routing}}")

    generate_randomised_ns2(
        waypoint_file=WAYPOINT_FILE, core_xml=CORE_XML, jitter=JITTER, seed=seed
    )

    framework.start()
    logging.basicConfig(level=logging.DEBUG)

    # Prepare experiment
    coreemu = CoreEmu()
    session: Session = coreemu.create_session(_id={{simInstanceId}})
    session.set_state(EventTypes.CONFIGURATION_STATE)

    ServiceManager.add_services("/root/.core/myservices")

    session.open_xml(file_name=CORE_XML, start=True)
    time.sleep(10)

    # Run the experiment
    time.sleep(3600)

    # When the experiment is finished, we set the session to
    # DATACOLLECT_STATE and collect the logs.
    # After that, we shutdown the session, cleanup the generated payloads
    # and manually make sure, that all remaining files of the experiments
    # are gone.
    # Finally, we wait another 10 seconds to make sure everyhing is clean.
    session.set_state(EventTypes.DATACOLLECT_STATE)
    time.sleep(2)
    collect_logs(session_dir=session.session_dir, sim_path=sim_path, instance_id=sim_instance_id)
    coreemu.shutdown()
    os.system("core-cleanup")
    time.sleep(10)

    framework.stop()
