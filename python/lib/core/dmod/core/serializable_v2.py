from __future__ import annotations

import dataclasses
import json
from abc import ABC, abstractmethod
from collections import OrderedDict
from configparser import ConfigParser
from io import StringIO
from typing import Dict, Generic, List, Type, TypeVar, Union

from typing_extensions import Self, TypeAlias

from .common.helper_functions import attempt_import

_SERIALIZABLE_JSON_PRIMITIVES: TypeAlias = Union[str, float, int, bool]
SERIALIZABLE_AS_DICT: TypeAlias = Dict[
    str,
    Union[
        _SERIALIZABLE_JSON_PRIMITIVES,
        "SERIALIZABLE_AS_DICT",
        List[_SERIALIZABLE_JSON_PRIMITIVES],
        List["SERIALIZABLE_AS_DICT"],
    ],
]
"""Dictionary, keyed by strings, of non-None json serializable types."""


A = TypeVar("A")
""" Unbounded generic type variable for type that may be converted. """
T = TypeVar("T", bound="SimpleSerializable")
""" Bounded generic type variable for types that can be serialized. """
O = TypeVar("O")
""" Unbounded generic type variable for type that may be the result of convertion/serialization. """


def to_ini_str(serializable_as_dict: SERIALIZABLE_AS_DICT,
               include_section_header: bool = True,
               space_around_delimiters: bool = True,
               preserve_key_case: bool = False) -> str:
    """
    Transform a serialized dictionary to an ini formatted string.

    Parameters
    ----------
    serializable_as_dict
        A serialized dictionary representation of a ::class:`Serializable_V1` object (or, strictly speaking, a ``dict``
        adhering to the required key and value typing criteria for such serialized representations).
    include_section_header
        Whether to include an INI section header in the transformed output string (default: ``True``).
    space_around_delimiters
        Whether to include spaces around `=` delimiters (default: ``True``).
    preserve_key_case
        Whether to preserve case of keys (default: ``False``).
    """
    cp = ConfigParser(interpolation=None)
    if preserve_key_case:
        cp.optionxform = str

    if include_section_header:
        cp.read_dict(serializable_as_dict)
    else:
        cp.read_dict({"_NO_SECTION": serializable_as_dict})

    s: StringIO
    with StringIO() as s:
        cp.write(s, space_around_delimiters=space_around_delimiters)
        transformed_str = s.getvalue()
        # If set to not use section headers, remove the [NO_SECTION] header
        if not include_section_header:
            transformed_str = transformed_str[transformed_str.find("\n") + 1:]
        # Remove EOL configparser puts at end of the file
        return transformed_str.rstrip()


def from_ini_str(ini_str: str) -> SERIALIZABLE_AS_DICT:
    """
    Transform an ini string to a serialized dictionary.

    Parameters
    ----------
    ini_str
        The ini formated string to transform.

    Returns
    -------
    The serial dictionary representation of the ini formatted string.
    """
    cp = ConfigParser(interpolation=None)
    cp.read_string(ini_str)
    values = {section_name: dict(cp.items(section_name)) for section_name in cp.sections()}
    return values


def to_namelist_str(serializable_as_dict: SERIALIZABLE_AS_DICT) -> str:
    """
    Transform a serialized ::class:`Serializable_V1` to a namelist formatted string.

    Parameters
    ----------
    serializable_as_dict
        A serialized dictionary representation of a ::class:`Serializable_V1` object (or, strictly speaking, a ``dict``
        adhering to the required key and value typing criteria for such serialized representations).

    Returns
    -------
    The given dictionary transformed into a string suitable for writing to a namelist file.
    """
    # TODO: might need to make f90nml an extras (or at least need in dependencies)
    f90nml = attempt_import("f90nml")
    # While dicts are ordered in recent python, f90nml requires an OrderedDict
    namelist = f90nml.Namelist(OrderedDict(serializable_as_dict))
    # Cleanup EOL characters
    return str(namelist).rstrip()


def from_namelist_str(namelist_str: str, comment_tokens: List[str] = []) -> SERIALIZABLE_AS_DICT:
    """
    Transform a namelist formatted string to a dictionary.

    Parameters
    ----------
    namelist_str
        The namelist formated string to transform.
    comment_tokens
        List of tokens to set as comment tokens for the underlying f90nml parser (by default, an empty list).

    Returns
    -------
    Serialized dictionary representation of the namelist formatted string.
    """
    # TODO: might need to make f90nml an extras (or at least need in dependencies)
    f90nml = attempt_import("f90nml")
    parser = f90nml.Parser()
    data: f90nml.Namelist = parser.reads(namelist_str)
    return data.todict()


def to_yaml_str(serializable_as_dict: SERIALIZABLE_AS_DICT) -> str:
    """
    Transform a serialized ::class:`Serializable_V1` to a YAML formatted string.

    Parameters
    ----------
    serializable_as_dict
        A serialized dictionary representation of a ::class:`Serializable_V1` object (or, strictly speaking, a ``dict``
        adhering to the required key and value typing criteria for such serialized representations).

    Returns
    -------
    The given dictionary transformed into a string suitable for writing to a YAML file.
    """
    # TODO: might need to make yaml/pyyaml an extras (or at least need in dependencies)
    yaml = attempt_import("yaml")

    # See https://github.com/yaml/pyyaml/issues/234 and https://github.com/yaml/pyyaml/issues/234#issuecomment-765894586
    class Dumper(yaml.Dumper):
        def increase_indent(self, flow: bool = False, *args, **kwargs):
            # this resolves how lists are indented. without this, they are indented inline with keys
            return super().increase_indent(flow=flow, indentless=False)

    # Remove EOL
    return yaml.dump(serializable_as_dict, Dumper=Dumper).rstrip()


def from_yaml_str(yaml_str: str) -> SERIALIZABLE_AS_DICT:
    yaml = attempt_import("yaml")
    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader

    return yaml.load(yaml_str, Loader=Loader)


def to_toml_str(serializable_as_dict: SERIALIZABLE_AS_DICT) -> str:
    """
    Transform a serialized ::class:`Serializable_V1` to a TOML formatted string.

    Parameters
    ----------
    serializable_as_dict
        A serialized dictionary representation of a ::class:`Serializable_V1` object (or, strictly speaking, a ``dict``
        adhering to the required key and value typing criteria for such serialized representations).

    Returns
    -------
    The given dictionary transformed into a string suitable for writing to a TOML file.
    """
    # TODO: might need to make toml an extras (or at least need in dependencies)
    tomli_w = attempt_import("tomli_w")
    return tomli_w.dumps(serializable_as_dict).rstrip()


def from_toml_str(toml_str: str) -> SERIALIZABLE_AS_DICT:
    tomli = attempt_import("tomli")
    return tomli.loads(toml_str)


def to_param_txt_str(serializable_as_dict: SERIALIZABLE_AS_DICT):
    """
    Transform a serialized ::class:`Serializable_V1` to a simple key-value params formatted string.

    Transform the given dictionary into a string suitable for writing to simple key-value, space-delimited format
    suitable for certain types of params configuration files.

    Parameters
    ----------
    serializable_as_dict
        A serialized dictionary representation of a ::class:`Serializable_V1` object (or, strictly speaking, a ``dict``
        adhering to the required key and value typing criteria for such serialized representations).

    Returns
    -------
    The given dictionary transformed into a string suitable for writing to simple key-value params file.
    """

    """ Serialize to a simple key-value format that is space delimited. """
    cp = ConfigParser(interpolation=None, delimiters=tuple(" "))
    #if preserve_key_case:
    #    cp.optionxform = str
    data = {"_NO_SECTION": serializable_as_dict}
    cp.read_dict(data)
    s: StringIO
    with StringIO() as s:
        cp.write(s, space_around_delimiters=False)
        transformed_str = s.getvalue()
        return transformed_str[transformed_str.find("\n") + 1 :].rstrip()


def from_param_txt_str(ini_str: str) -> SERIALIZABLE_AS_DICT:
    """
    Deserialize to a dictionary from a simple key-value format that is space delimited.

    Parameters
    ----------
    ini_str
        The simple key-value param string.

    Returns
    -------
    The deserialized dictionary representation.
    """
    """  """
    cp = ConfigParser(interpolation=None, delimiters=tuple(" "))
    cp.read_string(f"[{"_NO_SECTION"}]\n" + ini_str)

    # only NO_SECTIONS should be present
    assert len(cp.sections()) == 1

    return dict(cp.items("_NO_SECTION"))



class Serializer(Generic[T, O], ABC):
    """
    Abstract type to apply specialized serialization to ::class:`T` objects, transforming them into ::class:`O` objects.

    An abstraction to support decoupling of serialization from the specific implementation of ::class:`T` when needed.
    While such types support their own serialization and deserialization, the specific format may not be appropriate
    or sufficient for all situations.  For example, a configuration object may be a unified concept but written to
    multiple files.  Such files could be represented by distinct objects, but doing so only because the underlying
    entity is saved this way unnecessarily couples the design for the object to the specific serialization format.

    In the base definition, ::class:`O` is expected to be something that makes sense for serialization and
    deserialization, like ``str`` or ::class:`Path` or JSON objects, but subtype implementations are free to determine
    what that is.
    """

    @abstractmethod
    def serialize(self, serializable: T) -> O:
        """
        Apply the specialized serialization to the provided ::class:`T` instance.

        Parameters
        ----------
        serializable
            The instance to serialize.

        Returns
        -------
        The serialized string representation of the instance.

        Raises
        ------
        TypeError
            Raised if the provided instance is not a support type.
        """
        pass


class Deserializer(Generic[T, O], ABC):
    """
    Abstract type to apply custom deserialization to ::class:`T` objects.

    An abstraction to support decoupling of deserialization from the specific implementation of ::class:`T` when needed.
    While such types support their own serialization and deserialization, the specific format may not be appropriate
    or sufficient for all situations.  For example, a configuration object may be a unified concept but written to
    multiple files.  Such files could be represented by distinct objects, but doing so only because the underlying
    entity is saved this way unnecessarily couples the design for the object to the specific serialization format.

    In the base definition, ::class:`O` is expected to be something that makes sense for serialization and
    deserialization, like ``str`` or ::class:`Path` or JSON objects, but subtype implementations are free to determine
    what that is.
    """

    @abstractmethod
    def deserialize(self, serialized_form: O) -> T:
        """
        Apply the custom deserialization to the provided serialized ::class:`O` representation of a ::class:`T`.

        Parameters
        ----------
        serialized_form
            The serialized representation of the instance to deserialize.

        Returns
        -------
        The deserialized ::class:`T` instance.

        Raises
        ------
        ValueError
            Raised if the provided ::class:`O` object is not a valid serialized representation of a ::class:`T`.
        """
        pass


class Validator(Generic[T], ABC):
    """
    Abstraction for type responsible for validating generically defined ::class:`T` objects.

    Abstract type that allows for decoupling validation implementations from the code of a ::class:`T`, allowing
    flexibility for distinct situations requiring different variations of validation implementations for a single
    subclass of ::class:`T`.

    For example, a configuration object may include attributes that reference file or directory paths.  In some
    situations, it may be appropriate to check whether the such a path exists, while in others it may be necessary to
    skip this (e.g., the config is intended for use in a different environment).  In yet other situations, it may be
    necessary to validate that the path exists and can be read from or written to by a particular user.  By decoupling
    validation into its own type, multiple varieties can be created to support subtly different validations needs in
    these kinds of scenarios.
    """

    class ValidationTypeError(TypeError):
        """
        Convenience extension of :class:`TypeError` during validation errors.
        """

    class ValidationValueError(ValueError):
        """
        Convenience extension of :class:`ValueError` during validation errors.
        """

    @abstractmethod
    def validate_types(self, obj: T):
        """
        Validate that all attributes of the object being validated are of the expected type.

        Parameters
        ----------
        obj
            The ::class:`T` object being validated.

        Raises
        -------
        TypeError
            If any attribute value is not of the expected type.
        """
        pass

    @abstractmethod
    def validate_values(self, obj: T):
        """
        Validate attribute values for the given object are in acceptable ranges or are otherwise sane and valid.

        Parameters
        ----------
        obj
            The ::class:`T` object being validated.

        Raises
        -------
        ValueError
            Raised if any of the "params" specific attributes are out of its acceptable range.
        """
        pass


class SimpleSerializable(ABC):
    """
    Abstract type that can be serialized, deserialized, and validated, with default members for those operations.

    Abstract type supporting serialization, deserialization, and validation, where these operations are performed by
    separate ::class:`Serializer`, ::class:`Deserializer`, and ::class:`Validator` objects.  However, subtypes are
    aware of and can utilize default instances of these types to perform such operations independently, just via
    composition.  Subtypes can also accept visiting ::class:`Serializer` and ::class:`Validator` objects for specialized
    variations of those operations.
    """

    DEFAULT_SERIAL_DATETIME_STR_FORMAT = '%Y-%m-%d %H:%M:%S'
    """ A default datetime format pattern string. """

    @classmethod
    def factory_init_from_deserialized_json(cls, json_obj: SERIALIZABLE_AS_DICT):
        """
        Factory create a new instance of this type based on a JSON object dictionary deserialized from received JSON.

        Parameters
        ----------
        json_obj

        Returns
        -------
        A new object of this type instantiated from the deserialize JSON object dictionary
        """
        return cls.get_default_deserializer_instance().deserialize(json_obj)

    @classmethod
    @abstractmethod
    def get_default_deserializer_instance(cls) -> Deserializer[Self, SERIALIZABLE_AS_DICT]:
        """
        Get an instance of the default deserializer for this type.

        Returns
        -------
        An instance of the default deserializer for this type.
        """
        pass

    def accept_serializer(self, serializer: Serializer[Self, O]) -> O:
        """
        Perform specialized serialization of this instance using the provided serializer.

        Parameters
        ----------
        serializer
            A serializer object used to apply specialized serialization this instance.

        Returns
        -------
        The serialized representation of this instance, in the specialized format.
        """
        return serializer.serialize(self)

    @abstractmethod
    def get_default_serializer_instance(self) -> Serializer[Self, SERIALIZABLE_AS_DICT]:
        """
        Get an instance of the default serializer for this type.

        Returns
        -------
        An instance of the default serializer for this type.
        """
        pass

    def to_dict(self) -> SERIALIZABLE_AS_DICT:
        """
        Get the representation of this instance as a serialized dictionary or dictionary-like object (e.g., a JSON
        object).

        Returns
        -------
        The representation of this instance as a serialized dictionary or dictionary-like object, with valid types of
        keys and values.
        """
        return self.accept_serializer(self.get_default_serializer_instance())

    def __str__(self):
        return str(self.to_json_str())

    def to_json_str(self, sort_keys: bool = True) -> str:
        """
        Get the representation of this instance as a serialized JSON-formatted string.

        Parameters
        ----------
        sort_keys
            The value to use for the argument of the same name when calling the :method:`json.dumps` method (defaults to
             ``True``).

        Returns
        -------
        json_string
            the serialized JSON string representation of this instance
        """
        return json.dumps(self.to_dict(), sort_keys=sort_keys)


class Validated(ABC):
    """
    Abstract type that can be validated, with default members for those operations.

    Abstract type supporting validation, where this operation is performed by separate ::class:`Validator` objects.
    These are accepted as visiting objects via the :meth:`accept_validator` method.

    However, subtypes are aware of and can utilize default validator instances to perform a baseline validation
    independently.
    """

    @abstractmethod
    def get_default_validator_instance(self) -> Validator[Self]:
        """
        Get an instance of the default validator for this type.

        Returns
        -------
        An instance of the default validator for this type.
        """
        pass

    def accept_validator(self, validator: Validator[Self]):
        """
        Perform specialized validation of this instance using the provided validator.

        Note that this calls both ::meth:`validate_types` and :meth:`validate_values` on the provided validator.

        Parameters
        ----------
        validator
            Object to perform validation on this instance.

        Returns
        -------
        Whether the types and values of this instance are valid according to the provided validator.
        """
        validator.validate_types(self)
        validator.validate_values(self)

    def run_default_validation(self):
        """
        Execute validation on this instance using its default validator.

        See Also
        --------
        get_default_validator_instance
        """
        self.accept_validator(self.get_default_validator_instance())


# TODO: (later) this might belong somewhere else
@dataclasses.dataclass
class Interval(SimpleSerializable):
    """ Helper class for defining a numeric interval and testing if a value is within it. """
    min_val: Union[int, float]
    max_val: Union[int, float]
    min_is_open: bool = False
    max_is_open: bool = False

    def __post_init__(self):

        if self.min_val == self.max_val and (self.min_is_open or self.max_is_open):
            raise ValueError(f"Invalid to create {self.__class__.__name__} with the two equal endpoints "
                             f"unless both endpoints are closed.")
        if self.min_val > self.max_val:
            raise ValueError(f"Can't create {self.__class__.__name__} with min endpoint '{self.min_val!s}' that is "
                             f"greater than max endpoint '{self.max_val!s}'")

    def contains(self, value: Union[int, float]) -> bool:
        """ Test if the given value is contained by the interval. """
        # Implication here, based on post_init validation, is that both endpoints are closed, so check the value
        if self.min_val == self.max_val:
            return value == self.min_val
        meets_min = value > self.min_val if self.min_is_open else value >= self.min_val
        meets_max = value < self.max_val if self.max_is_open else value <= self.max_val
        return meets_min and meets_max

    @classmethod
    def get_default_deserializer_instance(cls) -> Deserializer[Self, SERIALIZABLE_AS_DICT]:
        return IntervalDictSerDes()

    def get_default_serializer_instance(self) -> Serializer[Self, SERIALIZABLE_AS_DICT]:
        return IntervalDictSerDes()


class IntervalDictSerDes(Serializer[Interval, dict[str, Union[int, float]]],
                         Deserializer[Interval, dict[str, Union[int, float]]]):
    """ Serializer/Deserializer for Interval objects to dictionaries. """
    def serialize(self, interval: Interval) -> dict[str, Union[int, float]]:
        return dataclasses.asdict(interval)

    def deserialize(self, serialized_interval: dict[str, Union[int, float]]) -> Interval:
        return Interval(**serialized_interval)


class IntervalStringSerializer(Serializer[Interval, str]):
    """ Type encapsulating serializing an interval to a string using standard math notation."""
    def serialize(self, interval: Interval) -> str:
        begin = f"({interval.min_val}" if interval.min_is_open else f"[{interval.min_val}"
        end = f"{interval.max_val})" if interval.max_is_open else f"{interval.max_val}]"
        return f"{begin},{end}"
