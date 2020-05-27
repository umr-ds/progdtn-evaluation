#! /usr/bin/env python3

import sys
import argparse
import base64
import json
from typing import Any, Dict, List
from dataclasses import dataclass

import requests


@dataclass()
class RESTError(Exception):
    status_code: int
    error: str


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
    """Load bundle context from provided file and parse it to check if it is valid JSON"""
    with open(path, "r") as f:
        contents: str = f.read()
        # try to parse json to see if it is valid
        decoded = json.loads(contents)
        return decoded


def build_url(address: str, port: int) -> str:
    return f"http://{address}:{port}/rest"


def load_registration_data(path: str) -> Dict[str, str]:
    with open(path, "r") as f:
        ids: Dict[str, str] = json.load(f)
        return ids


def register(
    rest_url: str, endpoint_id: str, registration_data_file: str = ""
) -> Dict[str, str]:
    """Registers the client with the REST Application Agent

    Args:
        rest_url: Address + Port+ Prefix for REST actions
        endpoint_id: BPv7 endpoint ID used for registration
        registration_data_file: If set, registration data will be written to a file

    Returns:
        Dictionary with two fields:
            "endpoint_id" contains the same value as was provided
            "uuid": token received from the server which is necessary for future actions

    Raises:
        RESTError if anything goes wrong
    """
    id_json = json.dumps({"endpoint_id": endpoint_id})
    response: requests.Response = requests.post(f"{rest_url}/register", data=id_json)
    if response.status_code != 200:
        raise RESTError(status_code=response.status_code, error=response.text)

    parsed_response = response.json()
    if parsed_response["error"]:
        raise RESTError(
            status_code=response.status_code, error=parsed_response["error"]
        )

    data = {"endpoint_id": endpoint_id, "uuid": parsed_response["uuid"]}
    marshaled = json.dumps(data)
    if registration_data_file:
        with open(registration_data_file, "w") as f:
            f.write(marshaled)
    return data


def fetch_pending(rest_url: str, uuid: str) -> List[Dict[str, Any]]:
    """Fetch bundles addressed to this node

    Args:
        rest_url: Address + Port+ Prefix for REST actions
        uuid: Authentication token received via the register-method.

    Returns:
        List of all pending bundle's addressed to this node as a unmarshaled JSON object

    Raises:
        RESTError if anything goes wrong
    """
    response: requests.Response = requests.post(
        f"{rest_url}/fetch", data=json.dumps({"uuid": uuid})
    )
    if response.status_code != 200:
        raise RESTError(status_code=response.status_code, error=response.text)

    parsed_response = response.json()
    if parsed_response["error"]:
        raise RESTError(
            status_code=response.status_code, error=parsed_response["error"]
        )

    return parsed_response["bundles"]


def _submit_bundle(rest_url: str, data: Dict[str, Any]) -> None:
    response: requests.Response = requests.post(
        f"{rest_url}/build", data=json.dumps(data)
    )
    if response.status_code != 200:
        raise RESTError(status_code=response.status_code, error=response.text)

    parsed_response = response.json()
    if parsed_response["error"]:
        raise RESTError(
            status_code=response.status_code, error=parsed_response["error"]
        )


def send_bundle(
    rest_url: str,
    uuid: str,
    source: str,
    destination: str,
    payload: str,
    lifetime: str = "24h",
) -> None:
    """Sends a bundle via the REST application agent

    Args:
        rest_url: Address + Port+ Prefix for REST actions
        uuid: Authentication token received via the register-method.
        source: BPv7 endpoint ID which will be set as the bundle's source.
                Needs to be one of the IDs of the agent's node
        destination: BPv7 endpoint ID which will be set as the bundle's destination
        payload: Bundle payload, should be a plaintext string or base64 encoded binary data
        lifetime: Time until the bundle expires and is deleted from node stores

    Raises:
        RESTError if anything goes wrong
    """
    data = {
        "uuid": uuid,
        "arguments": {
            "destination": destination,
            "source": source,
            "creation_timestamp_now": 1,
            "lifetime": lifetime,
            "payload_block": payload,
        },
    }
    _submit_bundle(rest_url=rest_url, data=data)


def send_context_bundle(
    rest_url: str,
    uuid: str,
    source: str,
    destination: str,
    payload: str,
    context: Dict[str, Any],
    lifetime: str = "24h",
) -> None:
    """Same as send_bundle, but adds an extension block for context data"""
    data = {
        "uuid": uuid,
        "arguments": {
            "destination": destination,
            "source": source,
            "creation_timestamp_now": 1,
            "lifetime": lifetime,
            "payload_block": payload,
            "context_block": context,
        },
    }
    _submit_bundle(rest_url=rest_url, data=data)


def send_context(rest_url: str, context_name: str, node_context: Dict[str, Any]) -> str:
    """Sends node context information to the routing daemon

    Args:
        rest_url (str): Address + Port+ Prefix for REST actions
        context_name (str): name of the context item
        node_context (Dict[str, Any]): Actual context

    Raises:
        RESTError if anything goes wrong
    """
    contest_str: str = json.dumps(node_context)
    response: requests.Response = requests.post(
        f"{rest_url}/context/{context_name}", data=contest_str
    )
    if response.status_code != 202:
        raise RESTError(status_code=response.status_code, error=response.text)

    return response.text


def get_node_context(rest_url: str) -> Dict[str, Any]:
    """Get all the Node's context information

    Args:
        rest_url (str): Address + Port+ Prefix for REST actions

    Raises:
        RESTError if anything goes wrong
    """
    response: requests.Response = requests.get(f"{rest_url}/context")
    if response.status_code != 200:
        raise RESTError(status_code=response.status_code, error=response.text)

    return response.json()


def get_size(rest_url: str) -> int:
    """Get size of stored bundle buffer

    Args:
        rest_url: Address + Port+ Prefix for REST actions

    Returns:
        Size of store

    Raises:
        RESTError if anything goes wrong
    """
    response: requests.Response = requests.get(f"{rest_url}/size")
    response_text = response.text

    if response.status_code != 200:
        raise RESTError(status_code=response.status_code, error=response.text)

    return int(response_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interact with dtnd")
    parser.add_argument("interface", help="One of [agent, routing]")
    parser.add_argument("action", help="One of [register, send, fetch, size]")
    parser.add_argument("-p", "--payload", help="Specify payload file")
    parser.add_argument("-c", "--context", help="Specify context file")
    parser.add_argument("-i", "--id", help="Node ID for registration")
    parser.add_argument(
        "-r",
        "--registration_data",
        default="registration_data.json",
        help="File containing the registration data which we get from the /register endpoint",
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
        "-d", "--destination", help="DTN-EndpointID of the bundle's recipient"
    )
    args = parser.parse_args()

    if args.interface == "agent":
        url = build_url(address=args.address, port=args.port_agent)

        if args.action == "send":
            payload = load_payload(path=args.payload)
            if args.context:
                registration_data = load_registration_data(path=args.registration_data)
                try:
                    context = load_context(args.context)
                    send_context_bundle(
                        rest_url=url,
                        uuid=registration_data["uuid"],
                        source=registration_data["endpoint_id"],
                        destination=args.destination,
                        payload=payload,
                        context=context,
                    )
                except RESTError as err:
                    print(f"HTTP Status: {err.status_code}", file=sys.stderr)
                    print(f"Error: {err.error}", file=sys.stderr)
            else:
                try:
                    registration_data = load_registration_data(
                        path=args.registration_data
                    )
                    send_bundle(
                        rest_url=url,
                        uuid=registration_data["uuid"],
                        source=registration_data["endpoint_id"],
                        destination=args.destination,
                        payload=payload,
                    )
                except RESTError as err:
                    print(f"HTTP Status: {err.status_code}", file=sys.stderr)
                    print(f"Error: {err.error}", file=sys.stderr)

        elif args.action == "fetch":
            registration_data = load_registration_data(path=args.registration_data)
            try:
                pending = fetch_pending(rest_url=url, uuid=registration_data["uuid"])
                if pending:
                    print("Pending Bundles:")
                    for bundle in pending:
                        print(bundle)
                else:
                    print("No new bundles")
            except RESTError as err:
                print(f"HTTP Status: {err.status_code}", file=sys.stderr)
                print(f"Error: {err.error}", file=sys.stderr)

        elif args.action == "register":
            try:
                registration_data = register(
                    rest_url=url,
                    endpoint_id=args.id,
                    registration_data_file=args.registration_data,
                )
                print(f"Registration data: {registration_data}")
            except RESTError as err:
                print(f"HTTP Status: {err.status_code}", file=sys.stderr)
                print(f"Error: {err.error}", file=sys.stderr)

        else:
            print("UNSUPPORTED ACTION", file=sys.stderr)
    elif args.interface == "routing":
        url = build_url(address=args.address, port=args.port_routing)

        if args.action == "send":
            context = load_context(path=args.context)
            try:
                response = send_context(
                    rest_url=url, context_name=args.context_name, node_context=context
                )
                print(response)
            except RESTError as err:
                print(f"HTTP Status: {err.status_code}", file=sys.stderr)
                print(f"Error: {err.error}", file=sys.stderr)

        elif args.action == "fetch":
            try:
                node_context = get_node_context(rest_url=url)
                print("Node Context:")
                print(node_context)
            except RESTError as err:
                print(f"HTTP Status: {err.status_code}", file=sys.stderr)
                print(f"Error: {err.error}", file=sys.stderr)

        elif args.action == "size":
            try:
                size = get_size(rest_url=url)
                print(f"Store size: {size}")
            except RESTError as err:
                print(f"HTTP Status: {err.status_code}", file=sys.stderr)
                print(f"Error: {err.error}", file=sys.stderr)

        else:
            print("UNSUPPORTED ACTION", file=sys.stderr)
    else:
        print("UNKNOWN INTERFACE", file=sys.stderr)
