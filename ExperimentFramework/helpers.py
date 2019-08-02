import os
import uuid


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
