import pathlib

from abc import abstractmethod

from data_handlers.helpers import parse_parameters


class DtnSoftware:

    def __init__(self, experiment_dir):
        """ Open a MACI experiment directory and parse its parameters.py file.
            The `params` dict will be included to this class' variables.
        """
        self.experiment_dir = pathlib.Path(experiment_dir)

        parameters_data = parse_parameters(experiment_dir)
        self.__dict__ = {**self.__dict__, **parameters_data}

    @property
    @abstractmethod
    def duration(self):
        """ Calculate the duration for a transmission between the first and the
            `node_num`s node as a datetime.timedelta. This method needs to be
            implemented.
        """
        pass
 
    def __str__(self):
        class_name = type(self).__name__
        return f"{class_name} ({self.node_num}, {self.size}, {self.simInstanceId}): {self.duration}"
