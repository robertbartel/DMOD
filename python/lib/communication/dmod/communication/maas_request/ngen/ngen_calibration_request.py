from dmod.core.serializable import Serializable
from dmod.core.meta_data import TimeRange
from enum import Enum
from typing import ClassVar, Dict, Literal, Optional, Type
from pydantic import Field

from ...message import AbstractInitRequest, MessageEventType
from ...maas_request import ModelExecRequestResponse
from .ngen_request import NGENRequest


class CalibrationParameterBounds(Serializable):
    min: float
    max: float
    initial: float


class Objective(str, Enum):
    custom = "custom"
    kling_gupta = "kling_gupta"
    nnse = "nnse"
    single_peak = "single_peak"
    volume = "volume"


class Algorithm(str, Enum):
    dds = "dds"
    pso = "pso"


class NgenStrategy(str, Enum):
    uniform = "uniform"
    explicit = "explicit"
    independent = "independent"


class NgenCalibrationRequest(NGENRequest):
    """
    An extension of ::class:`NGENRequest` for requesting ngen-cal calibration jobs.
    """

    event_type: ClassVar[MessageEventType] = MessageEventType.CALIBRATION_REQUEST
    model_name: ClassVar[str] = "ngen-cal"  # FIXME case sentitivity

    # TODO: probably will need to re-examine this
    _DEFAULT_CPU_COUNT: ClassVar[int] = 1
    """ The default number of CPUs to assume are being requested for the job, when not explicitly provided. """

    # NOTE: we should probably use `ngen.cal.strategy.Strategy` as this field type
    strategy_algorithm: Algorithm = Algorithm.dds

    # NOTE: we should probably use `ngen.cal.strategy.Objective` as this field type
    strategy_objective_function: Objective

    # NOTE: I think we can eliminate this field since we will likely have a different request type
    # for `sensitivity`
    strategy_type: Literal["estimation"] = "estimation"
    evaluation_time_range: TimeRange
    is_obj_func_min: bool = True
    is_restart: bool = False
    iterations: int = Field(gt=0)
    job_name: Optional[str]

    # NOTE: this could be `ngen.cal.parameter.Parameters` instead
    model_cal_params: Dict[str, CalibrationParameterBounds]

    # NOTE: we should probably use `ngen.cal.ngen.NgenStrategy` as this field type
    model_strategy: NgenStrategy = NgenStrategy.uniform

    @classmethod
    def factory_init_correct_response_subtype(cls, json_obj: dict) -> 'NgenCalibrationResponse':
        """
        Init a :obj:`Response` instance of the appropriate subtype for this class from the provided JSON object.

        Parameters
        ----------
        json_obj

        Returns
        -------
        CalibrationJobResponse
            A response of the correct type, with state details from the provided JSON.
        """
        return NgenCalibrationResponse.factory_init_from_deserialized_json(json_obj=json_obj)

    # TODO: may need to modify this to have (realization) config dataset start empty (at least optionally) and apply

    # TODO: This should likely be created or determined if it already exsits on the fly
    # @property
    # def data_requirements(self) -> List[DataRequirement]:
    #     """
    #     List of all the explicit and implied data requirements for this request, as needed fo    r creating a job object.

    #     Returns
    #     -------
    #     List[DataRequirement]
    #         List of all the explicit and implied data requirements for this request.
    #     """
    #     data_requirements = super().data_requirements
    #     return [self.calibration_cfg_data_requirement ,*data_requirements]


# TODO: aaraney. this looks unfinished
# class NgenCalibrationResponse(ExternalRequestResponse):
class NgenCalibrationResponse(ModelExecRequestResponse):

    response_to_type: ClassVar[Type[AbstractInitRequest]] = NgenCalibrationRequest
