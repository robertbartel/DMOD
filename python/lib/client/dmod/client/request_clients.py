import logging
from abc import ABC, abstractmethod
from datetime import datetime
from dmod.core.execution import AllocationParadigm
from dmod.core.exception import DmodRuntimeError
from dmod.communication import DataServiceClient, ExternalRequestClient, ManagementAction, ModelExecRequestClient, \
    NGENRequest, NGENRequestResponse, UpdateMessage, UpdateMessageResponse, UpdateRegistrationMessage, \
    UpdateRegistrationResponse
from dmod.communication.client import R
from dmod.communication.dataset_management_message import DatasetManagementMessage, DatasetManagementResponse, \
    MaaSDatasetManagementMessage, MaaSDatasetManagementResponse, QueryType, DatasetQuery
from dmod.communication.data_transmit_message import DataTransmitMessage, DataTransmitResponse
from dmod.core.meta_data import DataCategory, DataDomain
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Type, Union

import asyncio
import json
import websockets

#import logging
#logger = logging.getLogger("gui_log")


class FollowableClient(ABC):

    @abstractmethod
    async def follow_exec(self, job_id: str):
        """
        Connect to the service to request update messages be sent to this client and added to the update queue.

        Parameters
        ----------
        job_id : str
            The job id of the job execution of interest.
        """
        pass

    @abstractmethod
    def get_update_from_queue(self, job_id: str) -> UpdateMessage:
        pass

    @abstractmethod
    def is_following_updates(self, job_id: str) -> bool:
        """
        Whether this client is currently following updates for the given job id.

        Parameters
        ----------
        job_id

        Returns
        -------
        bool
            Whether this client is currently following updates for the given job id.
        """
        pass


class NgenRequestClient(ModelExecRequestClient[NGENRequest, NGENRequestResponse], FollowableClient):

    # In particular needs - endpoint_uri: str, ssl_directory: Path
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cached_session_file = Path.home().joinpath('.dmod_client_session')
        self._update_queues: Dict[str, asyncio.Queue[UpdateMessage]] = dict()
        """ Map keyed by job id of queues of received, but not processed, updates from follow_exec """

    async def build_message(self, *args, **kwargs) -> NGENRequest:
        """
        Build a ::class:`NGENRequest` from the passed args.

        This function expects to receive the same args, in the same order (for non-keyword args) as the init function
        for ::class:`NGENRequest`, except for the session secret (itself a var/keyword arg for the init function of
        ::class:`NGENRequest` directly).  The session secret is stored in a property of the client, and as such provided
        directly.

        Parameters
        ----------
        args
        kwargs

        Other Parameters
        ----------
        time_range : TimeRange
            The time range for the message.
        hydrofabric_data_id : str
            The data id for the hydrofabric dataset to use for the requested job.
        hydrofabric_uid : str
            The unique id for the hydrofabric to use for the requested job.
        cpu_count : int
            The number of CPUs requested in this message.
        realization_cfg_data_id : str
            The data id for the realization config dataset to use for the requested job.
        bmi_cfg_data_id : str
            The data id for the BMI initialization config dataset to use for the requested job.
        partition_cfg_data_id : str, optional
            The optional data id for the partitioning config dataset, if one is to be specified in this job request.
        cat_ids : List[str], optional
            The list of catchment ids involved in the request, if the job should operate on a subset of the entired
            hydrofabric.
        allocation_paradigm : AllocationParadigm, optional
            The allocation paradigm requested for the job, if one is explicitly specified.

        Returns
        -------
        NGENRequest
            An initialized ::class:`NGENRequest`.
        """

        def parse_param(key_name: str, var_index: int):
            return kwargs.get(key_name, (args[var_index] if len(args) > var_index else None))

        return NGENRequest(session_secret=self.session_secret,
                           cpu_count=parse_param('cpu_count', 3),
                           allocation_paradigm=parse_param('allocation_paradigm', 8),
                           time_range=parse_param('time_range', 0),
                           hydrofabric_uid=parse_param('hydrofabric_uid', 2),
                           hydrofabric_data_id=parse_param('hydrofabric_data_id', 1),
                           config_data_id=parse_param('realization_cfg_data_id', 4),
                           bmi_cfg_data_id=parse_param('bmi_cfg_data_id', 5),
                           partition_cfg_data_id=parse_param('partition_cfg_data_id', 6),
                           catchments=parse_param('cat_ids', 7))

    async def follow_exec(self, job_id: str):
        """
        Connect to the service to request update messages be sent to this client and added to the update queue.

        Parameters
        ----------
        job_id : str
            The job id of the job execution of interest.
        """
        # TODO: handle case when the queue for this id already exists
        self._update_queues[job_id] = asyncio.Queue()
        
        try:
            register_msg = UpdateRegistrationMessage(job_id=job_id, session_secret=self.session_secret)
            raw_response = await self.async_send(str(register_msg), await_response=True)
            response_obj = UpdateRegistrationResponse.factory_init_from_deserialized_json(json.loads(raw_response))
            if response_obj is None:
                raise DmodRuntimeError("{} didn't receive registration confirmation".format(self.__class__.__name__))
            elif not response_obj.success:
                raise DmodRuntimeError("{} failed to register for updates".format(self.__class__.__name__))

            listen_for_updates = True
            while listen_for_updates:
                # Await update messages 
                raw_update = await self.async_recv()
                # Convert raw update to update object
                update_object = UpdateMessage.factory_init_from_deserialized_json(json.loads(raw_update))
                # Make sure we can read the data, or bail and respond with the error
                if not isinstance(update_object, UpdateMessage):
                    msg = 'Could not deserialize received data to a valid {}'.format(UpdateMessage.__name__)
                    response = UpdateMessageResponse(success=False, reason='Invalid Update Message Data',
                                                     response_text=msg, data={'received_data': raw_update})
                    await self.async_send(data=str(response), await_response=False)
                    break
                # Otherwise, proceed, but ensure the update was for the right record/object
                if update_object.object_id == job_id:
                    # Put received update messages into an externally-accessible queue for other async coroutines/tasks
                    await self._update_queues[job_id].put(update_object)
                    response = UpdateMessageResponse(success=True, reason='Valid Update', digest=update_object.digest)
                else:
                    msg = "Expected updates for object {} but received for id {}"
                    response = UpdateMessageResponse(success=False, reason='Unexpected Object Id',
                                                     response_text=msg.format(job_id, update_object.object_id),
                                                     digest=update_object.digest)
                await self.async_send(data=str(response), await_response=False)
                listen_for_updates = self._continue_following_updates(job_id=job_id, last_message=update_object)
        finally:
            self._update_queues.pop(job_id)

    def _continue_following_updates(self, job_id: str, last_message: UpdateMessage) -> bool:
        if last_message.object_id != job_id:
            msg = '{} received update for unexpected object id {} (expected {}); ignoring'
            logging.warning(msg.format(self.__class__.__name__, last_message.object_id, job_id))
            return True
        stop_steps = {'DATA_UNPROVIDEABLE', 'PARTITIONING_FAILED', 'DATA_FAILURE', 'STOPPED', 'COMPLETED', 'FAILED'}
        return last_message.updated_data.get('status', ':').split(':')[-1] in stop_steps

    def get_update_from_queue(self, job_id: str) -> UpdateMessage:
        if not self.is_following_updates(job_id):
            raise ValueError("{} is not following the exec updates of job {}".format(self.__class__.__name__, job_id))
        return await self._update_queues[job_id].get()

    def is_following_updates(self, job_id: str) -> bool:
        """
        Whether this client is currently following updates for the given job id.

        Parameters
        ----------
        job_id

        Returns
        -------
        bool
            Whether this client is currently following updates for the given job id.
        """
        return job_id in self._update_queues

    async def request_exec(self, request: Optional[NGENRequest] = None, *args, **kwargs) -> NGENRequestResponse:
        if request is None:
            request = self.build_message(*args, **kwargs)
        if request is None:
            msg = 'Cannot request exec in {} without message object or details'
            raise DmodRuntimeError(msg.format(self.__class__.__name__))
        await self._async_acquire_session_info()
        # TODO: make sure this function is implemented in a reasonable way
        return await self.async_make_request(request)


class DatasetClient(ABC):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_response = None

    def _parse_list_of_dataset_names_from_response(self, response: DatasetManagementResponse) -> List[str]:
        """
        Parse an includes list of dataset names from a received management response.

        Note that an unsuccessful response, or a response (of the correct type) that does not explicitly include the
        expected data attribute with dataset names, will result in an empty list being returned.  However, an unexpected
        type for the parameter will cause a ::class:`RuntimeError`.

        Parameters
        ----------
        response : DatasetManagementResponse
            The response message from which to parse dataset names.

        Returns
        -------
        List[str]
            The list of parsed dataset names.

        Raises
        -------
        RuntimeError
            Raised if the parameter is not a ::class:`DatasetManagementResponse` (or subtype) object.
        """
        if not isinstance(response, DatasetManagementResponse):
            msg = "Can't parse list of datasets from non-{} (received a {} object)"
            raise RuntimeError(msg.format(DatasetManagementResponse.__name__, response.__class__.__name__))
        # Consider these as valid cases, and treat them as just not listing any datasets
        elif not response.success or response.data is None or 'datasets' not in response.data:
            return []
        else:
            return response.data['datasets']

    @abstractmethod
    async def create_dataset(self, name: str, category: DataCategory, domain: DataDomain, **kwargs) -> bool:
        pass

    @abstractmethod
    async def delete_dataset(self, name: str, **kwargs) -> bool:
        pass

    @abstractmethod
    async def download_dataset(self, dataset_name: str, dest_dir: Path) -> bool:
        pass

    @abstractmethod
    async def download_from_dataset(self, dataset_name: str, item_name: str, dest: Path) -> bool:
        pass

    @abstractmethod
    async def list_datasets(self, category: Optional[DataCategory] = None) -> List[str]:
        pass

    @abstractmethod
    async def upload_to_dataset(self, dataset_name: str, paths: List[Path]) -> bool:
        pass


class DatasetInternalClient(DatasetClient, DataServiceClient):

    @classmethod
    def get_response_subtype(cls) -> Type[R]:
        return DatasetManagementResponse

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def create_dataset(self, name: str, category: DataCategory, domain: DataDomain, **kwargs) -> bool:
        # TODO: (later) consider also adding param for data to be added
        request = DatasetManagementMessage(action=ManagementAction.CREATE, domain=domain, dataset_name=name,
                                           category=category)
        self.last_response = await self.async_make_request(request)
        return self.last_response is not None and self.last_response.success

    async def delete_dataset(self, name: str, **kwargs) -> bool:
        request = DatasetManagementMessage(action=ManagementAction.DELETE, dataset_name=name)
        self.last_response = await self.async_make_request(request)
        return self.last_response is not None and self.last_response.success

    async def download_dataset(self, dataset_name: str, dest_dir: Path) -> bool:
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
        except:
            return False
        success = True
        query = DatasetQuery(query_type=QueryType.LIST_FILES)
        request = DatasetManagementMessage(action=ManagementAction.QUERY, dataset_name=dataset_name, query=query)
        self.last_response: DatasetManagementResponse = await self.async_make_request(request)
        # TODO: (later) need to formalize this a little better than just here (and whereever it is serialized)
        results = self.last_response.query_results
        for item, dest in [(f, dest_dir.joinpath(f)) for f in (results['files'] if 'files' in results else [])]:
            dest.parent.mkdir(exist_ok=True)
            success = success and await self.download_from_dataset(dataset_name=dataset_name, item_name=item, dest=dest)
        return success

    async def download_from_dataset(self, dataset_name: str, item_name: str, dest: Path) -> bool:
        if dest.exists():
            return False
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
        except:
            return False
        request = DatasetManagementMessage(action=ManagementAction.REQUEST_DATA, dataset_name=dataset_name,
                                           data_location=item_name)
        self.last_response: DatasetManagementResponse = await self.async_make_request(request)
        with dest.open('w') as file:
            for page in range(1, (self.last_response.total_pages + 1)):
                request = DatasetManagementMessage(action=ManagementAction.DOWNLOAD_DATA, dataset_name=dataset_name,
                                                   data_location=item_name, page=page)
                self.last_response: DatasetManagementResponse = await self.async_make_request(request)
                file.write(self.last_response.file_data)

    async def list_datasets(self, category: Optional[DataCategory] = None) -> List[str]:
        action = ManagementAction.LIST_ALL if category is None else ManagementAction.SEARCH
        request = DatasetManagementMessage(action=action, category=category)
        self.last_response = await self.async_make_request(request)
        return self._parse_list_of_dataset_names_from_response(self.last_response)

    async def upload_to_dataset(self, dataset_name: str, paths: List[Path]) -> bool:
        """
        Upload data a dataset.

        Parameters
        ----------
        dataset_name : str
            The name of the dataset.
        paths : List[Path]
            List of one or more paths of files to upload or directories containing files to upload.

        Returns
        -------
        bool
            Whether uploading was successful
        """
        # TODO: *********************************************
        raise NotImplementedError('Function upload_to_dataset not implemented')


class DatasetExternalClient(DatasetClient,
                            ExternalRequestClient[MaaSDatasetManagementMessage, MaaSDatasetManagementResponse]):
    """
    Client for authenticated communication sessions via ::class:`MaaSDatasetManagementMessage` instances.
    """

    # In particular needs - endpoint_uri: str, ssl_directory: Path
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cached_session_file = Path.home().joinpath('.dmod_client_session')

    def _acquire_session_info(self, use_current_values: bool = True, force_new: bool = False):
        """
        Attempt to set the session information properties needed to submit a maas request.

        Parameters
        ----------
        use_current_values : bool
            Whether to use currently held attribute values for session details, if already not None (disregarded if
            ``force_new`` is ``True``).
        force_new : bool
            Whether to force acquiring a new session, regardless of data available is available on an existing session.

        Returns
        -------
        bool
            whether session details were acquired and set successfully
        """
        #logger.info("{}._acquire_session_info:  getting session info".format(self.__class__.__name__)
        if not force_new and use_current_values and self._session_id and self._session_secret and self._session_created:
            #logger.info('Using previously acquired session details (new session not forced)')
            return True
        else:
            #logger.info("Session from JobRequestClient: force_new={}".format(force_new))
            tmp = self._acquire_new_session()
            #logger.info("Session Info Return: {}".format(tmp))
            return tmp

    async def _async_acquire_session_info(self, use_current_values: bool = True, force_new: bool = False):
        if use_current_values and not force_new and self._cached_session_file.exists():
            try:
                session_id, secret, created = self.parse_session_auth_text(self._cached_session_file.read_text())
                self._session_id = session_id
                self._session_secret = secret
                self._session_create = created
            except Exception as e:
                # TODO: consider logging; for now, just don't bail and move on to logic for new session
                pass

        if not force_new and use_current_values and self._session_id and self._session_secret and self._session_created:
            #logger.info('Using previously acquired session details (new session not forced)')
            return True
        else:
            # TODO: look at if there needs to be an addition to connection count, active connections, or something here
            tmp = await self._async_acquire_new_session(cached_session_file=self._cached_session_file)
            #logger.info("Session Info Return: {}".format(tmp))
            return tmp

    def _process_data_download_iteration(self, raw_received_data: str) -> Tuple[bool, Union[DataTransmitMessage, MaaSDatasetManagementResponse]]:
        """
        Helper function for processing a single iteration of the process of downloading data.

        Function process the received param, assumed to be received from the data service via a websocket connection,
        by loading it to JSON and attempting to deserialize it, first to a ::class:`MaaSDatasetManagementResponse`, then
        to a ::class:`DataTransmitMessage`.  If both fail, a ::class:`MaaSDatasetManagementResponse` indicating failure
        is created.

        To minimize later processing, a tuple is instead returned, containing not only the obtained message, but also
        whether it contains transmitted data.  Note that the obtained message is the second tuple item.

        Parameters
        ----------
        raw_received_data : str
            The raw message text data, received over a websocket connection to the data service, expected to be either a
            serialized ::class:`DataTransmitMessage` or ::class:`MaaSDatasetManagementResponse`.

        Returns
        -------
        Tuple[bool, Union[DataTransmitMessage, MaaSDatasetManagementResponse]]
            A tuple of whether the returned message for data transmission (i.e., contains data) and a returned message
            that either contains download data or is a management response indicating the download process is finished.
        """
        try:
            received_as_json = json.loads(raw_received_data)
        except:
            received_as_json = ''

        # Try to deserialize to this type 1st; if message is something else (e.g., more data), we'll get None,
        #   but if message deserializes to this kind of object, then this will be the last (and only) message
        received_message = MaaSDatasetManagementResponse.factory_init_from_deserialized_json(received_as_json)
        if received_message is not None:
            return False, received_message
        # If this wasn't deserialized to a response before, and wasn't to a data transmit just now, then bail
        received_message = DataTransmitMessage.factory_init_from_deserialized_json(received_as_json)
        if received_message is None:
            message_obj = MaaSDatasetManagementResponse(success=False, action=ManagementAction.REQUEST_DATA,
                                                        reason='Unparseable Message')
            return False, message_obj
        else:
            return True, received_message

    def _update_after_valid_response(self, response: MaaSDatasetManagementResponse):
        """
        Perform any required internal updates immediately after a request gets back a successful, valid response.

        This provides a way of extending the behavior of this type specifically regarding the ::method:make_maas_request
        function. Any updates specific to the type, which should be performed after a request receives back a valid,
        successful response object, can be implemented here.

        Parameters
        ----------
        response : MaaSDatasetManagementResponse
            The response triggering the update.

        See Also
        -------
        ::method:make_maas_request
        """
        # TODO: think about if anything is needed for this
        pass

    async def _upload_file(self, dataset_name: str, path: Path, item_name: str) -> bool:
        """
        Upload a single file to the dataset

        Parameters
        ----------
        dataset_name : str
            The name of the destination dataset.
        path : Path
            The path of the local file to upload.
        item_name : str
            The name of the destination dataset item in which to place the data.
        Returns
        -------
        bool
            Whether the data upload was successful.
        """
        await self._async_acquire_session_info()
        #raw_data = path.read_bytes()
        chunk_size = 1024
        message = MaaSDatasetManagementMessage(action=ManagementAction.ADD_DATA, dataset_name=dataset_name,
                                               session_secret=self.session_secret, data_location=item_name)
        async with websockets.connect(self.endpoint_uri, ssl=self.client_ssl_context) as websocket:
            with path.open() as file:
                raw_chunk = file.read(chunk_size)
                while True:
                    await websocket.send(str(message))
                    response_json = json.loads(await websocket.recv())
                    response = MaaSDatasetManagementResponse.factory_init_from_deserialized_json(response_json)
                    if response is not None:
                        self.last_response = response
                        return response.success
                    response = DataTransmitResponse.factory_init_from_deserialized_json(response_json)
                    if response is None:
                        return False
                    if not response.success:
                        self.last_response = response
                        return response.success
                    # If here, we must have gotten a transmit response indicating we can send more data, so prime the next
                    #   sending message for the start of the loop
                    next_chunk = file.read(chunk_size)
                    message = DataTransmitMessage(data=raw_chunk, series_uuid=response.series_uuid,
                                                  is_last=not bool(next_chunk))
                    raw_chunk = next_chunk

    async def _upload_dir(self, dataset_name: str, dir_path: Path, item_name_prefix: str = '') -> bool:
        """
        Upload the contents of a local directory to a dataset.

        Parameters
        ----------
        dataset_name : str
            The name of the dataset.
        dir_path : Path
            The path of the local directory containing data files to upload.
        item_name_prefix : str
            A prefix to append to the name of destination items (otherwise equal to the local data files basename), used
            to make recursive calls to this function on subdirectories and emulate the local directory structure.

        Returns
        -------
        bool
            Whether data upload was successful.
        """
        success = True
        for child in dir_path.iterdir():
            if child.is_dir():
                new_prefix = '{}{}/'.format(item_name_prefix, child.name)
                success = success and await self._upload_dir(dataset_name=dataset_name, dir_path=child,
                                                             item_name_prefix=new_prefix)
            else:
                success = success and await self._upload_file(dataset_name=dataset_name, path=child,
                                                              item_name='{}{}'.format(item_name_prefix, child.name))
        return success

    async def create_dataset(self, name: str, category: DataCategory, domain: DataDomain, **kwargs) -> bool:
        await self._async_acquire_session_info()
        # TODO: (later) consider also adding param for data to be added
        request = MaaSDatasetManagementMessage(session_secret=self.session_secret, action=ManagementAction.CREATE,
                                               domain=domain, dataset_name=name, category=category)
        self.last_response = await self.async_make_request(request)
        return self.last_response is not None and self.last_response.success

    async def delete_dataset(self, name: str, **kwargs) -> bool:
        await self._async_acquire_session_info()
        request = MaaSDatasetManagementMessage(session_secret=self.session_secret, action=ManagementAction.DELETE,
                                               dataset_name=name)
        self.last_response = await self.async_make_request(request)
        return self.last_response is not None and self.last_response.success

    async def download_dataset(self, dataset_name: str, dest_dir: Path) -> bool:
        await self._async_acquire_session_info()
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
        except:
            return False
        success = True
        query = DatasetQuery(query_type=QueryType.LIST_FILES)
        request = MaaSDatasetManagementMessage(action=ManagementAction.QUERY, dataset_name=dataset_name, query=query,
                                               session_secret=self.session_secret)
        self.last_response: MaaSDatasetManagementResponse = await self.async_make_request(request)
        for item, dest in [(filename, dest_dir.joinpath(filename)) for filename in self.last_response.query_results]:
            dest.parent.mkdir(exist_ok=True)
            success = success and await self.download_from_dataset(dataset_name=dataset_name, item_name=item, dest=dest)
        return success

    async def download_from_dataset(self, dataset_name: str, item_name: str, dest: Path) -> bool:
        await self._async_acquire_session_info()
        if dest.exists():
            return False
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
        except:
            return False

        request = MaaSDatasetManagementMessage(action=ManagementAction.REQUEST_DATA, dataset_name=dataset_name,
                                               session_secret=self.session_secret, data_location=item_name)
        async with websockets.connect(self.endpoint_uri, ssl=self.client_ssl_context) as websocket:
            # Do this once outside loop, so we don't open a file for writing to which nothing is written
            await websocket.send(str(request))
            has_data, message_object = self._process_data_download_iteration(await websocket.recv())
            if not has_data:
                return message_object

            # Here, we will have our first piece of data to write, so open file and start our loop
            with dest.open('w') as file:
                while True:
                    file.write(message_object.data)
                    # Do basically same as above, except here send message to acknowledge data just written was received
                    await websocket.send(str(DataTransmitResponse(success=True, reason='Data Received',
                                                                  series_uuid=message_object.series_uuid)))
                    has_data, message_object = self._process_data_download_iteration(await websocket.recv())
                    if not has_data:
                        return message_object

    async def list_datasets(self, category: Optional[DataCategory] = None) -> List[str]:
        await self._async_acquire_session_info()
        action = ManagementAction.LIST_ALL if category is None else ManagementAction.SEARCH
        request = MaaSDatasetManagementMessage(session_secret=self.session_secret, action=action, category=category)
        self.last_response = await self.async_make_request(request)
        return self._parse_list_of_dataset_names_from_response(self.last_response)

    async def upload_to_dataset(self, dataset_name: str, paths: List[Path]) -> bool:
        """
        Upload data a dataset.

        Parameters
        ----------
        dataset_name : str
            The name of the dataset.
        paths : List[Path]
            List of one or more paths of files to upload or directories containing files to upload.

        Returns
        -------
        bool
            Whether uploading was successful
        """
        # Don't do anything if any paths are bad
        if len([p for p in paths if not p.exists()]) > 0:
            raise RuntimeError('Upload failed due to invalid non-existing paths being received')

        success = True
        # For all individual files
        for p in paths:
            if p.is_file():
                success = success and await self._upload_file(dataset_name=dataset_name, path=p, item_name=p.name)
            else:
                success = success and await self._upload_dir(dataset_name=dataset_name, dir_path=p)
        return success

    @property
    def errors(self):
        # TODO: think about this more
        return self._errors

    @property
    def info(self):
        # TODO: think about this more
        return self._info

    @property
    def warnings(self):
        # TODO: think about this more
        return self._warnings
