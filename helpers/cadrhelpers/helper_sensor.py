#! /usr/bin/env python3

from typing import Any, Dict
from time import sleep
from random import randint, choice

from cadrhelpers.dtnclient import send_context, build_url

REST_ADDRESS = "127.0.0.1"
CONTEXT_PORT = 35043


def send_integer(url: str, name: str) -> None:
    print(f"Sending random integer context with name '{name}'")
    value = {"value": randint(3, 10)}
    send_context(rest_url=url, context_name=name, node_context=value)


def send_random_context(url: str, context: Dict[str, Any]) -> None:
    """Pick and send a random context-item to the node"""
    name: str = choice(context.keys())
    send_context(rest_url=url, context_name=name, node_context=context[name])


if __name__ == "__main__":
    with open("/tmp/seed", "rb") as f:
        seed_bytes = f.read(4)
        seed = int.from_bytes(bytes=seed_bytes, byteorder="little", signed=False)

    print("Starting context generator")
    # context_collection: Dict[str, Any] = load_context(path=args.context_file)
    context_rest: str = build_url(address=REST_ADDRESS, port=CONTEXT_PORT)

    # sleep(10)

    while True:
        # send_random_context(url=context_rest, context=context_collection)
        send_integer(url=context_rest, name="fitness")
        sleep(randint(1, 20))
