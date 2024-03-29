import os
import uuid


def cleanup_payloads() -> None:
    dir_name = "/tmp/"
    files = os.listdir(dir_name)

    for item in files:
        if item.endswith(".file"):
            os.remove(os.path.join(dir_name, item))


def create_payload(size: int) -> str:
    path = f"/tmp/{uuid.uuid4()}.file"

    with open(path, "wb") as f:
        f.write(os.urandom(size))
    return path
