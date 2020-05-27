#! /usr/bin/env python3

import sys
import argparse
import base64
import json
from typing import Any, Dict, List

import requests


def load_payload(path: str) -> str:
    """Loads payload from specified file

    Args:
        path (str): Path to the file containing payload

    Returns:
        str: Content of payload file (encoded as base64 ist content was binary)
    """
    with open(path, "rb") as f:
        contents: bytes = f.read()
        return str(base64.b64encode(contents), encoding="utf-8")


def load_context(path: str) -> Dict[str, Any]:
    """Load bundle context from provided file and parse it to check if it is valid JSON

    Args:
        path (str): Path of the context-file

    Return:
        str:
    """
    with open(path, "r") as f:
        contents: str = f.read()
        # try to parse json to see if it is valid
        decoded = json.loads(contents)
        return decoded


def build_url(address: str, port: int) -> str:
    return f"http://{address}:{port}/rest"


def load_id(path: str) -> Dict[str, str]:
    with open(path, "r") as f:
        ids: Dict[str, str] = json.load(f)
        return ids


def send_bundle(
    rest_url: str, id_file: str, destination: str, payload: str, lifetime: str = "24h"
) -> None:
    ids = load_id(path=id_file)
    data = {
        "uuid": ids["uuid"],
        "arguments": {
            "destination": destination,
            "source": ids["endpoint_id"],
            "creation_timestamp_now": 1,
            "lifetime": lifetime,
            "payload_block": payload,
        },
    }
    response: requests.Response = requests.post(
        f"{rest_url}/build", data=json.dumps(data)
    )
    if response.status_code != 200:
        print(f"Status: {response.status_code}", file=sys.stderr)
        print(response.text, file=sys.stderr)
    else:
        parsed_response = response.json()
        if parsed_response["error"]:
            print(f"ERROR: {parsed_response['error']}", file=sys.stderr)


def send_context_bundle(
    rest_url: str,
    bundle_recipient: str,
    bundle_context: Dict[str, Any],
    bundle_payload: str,
) -> None:
    """Send a bundle via the context-REST agent

    Args:
        rest_url (str): URL of the REST-interface
        bundle_recipient (str): DTN EndpointID of the bundle's recipient
        bundle_context (Dict[str, Any]): Bundle's context
        bundle_payload (str): Bundle payload
    """

    bundle_data: str = json.dumps(
        {
            "recipient": bundle_recipient,
            "context": bundle_context,
            "payload": bundle_payload,
        }
    )

    response: requests.Response = requests.post(f"{rest_url}/send", data=bundle_data)
    if response.status_code != 202:
        print(f"Status: {response.status_code}")
    print(response.text)


def send_context(
    rest_url: str, context_name: str, node_context: Dict[str, Any]
) -> None:
    """Sends node context information to the routing daemon

    Args:
        rest_url (str): URL of the REST-interface
        context_name (str): name of the context item
        node_context (Dict[str, Any]): Actual context
    """
    contest_str: str = json.dumps(node_context)
    response: requests.Response = requests.post(
        f"{rest_url}/context/{context_name}", data=contest_str
    )
    if response.status_code != 202:
        print(f"Status: {response.status_code}", file=sys.stderr)
        print(response.text, file=sys.stderr)
    else:
        print(response.text)


def get_node_context(rest_url: str) -> None:
    """Get all the Node's context information

    Args:
        rest_url (str): URL of the REST-interface
    """
    response: requests.Response = requests.get(f"{rest_url}/context")
    if response.status_code != 200:
        print(f"Status: {response.status_code}")
        print(response.text, file=sys.stderr)
    else:
        print(response.text)


def fetch_pending(rest_url: str, id_file: str) -> None:
    """Fetch bundles addressed to this node"""
    ids = load_id(path=id_file)
    response: requests.Response = requests.post(
        f"{rest_url}/fetch", data=json.dumps({"uuid": ids["uuid"]})
    )
    if response.status_code != 200:
        print(f"Status: {response.status_code}", file=sys.stderr)
        print(response.text, file=sys.stderr)
    else:
        parsed_response = response.json()
        if parsed_response["error"]:
            print(f"ERROR: {parsed_response['error']}", file=sys.stderr)
        else:
            for bundle in parsed_response["bundles"]:
                print(bundle)


def get_size(rest_url: str, p: bool = True) -> int:
    """Get size of stored bundle buffer

    Args:
        rest_url: URL of the REST-interface
        p: Whether the result should be printed to stdout

    Returns:
        Size of store if request was successful, -1 otherwise
    """

    response: requests.Response = requests.get(f"{rest_url}/size")
    response_text = response.text
    if p:
        if response.status_code != 200:
            print(f"Status: {response.status_code}", file=sys.stderr)
            print(response_text, file=sys.stderr)
        else:
            print(response_text)

    if response.status_code != 200:
        return -1
    else:
        return int(response_text)


def register(rest_url: str, endpoint_id: str, uuid_file: str) -> None:
    id_json = json.dumps({"endpoint_id": endpoint_id})
    response: requests.Response = requests.post(f"{rest_url}/register", data=id_json)
    if response.status_code != 200:
        print(f"Status: {response.status_code}", file=sys.stderr)
        print(response.text, file=sys.stderr)
    else:
        parsed_response = response.json()
        if parsed_response["error"]:
            print(f"ERROR: {parsed_response['error']}", file=sys.stderr)
        else:
            print(f"UUID: {parsed_response['uuid']}")
            data = json.dumps(
                {"endpoint_id": endpoint_id, "uuid": parsed_response["uuid"]}
            )
            with open(uuid_file, "w") as f:
                f.write(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interact with dtnd")
    parser.add_argument("interface", help="One of [agent, routing]")
    parser.add_argument("action", help="One of [register, send, fetch, size]")
    parser.add_argument("-p", "--payload", help="Specify payload file")
    parser.add_argument("-c", "--context", help="Specify context file")
    parser.add_argument("-i", "--id", help="Node ID for registration")
    parser.add_argument(
        "-u",
        "--uuid",
        default="id.json",
        help="File containing the uuid which we get from the /register endpoint",
    )
    parser.add_argument(
        "-cn", "--context_name", help="When sending node context, supply its name"
    )
    parser.add_argument(
        "-a", "--address", default="localhost", help="Address of the REST-interface"
    )
    parser.add_argument(
        "-pa",
        "--port_agent",
        type=int,
        default=8080,
        help="Port of REST application agent",
    )
    parser.add_argument(
        "-pr",
        "--port_routing",
        type=int,
        default=35043,
        help="Port of the routing REST-interface",
    )
    parser.add_argument(
        "-r", "--recipient", help="DTN-EndpointID of the bundle's recipient"
    )
    args = parser.parse_args()

    if args.interface == "agent":
        url = build_url(address=args.address, port=args.port_agent)

        if args.action == "send":
            payload = load_payload(path=args.payload)
            send_bundle(
                rest_url=url,
                id_file=args.uuid,
                destination=args.recipient,
                payload=payload,
            )
        elif args.action == "fetch":
            fetch_pending(rest_url=url, id_file=args.uuid)
        elif args.action == "register":
            register(rest_url=url, endpoint_id=args.id, uuid_file=args.uuid)
        else:
            print("UNSUPPORTED ACTION", file=sys.stderr)
    elif args.interface == "routing":
        url = build_url(address=args.address, port=args.port_routing)

        if args.action == "send":
            context = load_context(path=args.context)
            send_context(
                rest_url=url, context_name=args.context_name, node_context=context
            )
        elif args.action == "get":
            get_node_context(rest_url=url)
        else:
            print("UNSUPPORTED ACTION", file=sys.stderr)
    else:
        print("UNKNOWN INTERFACE", file=sys.stderr)
