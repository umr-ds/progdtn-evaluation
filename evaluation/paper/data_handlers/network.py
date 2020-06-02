import glob
import os

import pandas as pd
pd.set_option('display.max_rows', 500)

from .helpers import parse_parameters


BWM_HEADERS_COMPLETE = ["ts", "iface", "bytes_out/s", "bytes_in/s", "bytes_total/s", "bytes_in", "bytes_out", "packets_out/s", "packets_in/s", "packets_total/s", "packets_in", "packets_out", "errors_out/s", "errors_in/s", "errors_in", "errors_out"]

BWM_HEADERS = ["ts", "iface", "bytes_out/s"]


def parse_bwm(bwm_path):
    df = pd.read_csv(bwm_path, sep=";", usecols=[0, 1, 2], names=BWM_HEADERS)
    
    #df = df[pd.to_numeric(df['bytes_out/s'], errors='coerce').notnull()]
    df['bytes_out/s'] = df['bytes_out/s'].astype(float)
    
    # BWM tends to spit our very large numbers if not shutdown correctly.
    # We want to avoid them, so just remove large numbers.
    df = df.loc[df['bytes_out/s'] < 54000000 * 100]
    df = df.loc[df['iface'] == 'total']
    
    try:
        df["ts"] = pd.to_datetime(df["ts"], unit="s")
    except Exception as e:
        print(bwm_path)
        raise e
    df["node"] = os.path.basename(bwm_path).split(".")[0]
    
    dir_path = os.path.dirname(bwm_path)
    parameters = parse_parameters(dir_path)
    
    df['software'] = parameters['software']
    df['size'] = parameters['size']
    df['id'] = parameters['simInstanceId']
    df['node_num'] = parameters['node_num']
    
    return df

def parse_bwms_instance(instance_path):
    bwm_paths = glob.glob(os.path.join(instance_path, "*.conf_bwm.csv"))

    parsed_bwms = [parse_bwm(p) for p in bwm_paths]
    df = pd.concat(parsed_bwms, sort=False)
    df = df.sort_values(["ts", "node"]).reset_index()
        
    df["dt"] = (df["ts"] - df["ts"].iloc[0]).dt.total_seconds()
        
    return df
    

def parse_bwms(experiment_path):
    instance_paths = glob.glob(os.path.join(experiment_path, "*"))
    
    parsed_instances = [parse_bwms_instance(path) for path in instance_paths]
    df = pd.concat(parsed_instances, sort=False)
    df = df.sort_values(["ts", "id", "node"]).reset_index()
        
    return df