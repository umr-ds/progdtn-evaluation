import os

import numpy as np
import pandas as pd

from sklearn import preprocessing

from dtn.helper import parse_experiment


def load_runtimes(experiment_path, columns=['software', 'node_num', 'size', 'id', 'duration']):
    runtimes_df = pd.DataFrame(columns=columns)
    for f in os.listdir(experiment_path):
        experiment = parse_experiment(experiment_path / f)
        runtimes_df = runtimes_df.append({
            'software': experiment.__class__.__name__,
            'node_num': experiment.node_num,
            'size': experiment.size,
            'id': experiment.simInstanceId,
            'duration': experiment.duration,
        }, ignore_index=True)
        
    runtimes_df = runtimes_df.dropna()
     
    runtimes_df['duration'] = runtimes_df['duration'] / np.timedelta64(1, 'ms')
        
    return runtimes_df