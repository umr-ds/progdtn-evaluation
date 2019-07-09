# -*- coding: utf-8 -*-

import time
import os
import shutil
import threading
import sys
import logging

from core import logger as core_logger
from core.service import ServiceManager
from core.xml import xmlsession
from core.emulator.coreemu import CoreEmu
from core.netns.nodes import CoreNode
from core.enumerations import EventTypes

import framework

_ch = logging.StreamHandler(sys.stdout)
_ch.setLevel(logging.DEBUG)
_ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger = logging.getLogger("maci")
logger.addHandler(_ch)
logger.setLevel(logging.DEBUG)

def start_dtnrpc(session, seed):
    for obj in session.objects.itervalues():
        if type(obj) is CoreNode:
            seed_path = '{}/{}.conf/random.seed'.format(session.session_dir, obj.name)
            with open(seed_path, "w") as seed_file:
                seed_file.write("{}".format(obj.objid + int(seed)))
            obj.cmd(['bash', '-c', 'nohup python3 -u /shared/dtnrpc/dtn_rpyc.py -s &> worker_run.log &'])


def prepare_add_file(input_file):
    total_file_size = os.path.getsize(input_file)

    if total_file_size > 20000000:
        too_big_file = open(input_file, 'rb')

        def get_chunk():
            return too_big_file.read(20000000)

        chunk_count = 0
        for chunk in iter(get_chunk, ''):
            chunk_path = '{}_chunk{}'.format(input_file, chunk_count)
            with open(chunk_path, 'wb') as chunk_file:
                chunk_file.write(chunk)
                framework.addBinaryFile(chunk_path)
            chunk_count = chunk_count + 1

        too_big_file.close()

    else:
        framework.addBinaryFile(input_file)


def collect_logs(session_dir):
    for root, _, files in os.walk(session_dir):
        for f in files:
            src_file_path = os.path.join(root, f)

            if 'blob' in src_file_path:
                continue
            if 'serval.log' in src_file_path:
                continue
            if '.conf' not in src_file_path:
                continue

            session_dir_trailing = '{}/'.format(session_dir)
            new_file_name = src_file_path.replace(session_dir_trailing,
                                                  '').replace('/', '_')
            dst_file_path = '{}/{}'.format(os.getcwd(), new_file_name)

            try:
                shutil.move(src_file_path, dst_file_path)
                prepare_add_file(new_file_name)
            except IOError:
                continue

    prepare_add_file('core_session.log')
    prepare_add_file('parameters.py')
    prepare_add_file('log.txt')


def make_session(topo_path, _id, algo):

    fh = logging.FileHandler('core_session.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s'
        ))
    core_logger.addHandler(fh)

    coreemu = CoreEmu()
    session = coreemu.create_session(_id=_id)
    # must be in configuration state for nodes to start.
    session.set_state(EventTypes.CONFIGURATION_STATE)

    # Set the routing algorithm for the experiment
    os.environ['ALGORITHMS'] = algo.replace('_', ',')

    ServiceManager.add_services('/root/.core/myservices')

    session.open_xml(topo_path, start=True)

    session.instantiate()

    return session


def stop_services(session):
    for obj in session.objects.itervalues():
        if type(obj) is CoreNode:

            # kill dtnrpc (blocking)
            obj.cmd(['bash', '-c', 'killall -w python3'])

            # stop all core services
            session.services.stop_services(obj)


def log_positions(session):
    _thread = threading.Timer(10, log_positions, args=[session])
    _thread.daemon = True
    _thread.start()

    for obj in session.objects.itervalues():
        if type(obj) is CoreNode:

            pos_file_path = '{}/{}.conf/trace.xy'.format(
                session.session_dir, obj.name)

            with open(pos_file_path, 'a') as pos_file:
                x, y, _ = obj.position.get()

                pos_file.write('{} {}'.format(x, y))
