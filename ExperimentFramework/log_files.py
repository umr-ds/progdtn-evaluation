import os
import shutil

import framework


excluded_files = [
    #DTN7
    "store_n",
    # Serval
    "blob",
    "serval.log",
    "keyring.dump",
    "proc/",
    "rhizome.db",
    "serval.keyring",
    # Forban
    "forban/bin",
    "forban/doc",
    "forban/lib",
    "forban/var/loot",
    "forban/var/share",
    "forban/cfg",
    ".git",
    "AUTHORS",
    "FAQ",
    "README",
    # IBRDTN
    "inbox"
]



def prepare_log_file(input_file):
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


def _is_blacklisted(name):
    for elem in excluded_files:
        if elem in name:
            return True

    return False


def collect_logs(session_dir):
    for root, _, files in os.walk(session_dir):
        for f in files:
            src_file_path = os.path.join(root, f)

            # Ignore all files outside the <nodename>.conf folder
            if '.conf' not in src_file_path:
                continue

            if _is_blacklisted(src_file_path):
                continue

            session_dir_trailing = '{}/'.format(session_dir)
            new_file_name = src_file_path.replace(session_dir_trailing,
                                                  '').replace('/', '_')
            dst_file_path = '{}/{}'.format(os.getcwd(), new_file_name)

            try:
                shutil.move(src_file_path, dst_file_path)
                prepare_log_file(new_file_name)
            except IOError:
                continue

    prepare_log_file('parameters.py')
