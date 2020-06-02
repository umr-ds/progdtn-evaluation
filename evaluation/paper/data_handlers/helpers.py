import pathlib


def parse_parameters(experiment_dir):
    parameters_data = {}
    parameters_path = pathlib.Path(experiment_dir) / "parameters.py"
    
    f = open(parameters_path)
    parameters_code = compile(f.read(), "parameters.py", "exec")
    exec(parameters_code, {}, parameters_data)
        
    f.close()

    return parameters_data["params"]