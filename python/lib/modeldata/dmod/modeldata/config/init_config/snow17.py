from dataclasses import dataclass, fields
from datetime import datetime
from pathlib import Path
from types import NoneType
from typing import Optional, Self, Tuple

from dmod.core.serializable_v2 import (Deserializer, SERIALIZABLE_AS_DICT, Serializer, SimpleSerializable,
                                       Validator, Validated, Interval, IntervalStringSerializer, from_namelist_str,
                                       from_param_txt_str, to_namelist_str, to_param_txt_str)


@dataclass(slots=True)
class Snow17InitConfig(SimpleSerializable, Validated):
    """
    Representation of BMI init config for Snow17.

    Note that this type is designed to model (in a software design sense) a Snow17 config.  It contains the required
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
        Whether Snow17 module should output HRU results.
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
    latitude: float
        Centroid latitude of catchment/hru [decimal degrees].
    elev: float
        Mean elevation of catchment/hru [m].
    warm_start_run: bool
        Whether to start from a warm start file.
    write_states: bool
        Whether to write restart files for subsequent "warm start" runs.
    scf: float
        Snow Correction Factor.
    mfmax: float
        Max non-rain melt factor [mm/degrees C/hr].
    mfmin: float
        Min non-rain melt factor [mm/degrees C/hr].
    uadj: float
        Average wind function for rain on snow.
    si: float
        100% snow cover threshold [mm].
    pxtemp: float
        Precipitation vs Snow threshold temperature [degrees C].
    nmf: float
        Max negative melt factor [mm/degrees C/hr].
    tipm: float
        Antecedent snow temperature index.
    mbase: float
        Base Temperature for non-rain melt factor [(degrees C)].
    plwhc: float
        Percent liquid water holding capacity [%].
    daygm: float
        Daily ground melt [mm/day].
    adc1: float
        Areal depletion curve, WE/Ai=0.
    adc2: float
        Areal depletion curve, WE/Ai=0.1.
    adc3: float
        Areal depletion curve, WE/Ai=0.2.
    adc4: float
        Areal depletion curve, WE/Ai=0.3.
    adc5: float
        Areal depletion curve, WE/Ai=0.4.
    adc6: float
        Areal depletion curve, WE/Ai=0.5.
    adc7: float
        Areal depletion curve, WE/Ai=0.6.
    adc8: float
        Areal depletion curve, WE/Ai=0.7.
    adc9: float
        Areal depletion curve, WE/Ai=0.8.
    adc10: float
        Areal depletion curve, WE/Ai=0.9.
    adc11: float
        Areal depletion curve, WE/Ai=1.0.
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

    latitude: float
    elev: float

    model_timestep: int = 3600
    output_hrus: bool = False
    warm_start_run: bool = False
    write_states: bool = False

    scf: float = 1.1
    mfmax: float = 1.0
    mfmin: float = 0.2
    uadj: float = 0.05
    si: float = 500.0
    pxtemp: float = 1.0
    nmf: float = 0.15
    tipm: float = 0.1
    mbase: float = 0.0
    plwhc: float = 0.03
    daygm: float = 0.0
    adc1: float = 0.05
    adc2: float = 0.1
    adc3: float = 0.2
    adc4: float = 0.3
    adc5: float = 0.4
    adc6: float = 0.5
    adc7: float = 0.6
    adc8: float = 0.7
    adc9: float = 0.8
    adc10: float = 0.9
    adc11: float = 1.0

    @classmethod
    def get_default_deserializer_instance(cls) -> Deserializer[Self, SERIALIZABLE_AS_DICT]:
        return Snow17FileFormatDeserializer()

    def __post_init__(self, *args, **kwargs):
        self.start_datehr = datetime(year=self.start_datehr.year, month=self.start_datehr.month,
                                     day=self.start_datehr.day, hour=self.start_datehr.hour)
        self.end_datehr = datetime(year=self.end_datehr.year, month=self.end_datehr.month,
                                   day=self.end_datehr.day, hour=self.end_datehr.hour)

    def get_default_validator_instance(self) -> Validator[Self]:
        return Snow17SimpleValidator()

    def get_default_serializer_instance(self) -> Serializer[Self, SERIALIZABLE_AS_DICT]:
        return Snow17FileFormatSerializer()

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
        Property of an init config representing the number of HRUs/catchments it applies to, though constrained to
        always be ``1`` for this implementation.
        """
        return 1

    @property
    def main_id(self) -> str:
        """ Alias for catchment_id, used in certain contexts. """
        return self.catchment_id


class Snow17SimpleValidator(Validator[Snow17InitConfig]):
    """
    Simple validator for Snow17 init config objects.

    This type does not concern itself with whether any ::class:`Path` attribute values are reasonable (e.g., a file
    exists at the path, etc.).  It only validates that it is a path value.

    However, the logic for validating paths is organized in a dedicated function (::method:`validate_path_values`) that
    is called by the main validation function (::method:`validate_values`).  The base implementation of
    ::method:`validate_path_values` is a no-op, but it can be overridden in subclasses to customize the path validation
    logic, while not having to override/re-write the rest of the base class's value validation.
    """

    def validate_path_values(self, obj: Snow17InitConfig):
        """
        Separate function for path value validation portion of this types validation logic (no-op in this type).
        
        Default, no-op implementation of separate function called by ::method:`validate_values` to organize the logic of
        path attribute validation.  Subclasses may override this method to implement their own more robust path 
        validation and otherwise maintain the same value validation as this base class.

        Subtypes should keep in mind
        
        Parameters
        ----------
        obj
            The ::class:`Snow17InitConfig` object being validated.
        """
        pass

    def validate_types(self, obj: Snow17InitConfig):
        """
        Validate that all attributes of the object being validated are of the expected type.

        Parameters
        ----------
        obj
            The ::class:`Snow17InitConfig` object being validated.

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

    def validate_values(self, obj: Snow17InitConfig):
        """
        Validate attribute values for the given object are in acceptable ranges or are otherwise sane and valid.

        Parameters
        ----------
        obj
            The ::class:`Snow17InitConfig` object being validated.

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
            "latitude": {"min_val": 0.0, "max_val": 360.0, "max_is_open": True},
            "scf": {"min_val": 0.9, "max_val": 1.8},
            "mfmax": {"min_val": 0.1, "max_val": 2.2},
            "mfmin": {"min_val": 0.01, "max_val": 0.6},
            "uadj": {"min_val": 0.01, "max_val": 0.2},
            "si": {"min_val": 0, "max_val": 10000},
            "pxtemp": {"min_val": 0.5, "max_val": 5},
            "nmf": {"min_val": 0.01, "max_val": 0.3},
            "tipm": {"min_val": 0, "max_val": 1},
            "mbase": {"min_val": 0, "max_val": 0},
            "plwhc": {"min_val": 0.01, "max_val": 0.3},
            "daygm": {"min_val": 0, "max_val": 0.5},
            "adc1": {"min_val": 0.05, "max_val": 0.05},
            "adc2": {"min_val": 0.1, "max_val": 0.1},
            "adc3": {"min_val": 0.2, "max_val": 0.2},
            "adc4": {"min_val": 0.3, "max_val": 0.3},
            "adc5": {"min_val": 0.4, "max_val": 0.4},
            "adc6": {"min_val": 0.5, "max_val": 0.5},
            "adc7": {"min_val": 0.6, "max_val": 0.6},
            "adc8": {"min_val": 0.7, "max_val": 0.7},
            "adc9": {"min_val": 0.8, "max_val": 0.8},
            "adc10": {"min_val": 0.9, "max_val": 0.9},
            "adc11": {"min_val": 1.0, "max_val": 1.0},
        }

        for attr, attr_range in attr_intervals.items():
            val = getattr(obj, attr)
            interval = Interval.get_default_deserializer_instance().deserialize(attr_intervals.get(attr))
            if not interval.contains(val):
                raise Validator.ValidationValueError(
                    f"{self.__class__.__name__} requires attribute '{attr}' to be in range "
                    f"{IntervalStringSerializer().serialize(interval)} but received '{val!s}'."
                )


class Snow17FileFormatDeserializer(Deserializer[Snow17InitConfig, SERIALIZABLE_AS_DICT]):
    """
    Deserializer of Snow17 init config objects that converts them from JSON dictionaries mirroring the arrangement of
    data used in the namelist and params files loaded by the module itself.

    Note that this type does validate deserialized objects before returning them.
    """

    __slots__ = ["_validator",]

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
        return "SNOW17_CONTROL"

    def __init__(self, validator: Optional[Validator[Snow17InitConfig]] = None ):
        """
        Initialize.

        Parameters
        ----------
        validator
            Optional validator to use to validate before returning deserialized objects; if ``None`` (the default), a
            ::class:`Snow17SimpleValidator` instance is created and used.
        """
        self._validator = validator if validator is not None else Snow17SimpleValidator()

    def deserialize(self, serialized_form: SERIALIZABLE_AS_DICT) -> Snow17InitConfig:
        """
        Deserialize the given dictionary to an init config object, if this can be done validly.

        Parameters
        ----------
        serialized_form
            A presumed serialized dictionary representing an init config object.

        Returns
        -------
        A valid, deserialized Snow17 init config object.

        Raises
        ------
        ValueError
            Raised if the argument is either not structured properly or does not contain appropriate values to
            deserialize to a valid init config object.
        """
        try:
            params: SERIALIZABLE_AS_DICT = serialized_form["params"]
            # Since the only thing within 'controls' is "SNOW17_CONTROL", just use that directly
            controls: SERIALIZABLE_AS_DICT = serialized_form["settings"][self.control_section_key()]

            if params["hru_id"] != controls["main_id"]:
                raise ValueError(f"Invalid serialized config for {self.__class__.__name__}: catchment id in params and "
                                 f"namelist portions do not match")
            if controls["n_hrus"] != 1:
                raise ValueError(f"Invalid serialized config for {self.__class__.__name__}: only n_hrus values of 1 "
                                 f"currently supported")

            # Do some mods to this here (though work from copy) to make things easier a little later
            modified_params_copy = params.copy()
            modified_params_copy["catchment_area"] = modified_params_copy.pop("hru_area")
            del modified_params_copy["hru_id"]

            def parse_optional_path(path_str: str) -> Optional[Path]:
                return None if path_str == "" else Path(path_str)

            config = Snow17InitConfig(
                catchment_id=controls["main_id"],
                # Skipping n_hrus since that should always be 1
                forcing_root=Path(controls["forcing_root"]),
                output_root=parse_optional_path(controls["output_root"]),
                output_hrus=bool(controls["output_hrus"]),
                start_datehr=datetime.strptime(str(controls["start_datehr"]), Snow17FileFormatSerializer.SERIAL_DATETIME_PATTERN),
                end_datehr=datetime.strptime(str(controls["end_datehr"]), Snow17FileFormatSerializer.SERIAL_DATETIME_PATTERN),
                model_timestep=int(controls["model_timestep"]),
                warm_start_run=bool(controls["warm_start_run"]),
                write_states=bool(controls["write_states"]),
                state_in_root=parse_optional_path(controls["snow_state_in_root"]),
                state_out_root=parse_optional_path(controls["snow_state_out_root"]),
                # Use this that we prepared earlier for the params portion of the kwargs
                **modified_params_copy,                
            )
        except KeyError as e:
            raise ValueError(f"Invalid Snow17 serialized init config: missing required key '{e.args[0]}'") from e

        try:
            self._validator.validate_types(config)
            self._validator.validate_values(config)
            return config
        except Validator.ValidationValueError as e:
            raise Validator.ValidationValueError(
                f"Unable to convert serialized dictionary to {config.__class__.__name__} due to validation errors"
            ) from e


class Snow17FileFormatSerializer(Serializer[Snow17InitConfig, SERIALIZABLE_AS_DICT]):
    """
    Serializer of Snow17 init config objects that converts them to JSON dictionaries mirroring the arrangement of data
    used in the namelist and params files loaded by the module itself.
    """

    SERIAL_DATETIME_PATTERN = "%Y%m%d%H"

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
        return Snow17FileFormatDeserializer.control_section_key()

    def serialize(self, serializable: Snow17InitConfig) -> SERIALIZABLE_AS_DICT:
        """
        Serialize the given init config object to a serialized dictionary that mirrors the arrangement of data
        used in the namelist and params files loaded by the module itself.

        Parameters
        ----------
        serializable
            An init config object.

        Returns
        -------
        The serialized dictionary representing the given init config object.
        """

        def serialize_optional_path(path: Optional[Path]) -> str:
            """ Serialize a path to a string, and a ``None`` value to an empty string. """
            return "" if path is None else str(path)

        settings = {
            self.control_section_key(): {
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
                "snow_state_in_root": serialize_optional_path(serializable.state_in_root),
                "snow_state_out_root": serialize_optional_path(serializable.state_out_root)
            }
        }

        params = {
            "hru_id": serializable.hru_id,
            "hru_area": serializable.hru_area,
            "latitude": serializable.latitude,
            "elev": serializable.elev,
            "scf": serializable.scf,
            "mfmax": serializable.mfmax,
            "mfmin": serializable.mfmin,
            "uadj": serializable.uadj,
            "si": serializable.si,
            "pxtemp": serializable.pxtemp,
            "nmf": serializable.nmf,
            "tipm": serializable.tipm,
            "mbase": serializable.mbase,
            "plwhc": serializable.plwhc,
            "daygm": serializable.daygm,
            "adc1": serializable.adc1,
            "adc2": serializable.adc2,
            "adc3": serializable.adc3,
            "adc4": serializable.adc4,
            "adc5": serializable.adc5,
            "adc6": serializable.adc6,
            "adc7": serializable.adc7,
            "adc8": serializable.adc8,
            "adc9": serializable.adc9,
            "adc10": serializable.adc10,
            "adc11": serializable.adc11,
        }

        return {"settings": settings, "params": params}


class Snow17FilesDeserializer(Deserializer[Snow17InitConfig, Tuple[Path, Path]]):
    """
    Deserializer for Snow17 init config objects from params and namelist files, as used when running the module.

    Note that this type leverages ::class:`Snow17FileFormatDeserializer`.  As such, this type also validate deserialized
    objects before returning them, using ::class:`SimpleSnow17Validator`.

    Note also that this type has an init param to control whether, when running :meth:`deserialize`, the provided params
    file path must resolve to the same path as configured in the namelist file (after deserializing the path string to a
    ::class:`Path` and calling ::method:`Path.resolve`).  The reason for this is that some false failures are possible
    depending on relative paths used and the current directory, so strict checking would often be problematic, but it
    may also be useful in some cases.
    """

    __slots__ = ["_validator", "_stricter_params_file_check"]

    def __init__(self, validator: Optional[Validator[Snow17InitConfig]] = None, strict_params_file_check: bool = False):
        """
        Initialize.

        Parameters
        ----------
        validator
            Optional validator to use to validate before returning deserialized objects; if ``None`` (the default), a
            ::class:`Snow17SimpleValidator` instance is created and used.
        strict_params_file_check
            Whether, when running :meth:`deserialize`, the provided params file path must resolve to the same path
            (after calling ``resolve()``) contained within the namelist file; some false failures are possible depending
            on relative paths used and the current directory, so the default is ``False``.
        """
        self._validator = validator if validator is not None else Snow17SimpleValidator()
        self._stricter_params_file_check = strict_params_file_check

    def deserialize(self, serialized_form: Tuple[Path, Path]) -> Snow17InitConfig:
        """
        Deserialize an init config object from the given namelist and params files.

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
        The deserialized init config object.
        """
        namelist_file, params_file = serialized_form

        controls_dict = from_namelist_str(namelist_file.read_text())
        params_dict = from_param_txt_str(params_file.read_text())

        control_section_key = Snow17FileFormatDeserializer.control_section_key()

        # controls_dict top-level control section key needs to be moved to upper case for consistency with everywhere else
        if control_section_key.lower() in controls_dict:
            controls_dict[control_section_key] = controls_dict.pop(control_section_key.lower())

        if control_section_key not in controls_dict:
            raise KeyError(f"Invalid namelist file for {self.__class__.__name__}: missing required top-level "
                           f"'{control_section_key}'/'{control_section_key.lower()}' key")


        # Everything inside of "params" will be a string; need to coerce everything but hru_id to floats
        try:
            hru_id = params_dict.pop("hru_id")
            params_dict = {key: float(val) for key, val in params_dict.items()}
            params_dict["hru_id"] = hru_id
        except KeyError as e:
            raise KeyError(f"Invalid {self.__class__.__name__} namelist: missing expected key '{e.args[0]}'") from e
        except ValueError as e:
            raise ValueError(f"{self.__class__.__name__} had {e.__class__.__name__} coercing values to floats") from e

        # controls_dict will have snow17_param_file, though this should be removed at this stage
        try:
            config_params_file_str = controls_dict[control_section_key].pop("snow17_param_file")
        except KeyError as e:
            raise ValueError(f"Invalid {self.__class__.__name__} namelist: missing required key '{e.args[0]}'") from e
        except IndexError as e:
            raise ValueError(f"Invalid {self.__class__.__name__} namelist: missing params file path") from e

        # TODO: (later) might want to look at doing this differently
        if self._stricter_params_file_check and Path(config_params_file_str).resolve() != params_file.resolve():
            raise ValueError(f"Invalid {self.__class__.__name__} namelist: configured/serialized params file "
                             f"'{config_params_file_str}' does not match params file '{params_file}' provided within "
                             f" deserialization arguments.")

        initial_deserializer = Snow17FileFormatDeserializer(validator=self._validator)
        return initial_deserializer.deserialize({"settings": controls_dict, "params": params_dict})


class Snow17FilesSerializer(Serializer[Snow17InitConfig, Tuple[Path, Path]]):
    """
    Serializer for Snow17 init config objects to params and namelist files, as used when running Snow17.
    """

    __slots__ = ["_namelist_file_path", "_params_file_path"]

    def __init__(self, namelist_file_path: Path, params_file_path: Path):
        self._namelist_file_path = namelist_file_path.resolve()
        self._params_file_path = params_file_path.resolve()

    def serialize(self, serializable: Snow17InitConfig) -> Tuple[Path, Path]:
        """
        Serialize the given init config object to a namelist and params file, as used in operations.

        Parameters
        ----------
        serializable
            The init config object to serialize.

        Returns
        -------
        Paths to the namelist and params files respectively that were created and now contain a serialized form of the
        provided object.
        """
        initial_serializer = Snow17FileFormatSerializer()
        serial_dict = initial_serializer.serialize(serializable)
        # Inject the path for the params config into the namelist config details
        serial_dict["settings"][initial_serializer.control_section_key()]["snow17_param_file"] = str(self._params_file_path)

        namelist_str = to_namelist_str(serial_dict["settings"])
        params_str = to_param_txt_str(serial_dict["params"])

        self._namelist_file_path.write_text(namelist_str)
        self._params_file_path.write_text(params_str)

        return self._namelist_file_path, self._params_file_path
