### ENV string routing "Routing algorithm"
### ENV int payload_size "Size of generated payloads"
### ENV int bundles_per_node "How many bundles should each sensor generate."

import os
import time
import logging
import pathlib
import toml

from random import choices
from string import ascii_letters, digits

from core.emulator.coreemu import CoreEmu, Session
from core.emulator.enumerations import EventTypes
from core.services import ServiceManager

import framework
from log_files import *


EXPERIMENT_CONFIG = "/dtn_routing/experiment_config.toml"
DATA_PATH = "/research_data"
CORE_XML = "/dtn_routing/scenarios/responders/responders.xml"
PAYLOAD_PATH = "/tmp/payload"
JITTER = 30.0
WIFI_RANGE = 275.0


if __name__ in ["__main__", "__builtin__"]:
    # generate experiment configuration
    experiment_config = {"Scenario": {}, "Experiment": {}, "REST": {}}

    # [Experiment]
    seed: int = {{seed}}
    print(f"Seed: {seed}")
    experiment_config["Experiment"]["seed"] = seed
    routing: str = "{{routing}}"
    experiment_config["Experiment"]["routing"] = routing
    payload_size: int = {{payload_size}}
    experiment_config["Experiment"]["payload_size"] = payload_size
    bundles_per_node: int = {{bundles_per_node}}
    experiment_config["Experiment"]["bundles_per_node"] = bundles_per_node
    experiment_config["Experiment"]["payload_path"] = PAYLOAD_PATH
    experiment_config["Experiment"]["generate_payload"] = False

    # [Scenario]
    experiment_config["Scenario"]["xml"] = CORE_XML
    experiment_config["Scenario"]["wifi_range"] = WIFI_RANGE

    # [REST]
    experiment_config["REST"]["address"] = "localhost"
    experiment_config["REST"]["agent_port"] = 8080
    experiment_config["REST"]["routing_port"] = 35043

    # write experiment configuration
    with open(EXPERIMENT_CONFIG, "w") as f:
        toml.dump(experiment_config, f)

    # generate payload
    payload: str = "".join(
        choices(ascii_letters + digits, k={{payload_size}})
    )
    with open(PAYLOAD_PATH, "w") as f:
        f.write(payload)

    sim_id: str = {{simId}}
    sim_instance_id: str = {{simInstanceId}}

    sim_path: str = f"{DATA_PATH}/{sim_id}"
    pathlib.Path(sim_path).mkdir(parents=True, exist_ok=True)

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
    time.sleep(600)

    # When the experiment is finished, we set the session to
    # DATACOLLECT_STATE and collect the logs.
    # After that, we shutdown the session, cleanup the generated payloads
    # and manually make sure, that all remaining files of the experiments
    # are gone.
    # Finally, we wait another 10 seconds to make sure everyhing is clean.
    session.set_state(EventTypes.DATACOLLECT_STATE)
    time.sleep(2)
    collect_logs(
        session_dir=session.session_dir, sim_path=sim_path, instance_id=sim_instance_id
    )
    coreemu.shutdown()
    os.system("core-cleanup")
    time.sleep(10)

    framework.stop()
