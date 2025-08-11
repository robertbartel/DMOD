import unittest
import dataclasses
from datetime import datetime
from typing import Dict, Tuple
from pathlib import Path
from . import find_git_root_dir
from ..modeldata.config.init_config.sacsma import (SacSmaInitConfig, SacSmaFileFormatDeserializer,
                                                   SacSmaFilesDeserializer, SacSmaFileFormatSerializer,
                                                   SacSmaFilesSerializer, Validator)

class SacSmaTestingExamples:

    def __init__(self):
        self.repo_root = find_git_root_dir()
        test_data_dir = self.repo_root.joinpath("test_data/init_configs")
        self.example_start_dates: Dict[int, datetime] = {
            1: datetime.strptime("2015-12-01 12:00:00", '%Y-%m-%d %H:%M:%S'),
        }
        self.example_end_dates: Dict[int, datetime] = {
            1: datetime.strptime("2015-12-30 12:00:00", '%Y-%m-%d %H:%M:%S'),
        }

        self.example_cfg_dicts = {
            1: {
                "settings": {
                    "SAC_CONTROL": {
                        "main_id": "cat-27",
                        "n_hrus": 1,
                        "forcing_root": "data/bmi/forcing/cat-27.csv",
                        "output_root": "",
                        "output_hrus": 0,
                        "start_datehr": 2015120112,
                        "end_datehr": 2015123012,
                        "model_timestep": 3600,
                        "warm_start_run": 0,
                        "write_states": 0,
                        "sac_state_in_root": "",
                        "sac_state_out_root": "",
                    },
                },
                "params": {
                    "hru_id": "cat-27",
                    "hru_area": 8.845200310497782,
                    "uztwm": 59.8237571716309,
                    "uzfwm": 53.759521484375,
                    "lztwm": 164.239395141602,
                    "lzfpm": 114.286056518555,
                    "lzfsm": 18.954044342041,
                    "adimp": 0.0,
                    "uzk": 0.476901233196259,
                    "lzpk": 0.0021645180881023,
                    "lzsk": 0.174269750714302,
                    "zperc": 57.0009422302246,
                    "rexp": 1.84920716285706,
                    "pctim": 0.0,
                    "pfree": 0.178764790296555,
                    "riva": 0.0,
                    "side": 0.0,
                    "rserv": 0.3,
                },
            },
        }
        self.example_cfg_objects = {
            1: SacSmaInitConfig(catchment_id="cat-27",
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
                                catchment_area=8.845200310497782,
                                uztwm=59.8237571716309,
                                uzfwm=53.759521484375,
                                lztwm=164.239395141602,
                                lzfpm=114.286056518555,
                                lzfsm=18.954044342041,
                                adimp=0.0,
                                uzk=0.476901233196259,
                                lzpk=0.0021645180881023,
                                lzsk=0.174269750714302,
                                zperc=57.0009422302246,
                                rexp=1.84920716285706,
                                pctim=0.0,
                                pfree=0.178764790296555,
                                riva=0.0,
                                side=0.0,
                                rserv=0.3
                                ),
        }
        self.example_files: Dict[int, Tuple[Path, Path]] = {
            1: (
                test_data_dir.joinpath("sac-init-ex1.namelist.input"),
                test_data_dir.joinpath("sac_params.ex1.txt")
            ),
        }

class TestSacSmaFileFormatDeserializer(unittest.TestCase):

    def setUp(self):
        self.testing_examples = SacSmaTestingExamples()
        self.deserializer = SacSmaFileFormatDeserializer()

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
        self.assertEqual(ex_dict["params"]["uztwm"], deserialized_obj.uztwm)

        self.assertEqual(ex_cfg_obj, self.deserializer.deserialize(ex_dict))

    def test_deserialization_2_a(self):
        """
        Test that deserialization fails as expected if the object would be created with invalid values.

        For example, if 20.0 for were the value of ``uztwm`` in the created object.  The valid range for ``uztwm`` is
        25.0 to 125.0.
        """
        ex_idx = 1
        base_dict = self.testing_examples.example_cfg_dicts[ex_idx]
        base_dict["params"]["uztwm"] = 20.0

        with self.assertRaises(Validator.ValidationValueError):
            self.deserializer.deserialize(base_dict)


class TestSacSmaFileFormatSerializer(unittest.TestCase):

    def setUp(self):
        self.testing_examples = SacSmaTestingExamples()
        self.serializer = SacSmaFileFormatSerializer()

    def test_serialization_1_a(self):
        """ Test that serialization works as expected for example case 1. """
        ex_idx = 1
        ex_dict = self.testing_examples.example_cfg_dicts[ex_idx]
        ex_cfg_obj = self.testing_examples.example_cfg_objects[ex_idx]
        self.assertEqual(ex_dict, self.serializer.serialize(ex_cfg_obj))


class TestSacSmaFilesDeserializer(unittest.TestCase):

    def setUp(self):
        self.testing_examples = SacSmaTestingExamples()
        self.deserializer = SacSmaFilesDeserializer()

    def test_deserialization_1_a(self):
        """ Test that deserialization works as expected for example case 1. """
        ex_idx = 1
        ex_cfg_obj = self.testing_examples.example_cfg_objects[ex_idx]
        example_files = self.testing_examples.example_files[ex_idx]
        self.assertEqual(ex_cfg_obj, self.deserializer.deserialize(example_files))


class TestSacSmaFilesSerializer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.testing_examples = SacSmaTestingExamples()
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
        serializer = SacSmaFilesSerializer(namelist_file, params_file)
        ex_cfg_obj = self.testing_examples.example_cfg_objects[ex_idx]
        serializer.serialize(ex_cfg_obj)

        # To test, deserialize and compare
        deserializer = SacSmaFilesDeserializer()
        deser_obj = deserializer.deserialize((namelist_file, params_file))
        self.assertEqual(ex_cfg_obj, deser_obj)


class TestSacSmaInitConfig(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.testing_examples = SacSmaTestingExamples()
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
        self.assertEqual(ex_cfg_obj, SacSmaInitConfig.factory_init_from_deserialized_json(ex_dict))

    def test_deserialization_1_b(self):
        """ Test that deserialization works as expected for example case 1, this time. """
        ex_idx = 1

        namelist_file = self.working_dir.joinpath(self.created_namelist_basenames[ex_idx])
        params_file = self.working_dir.joinpath(self.created_params_file_basenames[ex_idx])

        # First serialize the object
        serializer = SacSmaFilesSerializer(namelist_file, params_file)
        ex_cfg_obj = self.testing_examples.example_cfg_objects[ex_idx]
        ex_cfg_obj.accept_serializer(serializer)

        # To test, deserialize and compare
        deserializer = SacSmaFilesDeserializer()
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
        invalid_cfg = SacSmaInitConfig(**dataclasses.asdict(base_cfg))
        invalid_cfg.catchment_id = 12345
        with self.assertRaises(Validator.ValidationTypeError):
            invalid_cfg.run_default_validation()

    def test_validation_2_b(self):
        """
        Test that validation fails as expected for bad example with unexpected type for ``warm_start_run``.
        """
        ex_idx = 1
        base_cfg = self.testing_examples.example_cfg_objects[ex_idx]
        invalid_cfg = SacSmaInitConfig(**dataclasses.asdict(base_cfg))
        invalid_cfg.warm_start_run = 5
        with self.assertRaises(Validator.ValidationTypeError):
            invalid_cfg.run_default_validation()

    def test_validation_2_c(self):
        """
        Test that validation fails as expected for bad example with too small a value (20.0) for ``uztwm``.

        The valid range for ``uztwm`` is 25.0 to 125.0.
        """
        ex_idx = 1
        base_cfg = self.testing_examples.example_cfg_objects[ex_idx]
        invalid_cfg = SacSmaInitConfig(**dataclasses.asdict(base_cfg))
        invalid_cfg.uztwm = 20.0
        with self.assertRaises(Validator.ValidationValueError):
            invalid_cfg.run_default_validation()

    def test_validation_2_d(self):
        """
        Test that validation fails as expected for bad example with too large a value (120.0) for ``uzfwm``.

        The valid range for ``uzfwm`` is 10.0 to 100.0.
        """
        ex_idx = 1
        base_cfg = self.testing_examples.example_cfg_objects[ex_idx]
        invalid_cfg = SacSmaInitConfig(**dataclasses.asdict(base_cfg))
        invalid_cfg.uzfwm = 120.0
        with self.assertRaises(Validator.ValidationValueError):
            invalid_cfg.run_default_validation()
