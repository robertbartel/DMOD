import json
import re

from dmod.core.meta_data import DataDomain, DataFormat, DiscreteRestriction, StandardDatasetIndex, TimeRange
from dmod.core.common.reader import ReadSeeker
from dmod.core.exception import DmodRuntimeError
from dmod.core.data_domain_detectors import DataItem, ItemDataDomainDetector
from pandas import read_csv as pandas_read_csv
import ngen.config.realization

from typing import Optional
from io import BytesIO

from ..hydrofabric.geopackage_hydrofabric import GeoPackageHydrofabric


class AorcCsvFileDomainDetector(ItemDataDomainDetector):
    """
    Subclass for detecting domains of NextGen regridded per-catchment AORC forcing CSV files.

    Instances must be explicitly or implicitly provided an item name along with the item.  Receiving a :class:`Path`
    object implicitly satisfies this, with the object's ``name`` property used.  This is required because the applicable
    catchment for data is not within the data itself; the convention is to include the catchment id as part of the file
    name.
    """

    _data_format = DataFormat.AORC_CSV
    _datetime_format: str = "%Y-%m-%d %H:%M:%S"

    def __init__(self, *, item: DataItem, item_name: Optional[str] = None, decode_format: str = 'utf-8'):
        """
        Initialize an instance.

        Parameters
        ----------
        item: DataItem
            The data item for which a domain will be detected.
        item_name: Optional[str]
            The name for the item, which includes important domain metadata in some situations.
        decode_format: str
            The decoder format when decoding byte strings (``utf-8`` by default).
        """
        super().__init__(item=item, item_name=item_name, decode_format=decode_format)
        if self._item_name is None:
            raise DmodRuntimeError(f"{self.__class__.__name__} must be passed an item name on init unless item is file")
        self._num_time_steps = None

    def _get_catchment_id(self) -> str:
        matches = re.match('^.*(cat)[_-](\d+)\D?.*$', self._item_name)
        if matches:
            return f"{matches.group(1)}-{matches.group(2)}"
        else:
            raise DmodRuntimeError(f"{self.__class__.__name__} couldn't parse cat id from name '{self._item_name}'")

    def _get_cat_restriction(self) -> DiscreteRestriction:
        """ Get :class:`DiscreteRestriction` defining applicable catchments (i.e., catchment) for the domain. """
        return DiscreteRestriction(variable=StandardDatasetIndex.CATCHMENT_ID, values=[self._get_catchment_id()])

    def detect(self, **kwargs) -> DataDomain:
        """
        Detect and return the data domain.

        Parameters
        ----------
        kwargs
            Optional kwargs applicable to the subtype, which may enhance or add to the domain detection and generation
            capabilities, but which should not be required to produce a valid domain.

        Returns
        -------
        DataDomain
            The detected domain.

        Raises
        ------
        DmodRuntimeError
            If it was not possible to properly detect the domain.
        """

        # Do this early to fail here rather than try to load the dataframe
        cat_restriction = self._get_cat_restriction()
        data = BytesIO(self._item) if isinstance(self._item, bytes) else self._item
        dt_index = self.get_data_format().indices_to_fields()[StandardDatasetIndex.TIME]
        df = pandas_read_csv(data, parse_dates=[dt_index])
        if {col.lower() for col in df.columns} != {field.lower() for field in self.get_data_format().data_fields}:
            raise DmodRuntimeError(f"{self.__class__.__name__} could not detect; unexpected columns "
                                   f"{df.columns.values!s} in data for format {self.get_data_format().name} (expected "
                                   f"{[k for k in self.get_data_format().data_fields]})")
        self._num_time_steps = df.shape[0]
        date_range = TimeRange(begin=df.iloc[0][dt_index].to_pydatetime(), end=df.iloc[-1][dt_index].to_pydatetime())
        return DataDomain(data_format=self.get_data_format(), continuous_restrictions=[date_range],
                          discrete_restrictions=[cat_restriction])


# TODO: track and record hydrofabric ids and file names of what's out there so that we recognize known versions/regions


# TODO: might need to expand things in the future ... there are other geopackage formats (e.g., older NextGen
#  hydrofabric versions that used "id" instead of "divide_id") and maybe we need to account for that in detectors (and
#  in formats)
class GeoPackageHydrofabricDomainDetector(ItemDataDomainDetector):

    _data_format = DataFormat.NGEN_GEOPACKAGE_HYDROFABRIC_V2

    def detect(self, **kwargs) -> DataDomain:
        """
        Detect and return the data domain.

        Parameters
        ----------
        kwargs
            Optional kwargs applicable to the subtype, which may enhance or add to the domain detection and generation
            capabilities, but which should not be required to produce a valid domain.

        Keyword Args
        ------------
        version: str
            A version string for a constraint using the ``HYDROFABRIC_VERSION`` index.
        region: str
            A region string for a constraint using the ``HYDROFABRIC_REGION`` index; if provided, it will be converted
            to lower case and have any non-alphanumeric characters removed before use.

        Returns
        -------
        DataDomain
            The detected domain.

        Raises
        ------
        DmodRuntimeError
            If it was not possible to properly detect the domain.
        """
        # TODO: (later) probably isn't necessary to treat separately, but don't have a good way to test yet
        if isinstance(self._item, ReadSeeker):
            gpkg_data = self._item.read()
            self._item.seek(0)
        else:
            gpkg_data = self._item

        region = kwargs['region'].strip() if isinstance(kwargs.get('region'), str) else None

        # TODO: (later) at some point, account for model attributes data being present or not, and whether its valid
        try:
            factory_params = {"geopackage_file": gpkg_data}
            if region and region.lower() == "conus":
                factory_params["is_conus"] = True
            # TODO: (later) once GeoPackageHydrofabric for "vpu" to not just be int, account for that here
            hydrofabric = GeoPackageHydrofabric.from_file(**factory_params)
            d_restricts = [
                # Define range of catchment ids for catchment ids
                DiscreteRestriction(variable=StandardDatasetIndex.CATCHMENT_ID,
                                    values=list(hydrofabric.get_all_catchment_ids())),
                # Define hydrofabric id restriction for domain
                DiscreteRestriction(variable=StandardDatasetIndex.HYDROFABRIC_ID, values=[hydrofabric.uid])]
            # If included, also append region restriction
            # TODO: (later) implement this part later
            # TODO: (later) consider whether conus should literally also include all the individual VPUs, plus "CONUS"
            if region is not None:
                if hydrofabric.is_conus and region.lower() != "conus":
                    raise DmodRuntimeError(f"Determined hydrofabric to be CONUS, but got different region {region}")
                d_restricts.append(DiscreteRestriction(variable=StandardDatasetIndex.HYDROFABRIC_REGION,
                                                       values=[region]))
            elif hydrofabric.is_conus:
                d_restricts.append(DiscreteRestriction(variable=StandardDatasetIndex.HYDROFABRIC_REGION,
                                                       values=["CONUS"]))

            if 'version' in kwargs:
                d_restricts.append(DiscreteRestriction(variable=StandardDatasetIndex.HYDROFABRIC_VERSION,
                                                       values=[kwargs['version']]))

            return DataDomain(data_format=DataFormat.NGEN_GEOPACKAGE_HYDROFABRIC_V2, discrete_restrictions=d_restricts)
        except Exception as e:
            raise DmodRuntimeError(f"{self.__class__.__name__} encountered {e.__class__.__name__} attempting to detect "
                                   f"domain for data item: {e!s}")


class RealizationConfigDomainDetector(ItemDataDomainDetector):

    _data_format = DataFormat.NGEN_REALIZATION_CONFIG

    def detect(self, **_) -> DataDomain:
        try:
            real_obj = ngen.config.realization.NgenRealization(**json.load(self._item.open()))
        except Exception as e:
            raise DmodRuntimeError(f"{self.__class__.__name__} failed detect due to {e.__class__.__name__}: {e!s}")

        # When there is a global config, make catchment restriction values empty list to indicate "all"
        has_global_config = real_obj.global_config is not None and real_obj.global_config.formulations
        cat_restrict = DiscreteRestriction(variable=StandardDatasetIndex.CATCHMENT_ID,
                                           values=[] if has_global_config else sorted(real_obj.catchments.keys()))
        time_range = TimeRange(begin=real_obj.time.start_time, end=real_obj.time.end_time)
        # An individual file won't have a data id (i.e., data_id only applies to a Dataset or collection)
        return DataDomain(data_format=self.get_data_format(), continuous_restrictions=[time_range],
                          discrete_restrictions=[cat_restrict])
