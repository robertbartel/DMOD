import unittest
import dataclasses
from datetime import datetime
from typing import Dict, Tuple
from pathlib import Path
from . import find_git_root_dir
from ..modeldata.config.init_config.snow17 import (Snow17InitConfig, Snow17FileFormatDeserializer,
                                                   Snow17FilesDeserializer, Snow17FileFormatSerializer,
                                                   Snow17FilesSerializer, Validator)

class Snow17TestingExamples:

    def __init__(self):
        self.repo_root = find_git_root_dir()
        test_data_dir = self.repo_root.joinpath("test_data/init_configs")
        self.example_start_dates: Dict[int, datetime] = {
            1: datetime.strptime("2015-12-01 01:00:00", '%Y-%m-%d %H:%M:%S'),
        }
        self.example_end_dates: Dict[int, datetime] = {
            1: datetime.strptime("2015-12-30 23:00:00", '%Y-%m-%d %H:%M:%S'),
        }

        self.example_cfg_dicts = {
            1: {
                "settings": {
                    "SNOW17_CONTROL": {
                        "main_id": "cat-27",
                        "n_hrus": 1,
                        "forcing_root": "data/bmi/forcing/cat-27.csv",
                        "output_root": "",
                        "output_hrus": 0,
                        "start_datehr": 2015120101,
                        "end_datehr": 2015123023,
                        "model_timestep": 3600,
                        "warm_start_run": 0,
                        "write_states": 0,
                        "snow_state_in_root": "",
                        "snow_state_out_root": "",
                    },
                },
                "params": {
                    "hru_id": "cat-27",
                    "hru_area": 2994.7,
                    "latitude": 47.78,
                    "elev": 1612.50,
                    "scf": 1.15177,
                    "mfmax": 0.930472,
                    "mfmin": 0.137,
                    "uadj": 0.013103,
                    "si": 1515.00,
                    "pxtemp": 0.713424,
                    "nmf": 0.150,
                    "tipm": 0.200,
                    "mbase": 0.000,
                    "plwhc": 0.030,
                    "daygm": 0.300,
                    "adc1": 0.050,
                    "adc2": 0.10,
                    "adc3": 0.2,
                    "adc4": 0.3,
                    "adc5": 0.40,
                    "adc6": 0.5,
                    "adc7": 0.6,
                    "adc8": 0.7,
                    "adc9": 0.8,
                    "adc10": 0.9,
                    "adc11": 1.000,
                },
            },
        }
        self.example_cfg_objects = {
            1: Snow17InitConfig(catchment_id="cat-27",
                                forcing_root=Path("data/bmi/forcing/cat-27.csv"),
                                output_root=None,
                                output_hrus=False,
                                start_datehr=self.example_start_dates[1],
                                end_datehr=self.example_end_dates[1],
                                model_timestep=3600,
                                warm_start_run=False,
                                write_states=False,
                                state_in_root=None,
                                state_out_root=None,
                                catchment_area=2994.7,
                                latitude=47.78,
                                elev=1612.50,
                                scf=1.15177,
                                mfmax=0.930472,
                                mfmin=0.137,
                                uadj=0.013103,
                                si=1515.00,
                                pxtemp=0.713424,
                                nmf=0.150,
                                tipm=0.200,
                                mbase=0.000,
                                plwhc=0.030,
                                daygm=0.300,
                                adc1=0.050,
                                adc2=0.10,
                                adc3=0.2,
                                adc4=0.3,
                                adc5=0.40,
                                adc6=0.5,
                                adc7=0.6,
                                adc8=0.7,
                                adc9=0.8,
                                adc10=0.9,
                                adc11=1.000,
                                ),
        }
        self.example_files: Dict[int, Tuple[Path, Path]] = {
            1: (
                test_data_dir.joinpath("snow17-init-ex1.namelist.input"),
                test_data_dir.joinpath("snow17_params.ex1.txt")
            ),
        }


class TestSnow17FileFormatDeserializer(unittest.TestCase):

    def setUp(self):
        self.testing_examples = Snow17TestingExamples()
        self.deserializer = Snow17FileFormatDeserializer()

    def test_deserialization_1_a(self):
        """ Test that deserialization works as expected for example case 1. """
        ex_idx = 1
        ex_dict = self.testing_examples.example_cfg_dicts[ex_idx]
        ex_cfg_obj = self.testing_examples.example_cfg_objects[ex_idx]
        self.assertEqual(ex_cfg_obj, self.deserializer.deserialize(ex_dict))

    def test_deserialization_1_b(self):
        """ Test that deserialization works as expected for example case 1, checking an individual param value. """
        ex_idx = 1
        ex_dict = self.testing_examples.example_cfg_dicts[ex_idx]
        ex_cfg_obj = self.testing_examples.example_cfg_objects[ex_idx]

        deserialized_obj = self.deserializer.deserialize(ex_dict)
        self.assertEqual(ex_dict["params"]["mfmax"], deserialized_obj.mfmax)

        self.assertEqual(ex_cfg_obj, self.deserializer.deserialize(ex_dict))

    def test_deserialization_2_a(self):
        """
        Test that deserialization fails as expected if the object would be created with invalid values.

        For example, if 0.01 for were the value of ``mfmax`` in the created object.  The valid range for ``mfmax`` is
        0.1 to 2.2.
        """
        ex_idx = 1
        base_dict = self.testing_examples.example_cfg_dicts[ex_idx]
        base_dict["params"]["mfmax"] = 0.01

        with self.assertRaises(Validator.ValidationValueError):
            self.deserializer.deserialize(base_dict)


class TestSnow17FileFormatSerializer(unittest.TestCase):

    def setUp(self):
        self.testing_examples = Snow17TestingExamples()
        self.serializer = Snow17FileFormatSerializer()

    def test_serialization_1_a(self):
        """ Test that serialization works as expected for example case 1. """
        ex_idx = 1
        ex_dict = self.testing_examples.example_cfg_dicts[ex_idx]
        ex_cfg_obj = self.testing_examples.example_cfg_objects[ex_idx]
        self.assertEqual(ex_dict, self.serializer.serialize(ex_cfg_obj))


class TestSnow17FilesDeserializer(unittest.TestCase):

    def setUp(self):
        self.testing_examples = Snow17TestingExamples()
        self.deserializer = Snow17FilesDeserializer()

    def test_deserialization_1_a(self):
        """ Test that deserialization works as expected for example case 1. """
        ex_idx = 1
        ex_cfg_obj = self.testing_examples.example_cfg_objects[ex_idx]
        example_files = self.testing_examples.example_files[ex_idx]
        self.assertEqual(ex_cfg_obj, self.deserializer.deserialize(example_files))


class TestSnow17FilesSerializer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.testing_examples = Snow17TestingExamples()
        cls.working_dir = cls.testing_examples.repo_root.joinpath(f".workdir_{cls.__name__}")

        cls.working_dir.mkdir(exist_ok=True)

        cls.created_namelist_basenames = {
            1: f"sac-init-{cls.__name__}_1.namelist.input",
        }
        cls.created_params_file_basenames = {
            1: f"sac-params-{cls.__name__}_1.txt",
        }

    def tearDown(self):
        if self.working_dir.exists():
            for file in self.working_dir.iterdir():
                file.unlink()

    @classmethod
    def tearDownClass(cls):
        cls.working_dir.rmdir()

    def test_serialization_1_a(self):
        """ Test that serialization works as expected for example case 1. """
        ex_idx = 1

        namelist_file = self.working_dir.joinpath(self.created_namelist_basenames[ex_idx])
        params_file = self.working_dir.joinpath(self.created_params_file_basenames[ex_idx])

        # First serialize the object
        serializer = Snow17FilesSerializer(namelist_file, params_file)
        ex_cfg_obj = self.testing_examples.example_cfg_objects[ex_idx]
        serializer.serialize(ex_cfg_obj)

        # To test, deserialize and compare
        deserializer = Snow17FilesDeserializer()
        deser_obj = deserializer.deserialize((namelist_file, params_file))
        self.assertEqual(ex_cfg_obj, deser_obj)


class TestSnow17InitConfig(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.testing_examples = Snow17TestingExamples()
        cls.working_dir = cls.testing_examples.repo_root.joinpath(f".workdir_{cls.__name__}")

        cls.working_dir.mkdir(exist_ok=True)

        cls.created_namelist_basenames = {
            1: f"snow17-init-{cls.__name__}_1.namelist.input",
        }
        cls.created_params_file_basenames = {
            1: f"snow17-params-{cls.__name__}_1.txt",
        }

    def tearDown(self):
        if self.working_dir.exists():
            for file in self.working_dir.iterdir():
                file.unlink()

    @classmethod
    def tearDownClass(cls):
        cls.working_dir.rmdir()

    def test_to_dict_1_a(self):
        """ Test that default serialization works as expected for example case 1. """
        ex_idx = 1
        ex_cfg_obj = self.testing_examples.example_cfg_objects[ex_idx]
        ex_dict = self.testing_examples.example_cfg_dicts[ex_idx]
        self.assertEqual(ex_dict, ex_cfg_obj.to_dict())

    def test_to_dict_1_b(self):
        """ Test that default deserialization works as expected for example case 1. """
        ex_idx = 1

        ex_cfg_obj = self.testing_examples.example_cfg_objects[ex_idx]
        ex_dict = self.testing_examples.example_cfg_dicts[ex_idx]
        self.assertEqual(ex_cfg_obj, Snow17InitConfig.factory_init_from_deserialized_json(ex_dict))

    def test_deserialization_1_b(self):
        """ Test that deserialization works as expected for example case 1, this time. """
        ex_idx = 1

        namelist_file = self.working_dir.joinpath(self.created_namelist_basenames[ex_idx])
        params_file = self.working_dir.joinpath(self.created_params_file_basenames[ex_idx])

        # First serialize the object
        serializer = Snow17FilesSerializer(namelist_file, params_file)
        ex_cfg_obj = self.testing_examples.example_cfg_objects[ex_idx]
        ex_cfg_obj.accept_serializer(serializer)

        # To test, deserialize and compare
        deserializer = Snow17FilesDeserializer()
        deser_obj = deserializer.deserialize((namelist_file, params_file))
        self.assertEqual(ex_cfg_obj, deser_obj)

    def test_validation_1_a(self):
        """ Test that default validation works as expected for valid example case 1. """
        ex_idx = 1
        ex_cfg_obj = self.testing_examples.example_cfg_objects[ex_idx]
        ex_cfg_obj.run_default_validation()

    def test_validation_1_b(self):
        """ Test default validation works as expected for valid example case 1 directly using ``accept_validator``. """
        ex_idx = 1
        ex_cfg_obj = self.testing_examples.example_cfg_objects[ex_idx]
        ex_cfg_obj.accept_validator(ex_cfg_obj.get_default_validator_instance())

    def test_validation_2_a(self):
        """
        Test that validation fails as expected for bad example with unexpected type for catchment id.
        """
        ex_idx = 1
        base_cfg = self.testing_examples.example_cfg_objects[ex_idx]
        invalid_cfg = Snow17InitConfig(**dataclasses.asdict(base_cfg))
        invalid_cfg.catchment_id = 12345
        with self.assertRaises(Validator.ValidationTypeError):
            invalid_cfg.run_default_validation()

    def test_validation_2_b(self):
        """
        Test that validation fails as expected for bad example with unexpected type for ``warm_start_run``.
        """
        ex_idx = 1
        base_cfg = self.testing_examples.example_cfg_objects[ex_idx]
        invalid_cfg = Snow17InitConfig(**dataclasses.asdict(base_cfg))
        invalid_cfg.warm_start_run = 5
        with self.assertRaises(Validator.ValidationTypeError):
            invalid_cfg.run_default_validation()

    def test_validation_2_c(self):
        """
        Test that validation fails as expected for bad example with too small a value (0.008) for ``nmf``.

        The valid range for ``nmf`` is 0.01 to 0.3.
        """
        ex_idx = 1
        base_cfg = self.testing_examples.example_cfg_objects[ex_idx]
        invalid_cfg = Snow17InitConfig(**dataclasses.asdict(base_cfg))
        invalid_cfg.nmf = 0.008
        with self.assertRaises(Validator.ValidationValueError):
            invalid_cfg.run_default_validation()

    def test_validation_2_d(self):
        """
        Test that validation fails as expected for bad example with too large a value (0.5) for ``nmf``.

        The valid range for ``nmf`` is 0.01 to 0.3.
        """
        ex_idx = 1
        base_cfg = self.testing_examples.example_cfg_objects[ex_idx]
        invalid_cfg = Snow17InitConfig(**dataclasses.asdict(base_cfg))
        invalid_cfg.nmf = 0.5
        with self.assertRaises(Validator.ValidationValueError):
            invalid_cfg.run_default_validation()
