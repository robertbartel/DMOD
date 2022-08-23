import yaml
from pathlib import Path
from typing import Optional, Union


class NgenCalConfigTool:

    _GLOBAL_KEY_MODEL = 'model'
    _MODEL_KEY_BINARY = 'binary'
    _MODEL_KEY_PARTITION_CONFIG = 'partitions'

    def __init__(self, initial_config: Path):
        self._yaml_file: Path = initial_config
        with self._yaml_file.open() as file:
            self._backing_config = yaml.safe_load(file)

    @property
    def ngen_binary(self) -> str:
        """
        The ngen binary string, which may be something in PATH or an actual relative or absolute path to an executable.

        Returns
        -------
        str
            The ngen binary string
        """
        return self.model_element.get(self._MODEL_KEY_BINARY)

    @ngen_binary.setter
    def ngen_binary(self, binary: str):
        self.model_element[self._MODEL_KEY_BINARY] = binary

    @property
    def model_element(self) -> dict:
        """
        The model sub-element of the global backing config.

        Returns
        -------
        dict
            The model sub-element of the global backing config.
        """
        return self._backing_config[self._GLOBAL_KEY_MODEL]

    @property
    def partition_config(self) -> Path:
        """
        Path to the partition config file for parallelized ngen execution.

        Returns
        -------
        Path to the partition config file for parallelized ngen execution.
        """
        val = self.model_element.get(self._MODEL_KEY_PARTITION_CONFIG)
        return None if val is None else Path(val)

    @partition_config.setter
    def partition_config(self, partition_config: Union[Path, str]):
        if isinstance(partition_config, str):
            self.model_element[self._MODEL_KEY_PARTITION_CONFIG] = partition_config
        else:
            self.model_element[self._MODEL_KEY_PARTITION_CONFIG] = str(partition_config)

    def write_updates(self, yaml_file: Optional[Path] = None):
        """
        Write updated config to original location or new file.

        Parameters
        ----------
        yaml_file : Optional[Path]
            The file to which the updated configuration should be written, which defaults to the initial config path if
            not provided or set to ``None``.
        """
        if yaml_file is None:
            yaml_file = self._yaml_file
        with yaml_file.open('w') as file:
            yaml.dump(self._backing_config, file)
