from dataclasses import dataclass, fields
from pathlib import Path
from datetime import datetime
from types import NoneType
from typing import Optional, Self, Tuple
from dmod.modeldata.hydrofabric.hydrofabric import HydrofabricCatchment

from dmod.core.serializable_v2 import (Deserializer, SERIALIZABLE_AS_DICT, Serializer, SimpleSerializable,
                                       Validator, Validated, Interval, IntervalStringSerializer, from_namelist_str,
                                       from_param_txt_str, to_namelist_str, to_param_txt_str, O, T)


@dataclass(slots=True)
class SacSmaInitConfig(SimpleSerializable, Validated):
    """
    Representation of BMI init config for Sac-SMA.

    Note that this type is designed to model (in a software design sense) a Sac-SMA config.  It contains the required
    state variables - be they module execution settings or scientific modeling parameters - to represent the
    configuration.  Importantly, it's design is (for the most part) detached from various possible usages of such a
    config, including how the way the config is written to files on disk that are used by the module.  That is a concern
    for serialization, which is handled by dedicated ::class:`Serializer` and ::class:`Deserializer` classes.

    Attributes
    ----------
    catchment_id: str
        ID of catchment/hru (synonymous with ``main_id`` and ``hru_id``).
    catchment_area: float
        Area of catchment/hru (synonymous with ``hru_area``).
    forcing_root: Path
        Path to forcing data root (which is really going to be a forcing file in this usage).
    output_root: Optional[Path]
        Path to output data root, when ``output_hrus`` is ``True``; otherwise ``None``.
    output_hrus: bool
        Whether Sac-SMA module should output HRU results.
    start_datehr: datetime
        A start date and time for the simulation, though with precision down to the hour (provided args are stripped of
        other components).
    end_datehr: datetime
        An end date and time for the simulation, though with precision down to the hour (provided args are stripped of
        other components).
    model_timestep: int
        The timestep size for the module to use, in seconds.
    state_in_root: Optional[Path]
        Directory from which to read restart state file(s), when ``warm_start_run`` is ``True``; otherwise ``None``.
    state_out_root: Path
        Directory to write restart files for "warm start" runs, when ``write_states`` is ``True``; otherwise ``None``.
    warm_start_run: bool
        Whether to start from a warm start file.
    write_states: bool
        Whether to write restart files for subsequent "warm start" runs.
    uztwm: float
        Max upper zone tension water [mm]
    uzfwm: float
        Max upper zone free water [mm]
    lztwm: float
        Max lower zone tension water [mm]
    lzfpm: float
        Max lower zone free water, primary [mm]
    lzfsm: float
        Max lower zone free water, secondary (aka supplemental) [mm]
    adimp: float
        Additional impervious area due to saturation [decimal percentage]
    uzk: float
        Upper zone recession coefficient [per day]
    lzpk: float
        Lower zone recession coefficient, primary [decimal percentage]
    lzsk: float
        Lower zone recession coefficient, secondary (aka supplemental) [decimal percentage]
    zperc: float
        Minimum percolation rate coefficient
    rexp: float
        Percolation equation exponent
    pctim: float
        Minimum percent impervious area [decimal percent]
    pfree: float
        Percent percolating directly to lower zone free water [decimal percent]
    riva: float
        Percent of the basin that is riparian area [decimal percent]
    side: float
        Portion of the baseflow which does not go to the stream [decimal percent]
    rserv: float
        Percent of lower zone free water not transferable to the lower zone tension water [decimal percent]
    """

    catchment_id: str

    # Technically cat area goes under "params" but has to come before we start fields with default values
    catchment_area: float

    forcing_root: Path
    output_root: Optional[Path]
    start_datehr: datetime
    end_datehr: datetime
    state_in_root: Optional[Path]
    state_out_root: Optional[Path]

    model_timestep: int = 3600
    output_hrus: bool = False
    warm_start_run: bool = False
    write_states: bool = False

    # The rest of the "Params" specific attributes
    uztwm: float = 75.0
    uzfwm: float = 30.0
    lztwm: float = 150.0
    lzfpm: float = 300.0
    lzfsm: float = 150.0
    adimp: float = 0.0
    uzk: float = 0.3
    lzpk: float = 0.01
    lzsk: float = 0.1
    zperc: float = 100.0
    rexp: float = 2.0
    pctim: float = 0.0
    pfree: float = 0.1
    riva: float = 0.0
    side: float = 0.0
    rserv: float = 0.3

    @classmethod
    def get_default_deserializer_instance(cls) -> Deserializer[Self, SERIALIZABLE_AS_DICT]:
        return SacSmaFileFormatDeserializer()

    def __post_init__(self, *args, **kwargs):
        self.start_datehr = datetime(year=self.start_datehr.year, month=self.start_datehr.month,
                                     day=self.start_datehr.day, hour=self.start_datehr.hour)
        self.end_datehr = datetime(year=self.end_datehr.year, month=self.end_datehr.month,
                                   day=self.end_datehr.day, hour=self.end_datehr.hour)

    @property
    def hru_id(self) -> str:
        """ Alias for catchment_id, used in certain contexts. """
        return self.catchment_id

    @property
    def hru_area(self) -> float:
        """ Alias for catchment_area, used in certain contexts. """
        return self.catchment_area

    @property
    def n_hrus(self) -> int:
        """
        Property of a Sac-SMA config representing the number of HRUs/catchments it applies to, though constrained to
        always be ``1`` for this implementation.
        """
        return 1

    @property
    def main_id(self) -> str:
        """ Alias for catchment_id, used in certain contexts. """
        return self.catchment_id

    def get_default_serializer_instance(self) -> Serializer[Self, SERIALIZABLE_AS_DICT]:
        return SacSmaFileFormatSerializer()

    def get_default_validator_instance(self) -> Validator[Self]:
        return SacSmaSimpleValidator()


class SacSmaSimpleValidator(Validator[SacSmaInitConfig]):
    """
    Simple validator for Sac-SMA init config objects.

    This type does not concern itself with whether any ::class:`Path` attribute values are reasonable (e.g., a file
    exists at the path, etc.).  It only validates that it is a path value.

    However, the logic for validating paths is organized in a dedicated function (::method:`validate_path_values`) that
    is called by the main validation function (::method:`validate_values`).  The base implementation of
    ::method:`validate_path_values` is a no-op, but it can be overridden in subclasses to customize the path validation
    logic, while not having to override/re-write the rest of the base class's value validation.
    """

    def validate_path_values(self, obj: SacSmaInitConfig):
        """
        Separate function for path value validation portion of this types validation logic (no-op in this type).
        
        Default, no-op implementation of separate function called by ::method:`validate_values` to organize the logic of
        path attribute validation.  Subclasses may override this method to implement their own more robust path 
        validation and otherwise maintain the same value validation as this base class.

        Subtypes should keep in mind
        
        Parameters
        ----------
        obj
            The ::class:`SacSmaInitConfig` object being validated.
        """
        pass

    def validate_types(self, obj: SacSmaInitConfig):
        """
        Validate that all attributes of the object being validated are of the expected type.

        Parameters
        ----------
        obj
            The ::class:`SacSmaInitConfig` object being validated.

        Raises
        -------
        TypeError
            If any attribute value is not of the expected type.
        """
        incorrect = ((f.name, f.type) for f in fields(obj) if not isinstance(getattr(obj, f.name), f.type))
        attr, attr_type = next(iter(incorrect), (None, None))
        if attr:
            raise Validator.ValidationTypeError(
                f"'{obj.__class__.__name__}' expected '{attr}' attribute to be of type {attr_type}, but was of "
                f"type {type(getattr(obj, attr)).__name__} instead"
            )

        # Also need more specific checking of these, as they depend on another value
        var_expected_types = {
            'output_root': Path if obj.output_hrus else NoneType,
            'state_in_root': Path if obj.warm_start_run else NoneType,
            'state_out_root': Path if obj.write_states else NoneType,
        }
        dependent_attr = {
            'output_root': 'output_hrus',
            'state_in_root': 'warm_start_run',
            'state_out_root': 'write_states',
        }

        incorrect = ((a, a_type) for a, a_type in var_expected_types.items() if not isinstance(getattr(obj, a), a_type))
        attr, attr_type = next(iter(incorrect), (None, None))
        if attr:
            raise Validator.ValidationTypeError(
                f"'{obj.__class__.__name__}' expected '{attr}' to be of type {attr_type} based on the value of "
                f"'{dependent_attr[attr]}', but value was of type {type(getattr(obj, attr)).__name__} instead"
            )

    def validate_values(self, obj: SacSmaInitConfig):
        """
        Validate attribute values for the given object are in acceptable ranges or are otherwise sane and valid.

        Parameters
        ----------
        obj
            The ::class:`SacSmaInitConfig` object being validated.

        Raises
        -------
        ValueError
            Raised if any of the attributes values are not valid.
        """
        if not obj.catchment_id:
            raise Validator.ValidationValueError(
                f"{self.__class__.__name__} requires a valid catchment ID but received {obj.catchment_id!s}.")
        if obj.catchment_area <= 0:
            raise Validator.ValidationValueError(
                f"{self.__class__.__name__} requires a positive catchment area but received {obj.catchment_area!s}.")
        if obj.model_timestep <= 0:
            raise Validator.ValidationValueError(
                f"{self.__class__.__name__} requires a positive model timestep but received {obj.model_timestep!s}.")

        # Defer to this to organize and separate validation of path values if/when needed
        self.validate_path_values(obj)
        attr_intervals = {
            "uztwm": {"min_val": 25.0, "max_val": 125.0},
            "uzfwm": {"min_val": 10.0, "max_val": 100.0},
            "lztwm": {"min_val": 75.0, "max_val": 300.0},
            "lzfpm": {"min_val": 40.0, "max_val": 600.0},
            "lzfsm": {"min_val": 15.0, "max_val": 300.0},
            "adimp": {"min_val": 0.0, "max_val": 0.2},
            "uzk": {"min_val": 0.2, "max_val": 0.5},
            "lzpk": {"min_val": 0.001, "max_val": 0.015},
            "lzsk": {"min_val": 0.03, "max_val": 0.2},
            "zperc": {"min_val": 20, "max_val": 300},
            "rexp": {"min_val": 1.4, "max_val": 3.5},
            "pctim": {"min_val": 0.0, "max_val": 0.05},
            "pfree": {"min_val": 0.0, "max_val": 0.5},
            "riva": {"min_val": 0.0, "max_val": 0.2},
            "side": {"min_val": 0.0, "max_val": 0.2},
            "rserv": {"min_val": 0.2, "max_val": 0.4}
        }
        for attr, attr_range in attr_intervals.items():
            val = getattr(obj, attr)
            interval = Interval.get_default_deserializer_instance().deserialize(attr_intervals.get(attr))
            if not interval.contains(val):
                raise Validator.ValidationValueError(
                    f"{self.__class__.__name__} requires attribute '{attr}' to be in range "
                    f"{IntervalStringSerializer().serialize(interval)} but received '{val!s}'."
                )


# TODO: (later) perhaps implement these later and apply them to the config class
# class DefaultSacSmaSerializer(Serializer[SacSmaInitConfig, SERIALIZABLE_AS_DICT]):
#     """
#     Default serializer for Sac-SMA init config objects, that leverages that it is a dataclass.
#     """
#
#     def serialize(self, serializable: SacSmaInitConfig) -> SERIALIZABLE_AS_DICT:
#         """
#         Serialize the given Sac-SMA init config object to a serialized dictionary.
#
#         Parameters
#         ----------
#         serializable
#             A Sac-SMA init config object.
#
#         Returns
#         -------
#         The serialized dictionary representing the given Sac-SMA init config object.
#         """


class SacSmaFileFormatDeserializer(Deserializer[SacSmaInitConfig, SERIALIZABLE_AS_DICT]):
    """
    Deserializer of Sac-SMA init config objects that converts them from JSON dictionaries mirroring the arrangement of
    data used in the namelist and params files loaded by the module itself.

    Note that this type does validate deserialized objects before returning them.
    """

    __slots__ = ["_validator"]

    @classmethod
    def control_section_key(cls) -> str:
        """
        Get the key to use for the "controls" section of the serialized dictionary.

        Get the key to use for the "controls" section of the serialized dictionary, as used in dictionary basis for
        namelist files when serializing to file.

        Returns
        -------
        Get the key to use for the "controls" section of the serialized dictionary.
        """
        return "SAC_CONTROL"

    def __init__(self, validator: Optional[Validator[SacSmaInitConfig]] = None ):
        """
        Initialize.

        Parameters
        ----------
        validator
            Optional validator to use to validate before returning deserialized objects; if ``None`` (the default), a
            ::class:`SacSmaSimpleValidator` instance is created and used.
        """
        self._validator = validator if validator is not None else SacSmaSimpleValidator()

    def deserialize(self, serialized_form: SERIALIZABLE_AS_DICT) -> SacSmaInitConfig:
        """
        Deserialize the given dictionary to a Sac-SMA init config object, if this can be done validly.

        Parameters
        ----------
        serialized_form
            A presumed serialized dictionary representing a Sac-SMA init config object.

        Returns
        -------
        A valid, deserialized Sac-SMA init config object.

        Raises
        ------
        ValueError
            Raised if the argument is either not structured properly or does not contain appropriate values to
            deserialize to a valid Sac-SMA init config object.
        """
        try:
            params: SERIALIZABLE_AS_DICT = serialized_form["params"]
            # Since the only thing within 'controls' is "SAC_CONTROL", just use that directly
            controls: SERIALIZABLE_AS_DICT = serialized_form["settings"][self.control_section_key()]

            if params["hru_id"] != controls["main_id"]:
                raise ValueError("Invalid Sac-SMA serialized init config: catchment id in params and namelist portions "
                                 "do not match")
            if controls["n_hrus"] != 1:
                raise ValueError("Invalid Sac-SMA serialized init config: only n_hrus values of 1 currently supported")

            def parse_optional_path(path_str: str) -> Optional[Path]:
                return None if path_str == "" else Path(path_str)

            config = SacSmaInitConfig(
                catchment_id=controls["main_id"],
                # Skipping n_hrus since that should always be 1
                forcing_root=Path(controls["forcing_root"]),
                output_root=parse_optional_path(controls["output_root"]),
                output_hrus=bool(controls["output_hrus"]),
                start_datehr=datetime.strptime(str(controls["start_datehr"]), SacSmaFileFormatSerializer.SERIAL_DATETIME_PATTERN),
                end_datehr=datetime.strptime(str(controls["end_datehr"]), SacSmaFileFormatSerializer.SERIAL_DATETIME_PATTERN),
                model_timestep=int(controls["model_timestep"]),
                warm_start_run=bool(controls["warm_start_run"]),
                write_states=bool(controls["write_states"]),
                state_in_root=parse_optional_path(controls["sac_state_in_root"]),
                state_out_root=parse_optional_path(controls["sac_state_out_root"]),

                catchment_area=params["hru_area"],
                uztwm=params["uztwm"],
                uzfwm=params["uzfwm"],
                lztwm=params["lztwm"],
                lzfpm=params["lzfpm"],
                lzfsm=params["lzfsm"],
                adimp=params["adimp"],
                uzk=params["uzk"],
                lzpk=params["lzpk"],
                lzsk=params["lzsk"],
                zperc=params["zperc"],
                rexp=params["rexp"],
                pctim=params["pctim"],
                pfree=params["pfree"],
                riva=params["riva"],
                side=params["side"],
                rserv=params["rserv"]
            )
        except KeyError as e:
            raise ValueError(f"Invalid Sac-SMA serialized init config: missing required key '{e.args[0]}'") from e

        try:
            self._validator.validate_types(config)
            self._validator.validate_values(config)
            return config
        except Validator.ValidationValueError as e:
            raise Validator.ValidationValueError(
                f"Unable to convert serialized dictionary to {config.__class__.__name__} due to validation errors"
            ) from e


class SacSmaFileFormatSerializer(Serializer[SacSmaInitConfig, SERIALIZABLE_AS_DICT]):
    """
    Serializer of Sac-SMA init config objects that converts them to JSON dictionaries mirroring the arrangement of data
    used in the namelist and params files loaded by the module itself.
    """

    SERIAL_DATETIME_PATTERN = "%Y%m%d%H"

    def serialize(self, serializable: SacSmaInitConfig) -> SERIALIZABLE_AS_DICT:
        """
        Serialize the given Sac-SMA init config object to a serialized dictionary that mirrors the arrangement of data
        used in the namelist and params files loaded by the module itself.

        Parameters
        ----------
        serializable
            A Sac-SMA init config object.

        Returns
        -------
        The serialized dictionary representing the given Sac-SMA init config object.
        """

        def serialize_optional_path(path: Optional[Path]) -> str:
            """ Serialize a path to a string, and a ``None`` value to an empty string. """
            return "" if path is None else str(path)

        settings = {
            SacSmaFileFormatDeserializer.control_section_key(): {
                "main_id": serializable.main_id,
                "n_hrus": serializable.n_hrus,
                "forcing_root": str(serializable.forcing_root),
                "output_root": serialize_optional_path(serializable.output_root),
                ### NOTE: In the written files, param file path goes after the output root
                ### NOTE: But that's a concern for the to-files serializer
                # Bools are convert to 0/1
                "output_hrus": int(serializable.output_hrus),
                "start_datehr": int(serializable.start_datehr.strftime(self.SERIAL_DATETIME_PATTERN)),
                "end_datehr": int(serializable.end_datehr.strftime(self.SERIAL_DATETIME_PATTERN)),
                "model_timestep": serializable.model_timestep,
                # Bools are convert to 0/1
                "warm_start_run": int(serializable.warm_start_run),
                "write_states": int(serializable.write_states),
                "sac_state_in_root": serialize_optional_path(serializable.state_in_root),
                "sac_state_out_root": serialize_optional_path(serializable.state_out_root)
            }
        }

        params = {
            "hru_id": serializable.hru_id,
            "hru_area": serializable.hru_area,
            "uztwm": serializable.uztwm,
            "uzfwm": serializable.uzfwm,
            "lztwm": serializable.lztwm,
            "lzfpm": serializable.lzfpm,
            "lzfsm": serializable.lzfsm,
            "adimp": serializable.adimp,
            "uzk": serializable.uzk,
            "lzpk": serializable.lzpk,
            "lzsk": serializable.lzsk,
            "zperc": serializable.zperc,
            "rexp": serializable.rexp,
            "pctim": serializable.pctim,
            "pfree": serializable.pfree,
            "riva": serializable.riva,
            "side": serializable.side,
            "rserv": serializable.rserv
        }

        return {"settings": settings, "params": params}


class SacSmaFilesDeserializer(Deserializer[SacSmaInitConfig, Tuple[Path, Path]]):
    """
    Deserializer for Sac-SMA init config objects from params and namelist files, as used when running Sac-SMA.

    Note that this type leverages ::class:`SacSmaFileFormatDeserializer`.  As such, this type also validate deserialized
    objects before returning them, using ::class:`SimpleSacSmaValidator`.

    Note also that this type has an init param to control whether, when running :meth:`deserialize`, the provided params
    file path must resolve to the same path as configured in the namelist file (after deserializing the path string to a
    ::class:`Path` and calling ::method:`Path.resolve`).  The reason for this is that some false failures are possible
    depending on relative paths used and the current directory, so strict checking would often be problematic, but it
    may also be useful in some cases.
    """

    slots = ["_validator", "_stricter_params_file_check"]

    def __init__(self, validator: Optional[Validator[SacSmaInitConfig]] = None, strict_params_file_check: bool = False):
        """
        Initialize.

        Parameters
        ----------
        validator
            Optional validator to use to validate before returning deserialized objects; if ``None`` (the default), a
            ::class:`SacSmaSimpleValidator` instance is created and used.
        strict_params_file_check
            Whether, when running :meth:`deserialize`, the provided params file path must resolve to the same path
            (after calling ``resolve()``) contained within the namelist file; some false failures are possible depending
            on relative paths used and the current directory, so the default is ``False``.
        """
        self._validator = validator if validator is not None else SacSmaSimpleValidator()
        self._stricter_params_file_check = strict_params_file_check

    def deserialize(self, serialized_form: Tuple[Path, Path]) -> SacSmaInitConfig:
        """
        Deserialize a Sac-SMA init config object from the given namelist and params files.

        Function must account for a few things particular to the formats of the files themselves:
            - The utilized function for reading the namelist converts keys to lower case, but the convention is for
              top-level control section key to always be in upper case, so the function converts back to upper case.
            - The utilized function for reading the params file reads all values as strings; this function coverts
              numeric values back to floats.
            - Removing the params file path from the controls dict, since that's part of the init config object itself
              (merely an artifact of this serialization/deserialization variation).

        Parameters
        ----------
        serialized_form
            A tuple consisting of the path to the namelist file and the path to the params file.

        Returns
        -------
        The deserialized Sac-SMA init config object.
        """
        namelist_file, params_file = serialized_form

        controls_dict = from_namelist_str(namelist_file.read_text())
        params_dict = from_param_txt_str(params_file.read_text())

        controls_section_key = SacSmaFileFormatDeserializer.control_section_key()

        # controls_dict top-level control section key needs to be moved to upper case for consistency with everywhere else
        if controls_section_key.lower() in controls_dict:
            controls_dict[controls_section_key] = controls_dict.pop(controls_section_key.lower())

        if controls_section_key not in controls_dict:
            raise KeyError(f"Invalid Sac-SMA namelist file: missing required top-level '{controls_section_key}'/"
                           f"'{controls_section_key.lower()}' key")

        # Everything inside of "params" will be a string; need to coerce to floats
        for key, val in params_dict.items():
            # Although skip this
            if key == "hru_id":
                continue
            try:
                params_dict[key] = float(val)
            except ValueError as e:
                raise ValueError(f"Invalid Sac-SMA params file: value for key '{key}' is not a valid float") from e

        # controls_dict will have sac_param_file, though this should be removed at this stage
        try:
            config_params_file_str = controls_dict[controls_section_key].pop("sac_param_file")
        except KeyError as e:
            raise ValueError(f"Invalid Sac-SMA namelist file: missing required key '{e.args[0]}'") from e
        except IndexError as e:
            raise ValueError(f"Invalid Sac-SMA namelist file: wasn't configured with a params file path") from e

        # TODO: (later) might want to look at doing this differently
        if self._stricter_params_file_check and Path(config_params_file_str).resolve() != params_file.resolve():
            raise ValueError(f"Invalid Sac-SMA namelist file: configured/serialized params file "
                             f"'{config_params_file_str}' does not match params file '{params_file}' provided within "
                             f" deserialization arguments.")

        initial_deserializer = SacSmaFileFormatDeserializer(validator=self._validator)
        return initial_deserializer.deserialize({"settings": controls_dict, "params": params_dict})


class SacSmaFilesSerializer(Serializer[SacSmaInitConfig, Tuple[Path, Path]]):
    """
    Serializer for Sac-SMA init config objects to params and namelist files, as used when running Sac-SMA.
    """

    __slots__ = ["_namelist_file_path", "_params_file_path"]

    def __init__(self, namelist_file_path: Path, params_file_path: Path):
        self._namelist_file_path = namelist_file_path.resolve()
        self._params_file_path = params_file_path.resolve()

    def serialize(self, serializable: SacSmaInitConfig) -> Tuple[Path, Path]:
        """
        Serialize the given Sac-SMA init config object to a namelist and params file, as used in operations.

        Parameters
        ----------
        serializable
            The Sac-SMA init config object to serialize.

        Returns
        -------
        Paths to the namelist and params files respectively that were created and now contain a serialized form of the
        provided object.
        """
        initial_serializer = SacSmaFileFormatSerializer()
        serial_dict = initial_serializer.serialize(serializable)
        # Inject the path for the params config into the namelist config details
        control_section_key = SacSmaFileFormatDeserializer.control_section_key()
        serial_dict["settings"][control_section_key]["sac_param_file"] = str(self._params_file_path)

        namelist_str = to_namelist_str(serial_dict["settings"])
        params_str = to_param_txt_str(serial_dict["params"])

        self._namelist_file_path.write_text(namelist_str)
        self._params_file_path.write_text(params_str)

        return self._namelist_file_path, self._params_file_path


class HydrofabricSacSmaInitConfigGenerator(Deserializer[SacSmaInitConfig, HydrofabricCatchment]):

    __slots__ = ["_forcing_root", "_start", "_end", "_time_step_size", "_warm_start_run", "_write_states", "_validator"]

    def __init__(self, forcing_root: Path, start: datetime, end: datetime, time_step_size: int = 3600,
                 warm_start_run: bool = False, write_states: bool = False,
                 validator: Optional[Validator[SacSmaInitConfig]] = None):
        """
        Initialize, accepting certain general properties to insert into deserialized configs that are not in the
        hydrofabric, as well as optionally a specific validator.

        Parameters
        ----------
        forcing_root
            The root to forcing files for the module to directly use.
        start
            The start datetime value in insert into deserialized configs; note that while other more precise info can
            be included within the passed object, only the year, month, and day are used in the value inserted into
            deserialized config objects.
        end
            The end datetime value in insert into deserialized configs; note that while other more precise info can
            be included within the passed object, only the year, month, and day are used in the value inserted into
            deserialized config objects.
        time_step_size
            The model time step size to use when inserting into deserialized configs; by default, 3600.
        warm_start_run
            Warm start run flag to insert into deserialized configs; by default, ``False``.
        write_states
            Write states flag to insert into deserialized configs; by default, ``False``.
        validator
            An optional validator to use after creating deserialized configs; if ``None`` (the default), the default
            validator for the config instance will be used.
        """
        self._forcing_root = forcing_root
        self._start = start
        self._end = end
        self._time_step_size = time_step_size
        self._warm_start_run = warm_start_run
        self._write_states = write_states
        self._validator = validator

    def deserialize(self, serialized_form: HydrofabricCatchment) -> SacSmaInitConfig:
        config = SacSmaInitConfig(
            catchment_id=serialized_form.id,
            # Skipping n_hrus since that should always be 1
            forcing_root=self._forcing_root,
            output_root=None,
            start_datehr=datetime(year=self._start.year, month=self._start.month, day=self._start.day,
                                  hour=self._start.hour),
            end_datehr=datetime(year=self._end.year, month=self._end.month, day=self._end.day, hour=self._end.hour),
            model_timestep=self._time_step_size,
            warm_start_run=self._warm_start_run,
            write_states=self._write_states,
            state_in_root=None,
            state_out_root=None,
            **self.get_catchment_specific_params(catchment_data_object=serialized_form)
        )
        try:
            if self._validator is None:
                config.run_default_validation()
            else:
                config.accept_validator(self._validator)
            return config
        except Validator.ValidationValueError as e:
            raise Validator.ValidationValueError(
                f"{self.__class__.__name__} unable extract valid {config.__class__.__name__} due to validation errors"
            ) from e

    def get_catchment_specific_params(self, catchment_data_object: HydrofabricCatchment) -> dict[str, float]:
        """
        Get dict of catchment-specific params using in deserializing a config object from the given catchment data.

        Parameters
        ----------
        catchment_data_object
            Object containing catchment-specific data from the hydrofabric.

        Returns
        -------
        A dictionary catchment-specific params (keyed by param name) using in deserializing a config object from the
        given catchment data.

        See Also
        --------
        deserialize
        """
        # Seem to only be able to get hru_area/catchment_area for now; will have to use defaults for the rest
        return {"catchment_area": catchment_data_object.area}

