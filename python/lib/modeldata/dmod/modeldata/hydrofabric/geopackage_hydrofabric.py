from __future__ import annotations
import pyogrio
import geopandas as gpd
import hashlib
from pandas.util import hash_pandas_object
from pathlib import Path
from typing import Any, Callable, Dict, FrozenSet, Iterable, Iterator, List, Optional, Tuple, Union
from hypy import Nexus, Realization
from .hydrofabric import HydrofabricCatchment, Hydrofabric, C, N
import sqlite3
from ..subset import SubsetDefinition
from contextlib import contextmanager
from typing_extensions import Self
import pyproj


class GeoPackageCatchment(HydrofabricCatchment):
    """
    Customized subtype of ::class:`HydrofabricCatchment` backed by dataframes from a parent ::class:`GeoPackageHydrofabric`.

    Type overrides most properties of superclass so that those can be evaluated on-demand. This supports creating an
    instance based on data and a parent, and defers the association (or really, associates indirectly and gets the
    linked object on-demand) to things like a connected nexus for which the nexus object may or may not yet exist.
    """

    __slots__ = ["_cat_id", "_hydrofabric", "_catchments_df", "_nexuses_df", "_col_cat_id",
                 "_catchments_crs", "_col_nex_id", "_col_to_cat", "_col_to_nex"]

    def __init__(self, cat_id: str, hydrofabric: 'GeoPackageHydrofabric', catchments_df: gpd.GeoDataFrame,
                 catchment_crs: pyproj.CRS, nexuses_df: gpd.GeoDataFrame, col_cat_id: str, col_nex_id: str,
                 col_to_cat: str, col_to_nex: str):
        """
        Initialize this instance.

        Parameters
        ----------
        cat_id : str
            The id of the represented catchment.
        hydrofabric : GeoPackageHydrofabric
            The backing package hydrofabric.
        catchments_df : gpd.GeoDataFrame
            The geodataframe from parent hydrofabric specifically containing catchment data (for hydrologic modeling).
        catchment_crs : pyproj.CRS
            The coordinate reference system of the catchments data.
        nexuses_df : gpd.GeoDataFrame
            The geodataframe from parent hydrofabric specifically containing nexus data.
        col_cat_id : str
            The name of the column within ``catchments_df`` that holds catchment ids.
        col_nex_id : str
            The name of the column within ``nexuses_df`` that holds nexus ids.
        col_to_cat : str
            The name of the column within ``nexuses_df`` that holds reference to downstream catchment (by id).
        col_to_nex : str
            The name of the column within ``catchments_df`` that holds reference to downstream catchment (by id).
        """
        self._cat_id: str = cat_id
        self._hydrofabric: GeoPackageHydrofabric = hydrofabric
        self._catchments_df: gpd.GeoDataFrame = catchments_df
        self._nexuses_df: gpd.GeoDataFrame = nexuses_df
        self._catchments_crs: pyproj.CRS = catchment_crs
        self._col_cat_id = col_cat_id
        self._col_nex_id = col_nex_id
        self._col_to_cat = col_to_cat
        self._col_to_nex = col_to_nex

    def _get_conjoined_ids(self) -> List[str]:
        """
        Process and return the list of ids of those catchments in a conjoined relationship with this instance.

        Returns
        -------
        List[str]
            The list of ids of catchments in a conjoined relationship with this instance.
        """
        # TODO: implement properly
        raise NotImplementedError()

    def _get_contained_ids(self) -> List[str]:
        """
        Process and return the list of ids of those catchments having an "is-in" relationship with this instance.

        Returns
        -------
        List[str]
            The list of ids of those catchments having an "is-in" relationship with this instance.
        """
        # TODO: implement properly
        raise NotImplementedError()

    def _get_catchment_record(self) -> gpd.GeoDataFrame:
        """
        Get the (1-line) sub-dataframe from the catchments layer dataframe for this particular catchment.

        Returns
        -------
        gpd.GeoDataFrame
            The (1-line) sub-dataframe from the catchments layer dataframe for this particular catchment.
        """
        df = self._catchments_df.loc[self._catchments_df[self._col_cat_id] == self._cat_id]
        if df.shape[0] == 0:
            msg = 'No backing records in {} data for {} {}'
            raise RuntimeError(msg.format(self._hydrofabric.__class__.__name__, self.__class__.__name__, self._cat_id))
        elif df.shape[0] > 1:
            msg = 'Multiple ({}) backing records in {} data for catchment with id {}'
            raise RuntimeError(msg.format(df.shape[0], self._hydrofabric.__class__.__name__, self._cat_id))
        else:
            return df

    @property
    def area(self) -> float:
        return self._get_catchment_record()['areasqkm'].values[0]

    @property
    def elevation(self) -> float:
        raise NotImplementedError(f"{self.__class__.__name__} has not currently implemented elevation property.")

    @property
    def latitude(self) -> float:
        raise NotImplementedError(f"{self.__class__.__name__} has not currently implemented latitude property.")

    @property
    def conjoined_catchments(self) -> Tuple['GeoPackageCatchment', ...]:
        """

        Returns
        -------
        Tuple['GeoPackageCatchment']
            Tuple of catchment objects in a conjoined relationship with this object.
        """
        return tuple([c for c in [self._hydrofabric.get_catchment_by_id(cid) for cid in self._get_conjoined_ids()] if
                      c is not None])

    @property
    def contained_catchments(self) -> Tuple['GeoPackageCatchment', ...]:
        """
        Tuple of catchment object having an "is-in" relationship with this catchment object.

        Returns
        -------
        Tuple[GeoPackageCatchment]
            Tuple of catchment object having an "is-in" relationship with this catchment object.
        """
        return tuple([c for c in [self._hydrofabric.get_catchment_by_id(cid) for cid in self._get_contained_ids()] if
                      c is not None])

    @property
    def containing_catchment(self) -> Optional['GeoPackageCatchment']:
        """
        The (optional) catchment with which this catchment has an "is-in" relationship.

        Returns
        -------
        Optional[GeoPackageCatchment]
            The catchment with which this catchment has an "is-in" relationship, or ``None`` if there is not one.
        """
        # TODO: implement properly
        raise NotImplementedError

    @property
    def id(self) -> str:
        """
        The catchment identifier.

        Returns
        -------
        str
            The catchment identifier.
        """
        return self._cat_id

    @property
    def inflow(self) -> Optional['GeoPackageNexus']:
        """
        In-flowing connected Nexus.

        Returns
        -------
        Optional[GeoPackageNexus]
            In-flowing connected Nexus.
        """
        matches_df = self._nexuses_df.loc[self._nexuses_df[self._col_to_cat] == self._cat_id]
        if matches_df.shape[0] > 1:
            raise RuntimeError("Invalid catchment {} with multiple inflow nexuses".format(self._cat_id))
        elif matches_df.shape[0] == 0:
            return None
        else:
            return self._hydrofabric.get_nexus_by_id(matches_df[self._col_nex_id].values[0])

    @property
    def outflow(self) -> Optional['GeoPackageNexus']:
        """
        Out-flowing connected ::class:`GeoPackageNexus`.

        Returns
        -------
        Optional[GeoPackageNexus]
            Out-flowing connected nexus.
        """
        nex_id = self._get_catchment_record()[self._col_to_nex].values[0]
        return self._hydrofabric.get_nexus_by_id(nex_id)


class GeoPackageNexus(Nexus):
    """
    Customized subtype of ::class:`Nexus` backed by dataframes from a parent ::class:`GeoPackageHydrofabric`.

    Type overrides most properties of superclass so that those can be evaluated on-demand. This supports creating an
    instance based on data and a parent, and defers the association (or really, associates indirectly and gets the
    linked object on-demand) to things like a connected catchment for which the catchment object may or may not yet
    exist.
    """

    __slots__ = ["_nex_id", "_hydrofabric", "_catchments_df", "_nexuses_df", "_col_cat_id", "_col_nex_id",
                 "_col_to_cat", "_col_to_nex"]

    def __init__(self, nex_id: str, hydrofabric: 'GeoPackageHydrofabric', catchments_df: gpd.GeoDataFrame,
                 nexuses_df: gpd.GeoDataFrame, col_cat_id: str, col_nex_id: str, col_to_cat: str, col_to_nex: str):
        """
        Initialize this instance.

        Parameters
        ----------
        nex_id : str
            The id of the represented nexus.
        hydrofabric : GeoPackageHydrofabric
            The backing package hydrofabric.
        catchments_df : gpd.GeoDataFrame
            The geodataframe from parent hydrofabric specifically containing catchment data (for hydrologic modeling).
        nexuses_df : gpd.GeoDataFrame
            The geodataframe from parent hydrofabric specifically containing nexus data.
        col_cat_id : str
            The name of the column within ``catchments_df`` that holds catchment ids.
        col_nex_id : str
            The name of the column within ``nexuses_df`` that holds nexus ids.
        col_to_cat : str
            The name of the column within ``nexuses_df`` that holds reference to downstream catchment (by id).
        col_to_nex : str
            The name of the column within ``catchments_df`` that holds reference to downstream catchment (by id).
        """
        self._nex_id: str = nex_id
        self._hydrofabric: GeoPackageHydrofabric = hydrofabric
        self._catchments_df: gpd.GeoDataFrame = catchments_df
        self._nexuses_df: gpd.GeoDataFrame = nexuses_df
        self._col_cat_id = col_cat_id
        self._col_nex_id = col_nex_id
        self._col_to_cat = col_to_cat
        self._col_to_nex = col_to_nex

    def _get_nexus_record(self) -> gpd.GeoDataFrame:
        """
        Get the (1-line) sub-dataframe from the ``nexus`` layer dataframe for this particular nexus.

        Returns
        -------
        gpd.GeoDataFrame
            The (1-line) ssub-dataframe from the ``nexus`` layer dataframe for this particular nexus.
        """
        df = self._nexuses_df.loc[self._nexuses_df[self._col_nex_id] == self._nex_id]
        if df.shape[0] == 0:
            msg = 'No backing records in {} data for {} {}'
            raise RuntimeError(msg.format(self._hydrofabric.__class__.__name__, self.__class__.__name__, self._nex_id))
        elif df.shape[0] > 1:
            msg = 'Multiple ({}) backing records in {} data for nexus with id {}'
            raise RuntimeError(msg.format(df.shape[0], self._hydrofabric.__class__.__name__, self._nex_id))
        else:
            return df

    @property
    def id(self) -> str:
        """
        The nexus identifier.

        Returns
        -------
        str
            The nexus identifier.
        """
        return self._nex_id

    @property
    def receiving_catchments(self) -> Tuple['GeoPackageCatchment', ...]:
        """
        Tuple of GeoPackageCatchment object(s) receiving water from nexus

        Returns
        -------
        Tuple['GeoPackageCatchment']
            Tuple of GeoPackageCatchment object(s) receiving water from nexus
        """
        catchments = [self._hydrofabric.get_catchment_by_id(cid) for cid in
                      self._get_nexus_record()[self._col_to_cat].values]
        return tuple([c for c in catchments if c is not None])

    @property
    def contributing_catchments(self) -> Tuple['GeoPackageCatchment', ...]:
        """
        Tuple of GeoPackageCatchment object(s) contributing water to nexus

        Returns
        -------
        Tuple['GeoPackageCatchment']
            Tuple of GeoPackageCatchment object(s) contributing water to nexus
        """
        cat_rows = self._catchments_df.loc[self._catchments_df[self._col_to_nex] == self._nex_id]
        cat_lookups = [self._hydrofabric.get_catchment_by_id(cid) for cid in
                       cat_rows[self._col_cat_id].values]
        return tuple([c for c in cat_lookups if c is not None])


class GeoPackageHydrofabric(Hydrofabric[GeoPackageCatchment, GeoPackageNexus]):
    """
    Hydrofabric implementation sourced from and backed by Nextgen hydrofabric GeoPackage (v1.2) artifacts.

    See https://noaa-owp.github.io/hydrofabric/schema.html.
    """

    #_FLOWPATHS_LAYER_NAME = 'flowpaths'
    #_FLOWPATHS_CAT_ID_COL = 'realized_catchment'
    #_FLOWPATHS_TO_NEX_COL = 'toid'

    _DIVIDES_LAYER_NAME = 'divides'
    _DIVIDES_CAT_ID_COL = 'divide_id'
    _DIVIDES_TO_NEX_COL = 'toid'

    _NEXUS_LAYER_NAME = 'nexus'
    _NEXUS_NEX_ID_COL = 'id'
    _NEXUS_TO_CAT_COL = 'toid'

    @classmethod
    def from_file(cls, geopackage_file: Union[str, Path, bytes], vpu: Optional[int] = None, is_conus: bool = False) -> 'GeoPackageHydrofabric':
        """
        Initialize a new instance from a GeoPackage file or contents of such a file (as ``bytes``).

        Note that while a warning may appear because of implementation details in ``pyogrio``, this should work
        perfectly well if passed raw bytes from a file.

        Parameters
        ----------
        geopackage_file: Union[str, Path, bytes]
            The source file for data, or raw data from such a file, from which to instantiate.
        vpu: Optional[int]
            The VPU of the hydrofabric to create, if it is known (defaults to ``None``).
        is_conus: bool
            Whether this hydrofabric is for all of CONUS (defaults to ``False``).

        Returns
        -------
        GeoPackageHydrofabric
            A new instance of this type.
        """
        # pyogrio's function returns an ndarry of ndarrays, with inner layer info array containing layer name and type
        # We only need a list of layer names, though
        layer_names = [layer_info[0] for layer_info in pyogrio.list_layers(geopackage_file)]
        return cls(layer_names=layer_names,
                   layer_dataframes={ln: gpd.read_file(geopackage_file, layer=ln, engine="pyogrio") for ln in layer_names},
                   vpu=vpu,
                   is_conus=is_conus)

    def __init__(self, layer_names: List[str], layer_dataframes: Dict[str, gpd.GeoDataFrame], vpu: Optional[int] = None,
                 is_conus: bool = False):
        self._layer_names: List[str] = layer_names
        self._dataframes: Dict[str, gpd.GeoDataFrame] = layer_dataframes
        self._roots = None
        self._vpu = vpu
        self._is_conus = is_conus

        #flowpaths = self._dataframes[self._FLOWPATHS_LAYER_NAME]
        divides = self._dataframes[self._DIVIDES_LAYER_NAME]
        nexuses = self._dataframes[self._NEXUS_LAYER_NAME]

        col_args = {'col_cat_id': self._DIVIDES_CAT_ID_COL, 'col_nex_id': self._NEXUS_NEX_ID_COL,
                    'col_to_cat': self._NEXUS_TO_CAT_COL, 'col_to_nex': self._DIVIDES_TO_NEX_COL}

        self._catchments: Dict[str, GeoPackageCatchment] = dict(
            [(cid, GeoPackageCatchment(cid, self, divides, divides.crs, nexuses, **col_args)) for cid in
             self.get_all_catchment_ids()])

        self._nexuses: Dict[str, GeoPackageNexus] = dict(
            [(nid, GeoPackageNexus(nid, self, divides, nexuses, **col_args)) for nid in self.get_all_nexus_ids()])

    def __eq__(self, other):
        if not isinstance(other, GeoPackageHydrofabric) or self.uid != other.uid:
            return False
        if len(self._layer_names) != len(other._layer_names):
            return False
        for layer_name in self._layer_names:
            if layer_name not in other._dataframes:
                return False
            elif not self._dataframes[layer_name].equals(other._dataframes[layer_name]):
                return False
        return True

    def __hash__(self) -> int:
        return hash(self.uid)

    def get_all_catchment_ids(self) -> Tuple[str, ...]:
        """
        Get ids for all contained catchments.

        Returns
        -------
        Tuple[str, ...]
            Ids for all contained catchments.
        """
        return tuple(self._dataframes[self._DIVIDES_LAYER_NAME][self._DIVIDES_CAT_ID_COL].values)

    def get_all_nexus_ids(self) -> Tuple[str, ...]:
        """
        Get ids for all contained nexuses.

        Returns
        -------
        Tuple[str, ...]
            Ids for all contained nexuses.
        """
        return tuple(self._dataframes[self._NEXUS_LAYER_NAME][self._NEXUS_NEX_ID_COL].values)

    def get_catchment_by_id(self, catchment_id: str) -> Optional[GeoPackageCatchment]:
        return self._catchments.get(catchment_id)

    def get_nexus_by_id(self, nexus_id: str) -> Optional[GeoPackageNexus]:
        return self._nexuses.get(nexus_id)

    def get_subset_hydrofabric(self, subset: SubsetDefinition) -> 'GeoPackageHydrofabric':
        """
        Derive a hydrofabric object from this one with only entities included in a given subset.

        Parameters
        ----------
        subset : SubsetDefinition
            Subset describing which catchments/nexuses from this instance may be included in the produced hydrofabric.

        Returns
        -------
        GeoJsonHydrofabric
            A hydrofabric object that is a subset of this instance as defined by the given param.
        """
        # Note that this is somewhat specific to the schema of v1.2, though is probably similar to other versions
        new_dfs = dict()

        # A dictionary to encapsulate how to handle subsetting a particular, known layer type
        # The lambda is to delay evaluation, as in some cases a different layer's subset is needed for deriving a subset
        #
        # Basically, define what we should do for layer we could encounter, since it is possible to not always encounter
        # the same set of layers, even for the same version (e.g., the CONUS v1.2 file doesn't have 'forcing_metadata')
        #
        # Key: layer name
        # Value: Tuple[str, Callable[[], Iterable]]
            # Value[0]: name of column in this known layer that holds ids, which we will examine for subsetting
            # Value[1]: callable no arg function, returning collection of ids for records/rows to include in subset
        subset_query_setups: Dict[str, Tuple[str, Callable[[], Iterable[str]]]] = {
            'flowpaths': ('realized_catchment', lambda: subset.catchment_ids),
            'divides': (self._DIVIDES_CAT_ID_COL, lambda: subset.catchment_ids),
            'nexus': (self._NEXUS_NEX_ID_COL, lambda: subset.nexus_ids),
            'flowpath_attributes': ('id', lambda: new_dfs['flowpaths']['id']),
            'flowpath_edge_list': ('id', lambda: new_dfs['flowpaths']['id']),
            'crosswalk': ('id', lambda: new_dfs['flowpaths']['id']),
            'cfe_noahowp_attributes': ('id', lambda: subset.catchment_ids),
            'forcing_metadata': ('id', lambda: subset.catchment_ids)
        }

        # Then, apply this logic to every encountered layer to create subset layer/dataframe to use to init new instance
        def subset_layer(layer_name: str):
            dataframe = self._dataframes[layer_name]
            id_search_col = subset_query_setups[layer_name][0]
            applicable_ids = subset_query_setups[layer_name][1]()
            new_dfs[layer_name] = dataframe.loc[dataframe[id_search_col].isin(applicable_ids)]

        # Subset 'flowpaths' layer first; it's ids may be needed for subsetting other things like 'flowpath_edge_list'
        if 'flowpaths' in self._layer_names:
            subset_layer('flowpaths')

        # Now, generate the rest of the subset layers/dataframes
        for layer in [ln for ln in self._layer_names if ln != 'flowpaths']:
            subset_layer(layer)

        return GeoPackageHydrofabric(layer_names=self._layer_names, layer_dataframes=new_dfs)

    def is_catchment_recognized(self, catchment_id: str) -> bool:
        """
        Test whether a catchment is recognized.

        Parameters
        ----------
        catchment_id : str
            The id of the catchment.

        Returns
        -------
        bool
            Whether the catchment is recognized.
        """
        return catchment_id in self._dataframes[self._DIVIDES_LAYER_NAME][self._DIVIDES_CAT_ID_COL].values

    @property
    def is_conus(self) -> bool:
        """
        Whether this hydrofabric represents all of CONUS.

        Returns
        -------
        bool
            Whether this hydrofabric represents all of CONUS.
        """
        return self._is_conus

    def is_nexus_recognized(self, nexus_id: str) -> bool:
        """
       Test whether a nexus is recognized.

       Parameters
       ----------
       nexus_id : str
           The id of the nexus.

       Returns
       -------
       bool
           Whether the nexus is recognized.
       """
        return nexus_id in self._dataframes[self._NEXUS_LAYER_NAME][self._NEXUS_NEX_ID_COL].values

    @property
    def roots(self) -> FrozenSet[str]:
        """
        Get the ids of the root nodes of the hydrofabric graph.

        Returns
        -------
        FrozenSet[str]
            The set of ids for the roots of the hydrofabric graph.

        See Also
        -------
        ::attribute:`hydrofabric_graph`
        """
        if self._roots is None:
            divides_df = self._dataframes[self._DIVIDES_LAYER_NAME]
            nexuses_df = self._dataframes[self._NEXUS_LAYER_NAME]
            self._roots = frozenset(divides_df.loc[~divides_df[self._DIVIDES_CAT_ID_COL].isin(
                nexuses_df[self._NEXUS_TO_CAT_COL].values)][self._DIVIDES_CAT_ID_COL].values)
        return self._roots

    @property
    def uid(self) -> str:
        """
        Get a unique id for this instance.

        Ids are generated from in a deterministic manner from the underlying data.

        Returns
        -------
        int
            A unique id for this instance.
        """
        layer_hashes = [hash_pandas_object(self._dataframes[layer]).values.sum() for layer in sorted(self._layer_names)]
        return hashlib.sha1(','.join([str(h) for h in layer_hashes]).encode('UTF-8')).hexdigest()

    @property
    def vpu(self) -> Optional[int]:
        """
        The VPU of this hydrofabric, if it is known.

        Returns
        -------
        Optional[int]
            The VPU of this hydrofabric, if it is known; otherwise ``None``.
        """
        return self._vpu

    def write_file(self, output_file: Union[str, Path], overwrite_existing: bool = False):
        """
        Write this hydrofabric to a GeoPackage file.

        If a file exists, by default an exception is thrown.  However, a parameter can be passed such that an existing
        file is removed and overwritten.  This only will apply to regular files, though.

        Parameters
        ----------
        output_file: Union[str, Path]
            The file to which to write the data.
        overwrite_existing: bool
            Whether an existing file should be overwritten (``False`` by default).
        """
        output_path = output_file if isinstance(output_file, Path) else Path(output_file)
        if output_path.exists():
            if output_path.is_dir():
                msg = 'Cannot write {} data to path {}: this is an existing directory'
                raise RuntimeError(msg.format(self.__class__.__name__, output_file))
            elif output_path.is_file() and overwrite_existing:
                msg = 'Cannot write {} data to existing file {} when overwrite is set to False'
                raise RuntimeError(msg.format(self.__class__.__name__, output_file))
            elif output_path.is_file():
                output_path.unlink()
            else:
                msg = 'Cannot write {} data to existing, non-regular file {}'
                raise RuntimeError(msg.format(self.__class__.__name__, output_file))

        for layer_name in self._layer_names:
            self._dataframes[layer_name].to_file(output_file, driver="GPKG", layer=layer_name)


class V22Catchment(GeoPackageCatchment):

    __slots__ = GeoPackageCatchment.__slots__ + ["_cat_attrs_df", "_latitude", "_longitude"]

    def __init__(self, cat_id: str, hydrofabric: 'GeoPackageHydrofabric', catchments_df: gpd.GeoDataFrame,
                 catchments_crs: pyproj.CRS, cat_attrs_df: gpd.GeoDataFrame, nexuses_df: gpd.GeoDataFrame,
                 col_cat_id: str, col_nex_id: str, col_to_cat: str, col_to_nex: str):
        """
        Initialize this instance.

        Parameters
        ----------
        cat_id : str
            The id of the represented catchment.
        hydrofabric : GeoPackageHydrofabric
            The backing package hydrofabric.
        catchments_df : gpd.GeoDataFrame
            The geodataframe from parent hydrofabric specifically containing catchment data (for hydrologic modeling).
        catchments_crs : pyproj.CRS
            The coordinate reference system (CRS) for the catchment data.
        cat_attrs_df : gpd.GeoDataFrame
            The geodataframe from parent hydrofabric specifically containing catchment attributes.
        nexuses_df : gpd.GeoDataFrame
            The geodataframe from parent hydrofabric specifically containing nexus data.
        col_cat_id : str
            The name of the column within ``catchments_df`` that holds catchment ids.
        col_nex_id : str
            The name of the column within ``nexuses_df`` that holds nexus ids.
        col_to_cat : str
            The name of the column within ``nexuses_df`` that holds reference to downstream catchment (by id).
        col_to_nex : str
            The name of the column within ``catchments_df`` that holds reference to downstream catchment (by id).
        """
        super().__init__(cat_id, hydrofabric, catchments_df, catchments_crs, nexuses_df, col_cat_id, col_nex_id, col_to_cat, col_to_nex)
        self._cat_attrs_df = cat_attrs_df
        self._latitude = None
        self._longitude = None

    def _convert_to_long_lat(self):
        if self._latitude is None and self._longitude is None:
            dst_crs = pyproj.CRS.from_epsg(4326)

            if self._catchments_crs.equals(dst_crs):
                self._latitude = self.y
                self._longitude = self.x
            else:
                transformer = pyproj.Transformer.from_crs(self._catchments_crs, dst_crs, always_xy=True)
                self._longitude, self._latitude = transformer.transform(self.x, self.y)

    def _get_attribute_record(self) -> gpd.GeoDataFrame:
        """
        Get the (1-line) sub-dataframe from the catchment attributes layer dataframe for this particular catchment.

        Returns
        -------
        gpd.GeoDataFrame
            The (1-line) sub-dataframe from the catchment attributes layer dataframe for this particular catchment.
        """
        df = self._cat_attrs_df.loc[self._catchments_df[self._col_cat_id] == self._cat_id]
        if df.shape[0] == 0:
            msg = 'No backing records in {} data for {} {}'
            raise RuntimeError(msg.format(self._hydrofabric.__class__.__name__, self.__class__.__name__, self._cat_id))
        elif df.shape[0] > 1:
            msg = 'Multiple ({}) backing records in {} data for catchment with id {}'
            raise RuntimeError(msg.format(df.shape[0], self._hydrofabric.__class__.__name__, self._cat_id))
        else:
            return df

    @property
    def elevation(self) -> float:
        return self._get_attribute_record()['mean.elevation'].values[0]

    @property
    def latitude(self) -> float:
        if self._latitude is None:
            self._convert_to_long_lat()
        return self._latitude

    @property
    def x(self) -> float:
        return self._get_attribute_record()['centroid_x'].values[0]

    @property
    def y(self) -> float:
        return self._get_attribute_record()['centroid_y'].values[0]


class Version22Hydrofabric(GeoPackageHydrofabric, Hydrofabric[V22Catchment, GeoPackageNexus]):

    _DIV_ATTRS_LAYER_NAME = 'divide-attributes'
    _DIV_ATTRS_CAT_ID_COL = 'divide_id'
    #_DIVIDES_TO_NEX_COL = 'toid'

    def __init__(self, layer_names: List[str], layer_dataframes: Dict[str, gpd.GeoDataFrame], vpu: Optional[int] = None,
                 is_conus: bool = False):
        self._layer_names: List[str] = layer_names
        self._dataframes: Dict[str, gpd.GeoDataFrame] = layer_dataframes
        self._roots = None
        self._vpu = vpu
        self._is_conus = is_conus

        #flowpaths = self._dataframes[self._FLOWPATHS_LAYER_NAME]
        divides = self._dataframes[self._DIVIDES_LAYER_NAME]
        try:
            divide_attributes = self._dataframes[self._DIV_ATTRS_LAYER_NAME]
        except KeyError as e:
            raise RuntimeError(f'{self.__class__.__name__} did not find expected layer {self._DIV_ATTRS_LAYER_NAME} '
                               f'for catchment attributes in hydrofabric data.  This may either be a hydrofabric of a'
                               f'differ version or have not been constructed as expected with that table.  Please '
                               f'examine the hydrofabric raw data.') from e
        nexuses = self._dataframes[self._NEXUS_LAYER_NAME]

        col_args = {'col_cat_id': self._DIVIDES_CAT_ID_COL, 'col_nex_id': self._NEXUS_NEX_ID_COL,
                    'col_to_cat': self._NEXUS_TO_CAT_COL, 'col_to_nex': self._DIVIDES_TO_NEX_COL}

        self._catchments: Dict[str, V22Catchment] = {
            cid: V22Catchment(cid, self, divides, divides.crs, divide_attributes, nexuses, **col_args) for cid in
            self.get_all_catchment_ids()}

        self._nexuses: Dict[str, GeoPackageNexus] = {nid: GeoPackageNexus(nid, self, divides, nexuses, **col_args) for
                                                     nid in self.get_all_nexus_ids()}


class V22SqliteCatchment(HydrofabricCatchment):

    __slots__ = ["_id", "_connection", "_hydrofabric", "_cursor", "_area", "_elevation", "_cat_attributes",
                 "_catchments_crs", "_latitude", "_longitude", "_slope", "_x", "_y", "_inflow_nexus_id",
                 "_outflow_nexus_id", "_realization", ]

    _CAT_TABLE_NAME = 'divides'
    _CAT_TABLE_CAT_ID_COL = 'divide_id'
    _CAT_TABLE_DEST_ID_COL = 'toid'

    _CAT_ATTR_TABLE = 'divide-attributes'
    _CAT_TABLE_CAT_ID_COL = 'divide_id'

    _NETWORK_TABLE_NAME = 'network'
    _NETWORK_TABLE_CAT_ID_COL = 'divide_id'
    _NETWORK_TABLE_WB_ID_COL = 'id'

    _NEXUS_TABLE_NAME = 'nexus'
    _NEXUS_TABLE_NEX_ID_COL = 'id'
    _NEXUS_TABLE_DEST_ID_COL = 'toid'


    @classmethod
    def get_catchments_table_name(cls) -> str:
        return cls._CAT_TABLE_NAME

    @classmethod
    def get_catchment_attributes_table_name(cls) -> str:
        return cls._CAT_ATTR_TABLE

    @classmethod
    def get_cat_id_column_names(cls) -> dict[str, str]:
        """ Get the column name for catchment id for all tables of interest. """
        return {cls.get_catchments_table_name(): "divide_id", cls.get_catchment_attributes_table_name(): "divide_id"}

    def __init__(self, cat_id: str, hydrofabric: V22SqliteHydrofabric, catchment_crs: pyproj.CRS,
                 connection: sqlite3.Connection):
        self._id = cat_id
        self._connection = connection
        self._hydrofabric: V22SqliteHydrofabric = hydrofabric
        self._cursor = None
        self._catchments_crs = catchment_crs

        self._cat_attributes = None
        self._area = None
        self._elevation = None
        self._latitude = None
        self._longitude = None
        self._slope = None
        self._x = None
        self._y = None
        self._inflow_nexus_id = None
        self._outflow_nexus_id = None
        self._realization = None

    # def _convert_to_long_lat(self):
    #     if self._latitude is None and self._longitude is None:
    #         coord_sys = self._get_cat_coordinate_system()
    #         if coord_sys == "4326":
    #             self._latitude = self.y
    #             self._longitude = self.x
    #         else:
    #             srs_crs = pyproj.CRS.from_epsg(int(coord_sys))
    #             dst_crs = pyproj.CRS.from_epsg(4326)
    #             transformer = pyproj.Transformer.from_crs(srs_crs, dst_crs, always_xy=True)
    #             self._longitude, self._latitude = transformer.transform(self.x, self.y)
    #
    # def _get_cat_coordinate_system(self) -> str:
    #     """ Get the coordinate system of for catchments. """
    #     if self._cat_coordinate_system is None:
    #         with self.cursor_context() as cursor:
    #             result = cursor.execute("select srs_id from 'gpkg_geometry_columns' where table_name = ?",
    #                                     (self._CAT_TABLE_NAME,)
    #                                     ).fetchall()
    #             self._cat_coordinate_system = result[0][0]
    #     return self._cat_coordinate_system

    def _convert_to_long_lat(self):
        if self._latitude is None and self._longitude is None:
            dst_crs = pyproj.CRS.from_epsg(4326)

            if self._catchments_crs.equals(dst_crs):
                self._latitude = self.y
                self._longitude = self.x
            else:
                transformer = pyproj.Transformer.from_crs(self._catchments_crs, dst_crs, always_xy=True)
                self._longitude, self._latitude = transformer.transform(self.x, self.y)

    def _query_catchment_property(self, property_name: str):
        """
        Query the catchments table for a single property value for this particular catchment.

        Parameters
        ----------
        property_name
            The name of the property of interest

        Returns
        -------
        The value of the single noted property for this catchment.
        """
        table_name = self.get_catchments_table_name()
        cat_id_key = self.get_cat_id_column_names()[table_name]

        with self.cursor_context() as cursor:
            records = cursor.execute(
                f"SELECT {property_name} FROM {table_name} WHERE {cat_id_key} = ?", (self.id,)
            ).fetchall()
        # TODO: later sanity check
        return records[0][0]

    def _get_cat_attributes(self) -> list[Any]:
        table_name = self.get_catchment_attributes_table_name()
        cat_id_key = self.get_cat_id_column_names()[table_name]

        if self._cat_attributes is None:
            with self.cursor_context() as cursor:
                values = cursor.execute(
                    f"SELECT * FROM '{table_name}' WHERE {cat_id_key} = ?", (self.id,)
                ).fetchall()[0]
                col_names = [r[1] for r in cursor.execute(f"pragma table_info('{table_name}')").fetchall()]
                self._cat_attributes = dict(zip(col_names, values))

        return self._cat_attributes

    # def _query_catchment_attribute(self, attr_name: str):
    #     """
    #     Query the catchment attributes table for a single attribute value for this particular catchment.
    #
    #     Parameters
    #     ----------
    #     attr_name
    #         The name of the catchment attribute of interest
    #
    #     Returns
    #     -------
    #     The value of the single noted catchment attribute for this catchment.
    #     """
    #     table_name = self.get_catchment_attributes_table_name()
    #     cat_id_key = self.get_cat_id_column_names()[table_name]
    #
    #     with self.cursor_context() as cursor:
    #         records = cursor.execute(
    #             f"SELECT {attr_name} FROM '{table_name}' WHERE {cat_id_key} = ?", (self.id,)
    #         ).fetchall()
    #     # TODO: later sanity check
    #     return records[0][0]

    def _query_catchment_attribute(self, attr_name: str):
        return self._get_cat_attributes()[attr_name]

    @contextmanager
    def cursor_context(self) -> Iterator[sqlite3.Cursor]:
        """Yield a cursor instance with a lifetime of the context manager."""
        if self._cursor is not None:
            raise RuntimeError(f'{self.__class__.__name__} cannot use a SQLite connection cursor context twice')
        self._cursor = self._connection.cursor()
        try:
            yield self._cursor
        finally:
            self._cursor.close()
            self._cursor = None

    @property
    def area(self) -> float:
        if self._area is None:
            self._area = self._query_catchment_property('areasqkm')
        return self._area

    @property
    def elevation(self) -> float:
        if self._elevation is None:
            self._elevation = self._query_catchment_attribute('mean.elevation')
        return self._elevation

    @property
    def latitude(self) -> float:
        if self._latitude is None:
            self._convert_to_long_lat()
        return self._latitude

    @property
    def longitude(self) -> float:
        if self._longitude is None:
            self._convert_to_long_lat()
        return self._longitude

    @property
    def slope(self) -> float:
        if self._slope is None:
            self._slope = self._query_catchment_attribute('mean.slope')
        return self._slope

    @property
    def conjoined_catchments(self) -> Tuple[Self, ...]:
        """

        Returns
        -------
        Tuple[Self]
            Tuple of catchment objects in a conjoined relationship with this object.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not yet support conjoined catchments")

    @property
    def contained_catchments(self) -> Tuple[Self, ...]:
        """
        Tuple of catchment object having an "is-in" relationship with this catchment object.

        Returns
        -------
        Tuple[Self]
            Tuple of catchment object having an "is-in" relationship with this catchment object.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not yet support contained catchments")

    @property
    def containing_catchment(self) -> Optional['GeoPackageCatchment']:
        """
        The (optional) catchment with which this catchment has an "is-in" relationship.

        Returns
        -------
        Optional[GeoPackageCatchment]
            The catchment with which this catchment has an "is-in" relationship, or ``None`` if there is not one.
        """
        # TODO: implement properly
        raise NotImplementedError(f"{self.__class__.__name__} does not yet support catchment-containing relationships")

    @property
    def id(self) -> str:
        """
        The catchment identifier.

        Returns
        -------
        str
            The catchment identifier.
        """
        return self._id

    @property
    def inflow(self) -> Optional[V22SqliteNexus]:
        """
        In-flowing connected Nexus.

        Returns
        -------
        Optional[V22SqliteNexus]
            In-flowing connected Nexus.
        """
        if self._inflow_nexus_id is None:
            with self.cursor_context() as cursor:
                waterbody_records = cursor.execute(
                    f"SELECT {self._NETWORK_TABLE_WB_ID_COL} "
                    f"FROM {self._NETWORK_TABLE_CAT_ID_COL} "
                    f"WHERE {self._NETWORK_TABLE_CAT_ID_COL} = ?",
                    (self.id,)
                ).fetchall()
                # TODO: sanity check this only has one
                waterbody_id = waterbody_records[0][0]

                nexus_records = cursor.execute(
                    f"SELECT {self._NEXUS_TABLE_NEX_ID_COL} "
                    f"FROM {self._NEXUS_TABLE_NAME} "
                    f"WHERE {self._NEXUS_TABLE_DEST_ID_COL} = ?",
                    (waterbody_id,)
                ).fetchall()
                # TODO: sanity check that there is only one record here (not multiple inflow nexuses
                self._inflow_nexus_id = nexus_records[0][0]
        return self._hydrofabric.get_nexus_by_id(self._inflow_nexus_id)

    @property
    def outflow(self) -> Optional[V22SqliteNexus]:
        """
        Out-flowing connected ::class:`V22SqliteNexus` instance.`.

        Returns
        -------
        Optional[V22SqliteNexus]
            Out-flowing connected nexus.
        """
        if self._outflow_nexus_id is None:
            with self.cursor_context() as cursor:
                records = cursor.execute(
                    f"SELECT {self._CAT_TABLE_DEST_ID_COL} "
                    f"FROM {self._CAT_TABLE_NAME} "
                    f"WHERE {self._CAT_TABLE_CAT_ID_COL} = ?",
                    (self.id,)
                ).fetchall()
                self._outflow_nexus_id = records[0][0]
        return self._hydrofabric.get_nexus_by_id(self._outflow_nexus_id)

    @property
    def realization(self) -> Optional[Realization]:
        """
        The optional ::class:`Realization` for this catchment.

        Returns
        -------
        Optional[Realization]
            The ::class:`Realization` for this catchment, or ``None`` if it has not been set.
        """
        return self._realization

    @realization.setter
    def realization(self, realization: Realization):
        self._realization = realization

    @property
    def x(self) -> float:
        if self._x is None:
            self._x = self._query_catchment_attribute('centroid_x')
        return self._x

    @property
    def y(self) -> float:
        if self._y is None:
            self._y = self._query_catchment_attribute('centroid_y')
        return self._y


class V22SqliteNexus(Nexus):
    """
    Customized subtype of ::class:`Nexus` backed by dataframes from a parent ::class:`V22SqliteHydrofabric`.
    """

    __slots__ = ["_nex_id", "_hydrofabric", "_catchments_df", "_nexuses_df", "_col_cat_id", "_col_nex_id",
                 "_col_to_cat", "_col_to_nex"]

    def __init__(self, nex_id: str, hydrofabric: V22SqliteHydrofabric, connection: sqlite3.Connection):
        """
        Initialize this instance.

        Parameters
        ----------
        nex_id : str
            The id of the represented nexus.
        hydrofabric : GeoPackageHydrofabric
            The backing package hydrofabric.
        """
        self._connection = connection
        self._hydrofabric = hydrofabric
        self._cursor = None
        self._nex_id: str = nex_id
        self._hydrofabric: V22SqliteHydrofabric = hydrofabric
        self._col_cat_id = 'divide_id'
        """ The name of the column within catchment table that holds catchment ids. """
        self._col_nex_id = 'id'
        """ The name of the column within nexus table that holds nexus ids."""
        self._col_to_cat = 'toid'
        """ The name of the column within nexus table` that holds reference to downstream catchment/waterbody (by id). """
        self._col_to_nex = 'toid'
        """ The name of the column within catchment table that holds reference to downstream nexus (by id). """

    @contextmanager
    def cursor_context(self) -> Iterator[sqlite3.Cursor]:
        """Yield a cursor instance with a lifetime of the context manager."""
        if self._cursor is not None:
            raise RuntimeError(f'{self.__class__.__name__} cannot use a SQLite connection cursor context twice')
        self._cursor = self._connection.cursor()
        try:
            yield self._cursor
        finally:
            self._cursor.close()
            self._cursor = None

    @property
    def id(self) -> str:
        """
        The nexus identifier.

        Returns
        -------
        str
            The nexus identifier.
        """
        return self._nex_id

    @property
    def receiving_catchments(self) -> Tuple[V22SqliteCatchment, ...]:
        """
        Tuple of GeoPackageCatchment object(s) receiving water from nexus

        Returns
        -------
        Tuple['GeoPackageCatchment']
            Tuple of GeoPackageCatchment object(s) receiving water from nexus
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not implement the property 'receiving_catchments' yet")

    @property
    def contributing_catchments(self) -> Tuple[V22SqliteCatchment, ...]:
        """
        Tuple of catchment object(s) contributing water to nexus.

        Returns
        -------
        Tuple[V22SqliteCatchment]
            Tuple of catchment object(s) contributing water to nexus.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not implement the property 'contributing_catchments' yet")


# TODO: (later) might should adjust class hierarchy and interfaces a bit to abstract GeoPackageHydrofabric and make
#  this a subtype
class V22SqliteHydrofabric(Hydrofabric[V22SqliteCatchment, V22SqliteNexus]):

    _CAT_TABLE_NAME = V22SqliteCatchment._CAT_TABLE_NAME
    _CAT_TABLE_CAT_ID_COL = V22SqliteCatchment._CAT_TABLE_CAT_ID_COL
    _CAT_TABLE_DEST_ID_COL = V22SqliteCatchment._CAT_TABLE_DEST_ID_COL

    _CAT_ATTR_TABLE = V22SqliteCatchment._CAT_ATTR_TABLE
    _CAT_TABLE_CAT_ID_COL = V22SqliteCatchment._CAT_TABLE_CAT_ID_COL

    _NETWORK_TABLE_NAME = V22SqliteCatchment._NETWORK_TABLE_NAME
    _NETWORK_TABLE_CAT_ID_COL = V22SqliteCatchment._NETWORK_TABLE_CAT_ID_COL
    _NETWORK_TABLE_WB_ID_COL = V22SqliteCatchment._NETWORK_TABLE_WB_ID_COL

    _NEXUS_TABLE_NAME = V22SqliteCatchment._NEXUS_TABLE_NAME
    _NEXUS_TABLE_NEX_ID_COL = V22SqliteCatchment._NEXUS_TABLE_NEX_ID_COL
    _NEXUS_TABLE_DEST_ID_COL = V22SqliteCatchment._NEXUS_TABLE_DEST_ID_COL
    
    def __init__(self, sqlite_file: Path, multithreaded: bool = True):
        self._sqlite_file: Path = sqlite_file
        self._connection: sqlite3.Connection = sqlite3.connect(sqlite_file, check_same_thread=not multithreaded)
        self._cursor = None
        self._roots = None
        self._catchment_crs = None

    @property
    def catchment_crs(self) -> pyproj.CRS:
        if self._catchment_crs is None:
            with self.cursor_context() as cursor:
                result = cursor.execute("select srs_id from 'gpkg_geometry_columns' where table_name = ?", (self._CAT_TABLE_NAME,)).fetchall()
                self._catchment_crs = pyproj.CRS.from_epsg(int(result[0][0]))
        return self._catchment_crs

    @contextmanager
    def cursor_context(self) -> Iterator[sqlite3.Cursor]:
        """Yield a cursor instance with a lifetime of the context manager."""
        if self._cursor is not None:
            raise RuntimeError(f'{self.__class__.__name__} cannot use a SQLite connection cursor context twice')
        self._cursor = self._connection.cursor()
        try:
            yield self._cursor
        finally:
            self._cursor.close()
            self._cursor = None

    def get_all_catchment_ids(self) -> Tuple[str, ...]:
        with self.cursor_context() as cursor:
            records = cursor.execute(f"SELECT {self._CAT_TABLE_CAT_ID_COL} FROM {self._CAT_TABLE_NAME}")
            return tuple(c[0] for c in records.fetchall())

    def get_all_nexus_ids(self) -> Tuple[str, ...]:
        with self.cursor_context() as cursor:
            records = cursor.execute(f"SELECT {self._NEXUS_TABLE_NEX_ID_COL} FROM {self._NEXUS_TABLE_NAME}")
            return tuple(n[0] for n in records.fetchall())

    def get_catchment_by_id(self, catchment_id: str) -> Optional[C]:
        return V22SqliteCatchment(cat_id=catchment_id, hydrofabric=self, catchment_crs=self.catchment_crs,
                                  connection=self._connection)

    def get_nexus_by_id(self, nexus_id: str) -> Optional[N]:
        return V22SqliteNexus(nex_id=nexus_id, hydrofabric=self, connection=self._connection)

    def get_subset_hydrofabric(self, subset: SubsetDefinition) -> 'Hydrofabric':
        raise NotImplementedError(f"{self.__class__.__name__} does not yet support subsetting")

    def is_catchment_recognized(self, catchment_id: str) -> bool:
        with self.cursor_context() as cursor:
            records = cursor.execute(
                f"SELECT count({self._CAT_TABLE_CAT_ID_COL}) "
                f"FROM {self._CAT_TABLE_NAME} "
                f"WHERE {self._CAT_TABLE_CAT_ID_COL} = ?",
                (catchment_id,)
            ).fetchall()
            # For clarity, result is still structured as a list (result rows) of tuples (values for each returned row)
            return records[0][0]

    def is_nexus_recognized(self, nexus_id: str) -> bool:
        with self.cursor_context() as cursor:
            records = cursor.execute(
                f"SELECT count({self._NEXUS_TABLE_NEX_ID_COL}) "
                f"FROM {self._NEXUS_TABLE_NAME} "
                f"WHERE {self._NEXUS_TABLE_NEX_ID_COL} = ?",
                (nexus_id,)
            ).fetchall()
            # For clarity, result is still structured as a list (result rows) of tuples (values for each returned row)
            return records[0][0]

    @property
    def roots(self) -> FrozenSet[str]:
        """
        Get the ids of the root nodes of the hydrofabric graph.

        Returns
        -------
        FrozenSet[str]
            The set of ids for the roots of the hydrofabric graph.

        See Also
        -------
        ::attribute:`hydrofabric_graph`
        """

        # For clarity, this is basically doing:
        #
        # SELECT divide_id FROM divides WHERE divide_id NOT IN (
        #       SELECT divide_id FROM network WHERE id IN (
        #               SELECT toid FROM nexus
        #       )
        # )

        if self._roots is None:
            with self.cursor_context() as cursor:
                q = (f"SELECT {self._CAT_TABLE_CAT_ID_COL} "
                     f"FROM {self._CAT_TABLE_NAME} "
                     f"WHERE {self._CAT_TABLE_CAT_ID_COL} NOT IN ("
                     f"  SELECT {self._NETWORK_TABLE_CAT_ID_COL} "
                     f"  FROM {self._NETWORK_TABLE_NAME} "
                     f"  WHERE {self._NETWORK_TABLE_WB_ID_COL} IN ("
                     f"    SELECT {self._NEXUS_TABLE_DEST_ID_COL} FROM {self._NEXUS_TABLE_NAME}"
                     f"  )"
                     f")"
                     )
                records = cursor.execute(q)
                self._roots = frozenset(c[0] for c in records.fetchall())
        return self._roots
            
