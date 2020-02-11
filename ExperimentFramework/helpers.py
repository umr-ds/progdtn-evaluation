import os
import uuid

from core.emulator.coreemu import CoreEmu
from core.emulator.enumerations import EventTypes
from core.nodes.base import CoreNode
from core.services import ServiceManager


def cleanup_payloads():
    dir_name = "/tmp/"
    files = os.listdir(dir_name)

    for item in files:
        if item.endswith(".file"):
            os.remove(os.path.join(dir_name, item))


def create_payload(size):
    path = "/tmp/{}.file".format(uuid.uuid4())

    with open(path, "wb") as f:
        f.write(os.urandom(size))
    return path


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
