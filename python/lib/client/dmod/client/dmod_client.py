import logging

from dmod.communication import UpdateMessage
from dmod.core.execution import AllocationParadigm
from dmod.core.exception import DmodRuntimeError
from dmod.core.meta_data import DataCategory, DataDomain, DataFormat, DiscreteRestriction, TimeRange
from dmod.core.serializable import BasicResultIndicator, ResultIndicator
from .request_clients import DatasetClient, DatasetExternalClient, DatasetInternalClient, FollowableClient, \
    NgenRequestClient
from .client_config import YamlClientConfig
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import asyncio
import uuid


class DmodClient:

    def __init__(self, client_config: YamlClientConfig, bypass_request_service: bool = False, *args, **kwargs):
        self._client_config = client_config
        self._dataset_client = None
        self._ngen_client = None
        self._bypass_request_service = bypass_request_service
        self._followed_jobs: Dict[str, Set[uuid.UUID]] = dict()
        """ Job id keyed to sets of registered update queue ids. """
        self._job_update_queues: Dict[uuid.UUID, asyncio.Queue[UpdateMessage]] = dict()
        """ Update queue ids to update queues for updates on jobs that are being followed. """

    @property
    def client_config(self):
        return self._client_config

    async def create_dataset(self, dataset_name: str, category: DataCategory, domain: Optional[DataDomain] = None,
                             **kwargs) -> bool:
        """
        Create a dataset from the given parameters.

        Note that despite the type hinting, ``domain`` is only semi-optional, as a domain is required to create a
        dataset. However, if a ``data_format`` keyword arg provides a ::class:`DataFormat` value, then a minimal
        ::class:`DataDomain` object can be generated and used.

        Additionally, ``continuous_restrictions`` and ``discrete_restrictions`` keyword args are used if present for
        creating the domain when necessary.  If neither are provided, the generated domain will have a minimal discrete
        restriction created for "all values" (i.e., an empty list) of the first index variable of the provided
        ::class:`DataFormat`.

        In the event neither a domain not a data format is provided, a ::class:`ValueError` is raised.

        Additionally, keyword arguments are forwarded in the call to the ::attribute:`dataset_client` property's
        ::method:`DatasetClient.create_dataset` function.  This includes the aforementioned kwargs for a creating a
        default ::class:`DataDomain`, but only if they are otherwise ignored because a valid domain arg was provided.

        Parameters
        ----------
        dataset_name : str
            The name of the dataset.
        category : DataCategory
            The dataset category.
        domain : Optional[DataDomain]
            The semi-optional (depending on keyword args) domain for the dataset.
        kwargs
            Other optional keyword args.

        Keyword Args
        ----------
        data_format : DataFormat
            An optional data format, used if no ``domain`` is provided
        continuous_restrictions : List[ContinuousRestrictions]
            An optional list of continuous domain restrictions, used if no ``domain`` is provided
        discrete_restrictions : List[DiscreteRestrictions]
            An optional list of discrete domain restrictions, used if no ``domain`` is provided

        Returns
        -------
        bool
            Whether creation was successful.
        """
        # If a domain wasn't passed, generate one from the kwargs, or raise and exception if we can't
        if domain is None:
            data_format = kwargs.pop('data_format', None)
            if data_format is None:
                msg = "Client can't create dataset with `None` for {}, nor generate a default {} without a provided {}"
                raise ValueError(msg.format(DataDomain.__name__, DataDomain.__name__, DataFormat.__name__))
            print_msg = "INFO: no {} provided; dataset will be created with a basic default domain using format {}"
            print(print_msg.format(DataDomain.__name__, data_format.name))
            # If neither provided, bootstrap a basic restriction on the first index variable in the data format
            if not ('discrete_restrictions' in kwargs or 'continuous_restrictions' in kwargs):
                c_restricts = None
                d_restricts = [DiscreteRestriction(variable=data_format.indices[0], values=[])]
            # If at least one is provided, use whatever was passed, and fallback to None for the other if needed
            else:
                c_restricts = list(kwargs.pop('continuous_restrictions')) if 'continuous_restrictions' in kwargs else []
                d_restricts = list(kwargs.pop('discrete_restrictions')) if 'discrete_restrictions' in kwargs else []
            domain = DataDomain(data_format=data_format, continuous_restrictions=c_restricts,
                                discrete_restrictions=d_restricts)
        # Finally, ask the client to create the dataset, passing the details
        return await self.dataset_client.create_dataset(dataset_name, category, domain, **kwargs)

    @property
    def dataset_client(self) -> DatasetClient:
        if self._dataset_client is None:
            if self._bypass_request_service:
                if self.client_config.dataservice_endpoint_uri is None:
                    raise RuntimeError("Cannot bypass request service without data service config details")
                self._dataset_client = DatasetInternalClient(self.client_config.dataservice_endpoint_uri,
                                                             self.client_config.dataservice_ssl_dir)
            else:
                self._dataset_client = DatasetExternalClient(self.requests_endpoint_uri, self.requests_ssl_dir)
        return self._dataset_client

    @property
    def ngen_request_client(self) -> NgenRequestClient:
        if self._ngen_client is None:
            self._ngen_client = NgenRequestClient(self.requests_endpoint_uri, self.requests_ssl_dir)
        return self._ngen_client

    async def delete_dataset(self, dataset_name: str, **kwargs):
        return await self.dataset_client.delete_dataset(dataset_name, **kwargs)

    async def download_dataset(self, dataset_name: str, dest_dir: Path) -> bool:
        return await self.dataset_client.download_dataset(dataset_name=dataset_name, dest_dir=dest_dir)

    async def download_from_dataset(self, dataset_name: str, item_name: str, dest: Path) -> bool:
        return await self.dataset_client.download_from_dataset(dataset_name=dataset_name, item_name=item_name,
                                                               dest=dest)

    async def get_followed_update(self, unique_queue_id: uuid.UUID) -> UpdateMessage:
        """
        Get the next queued update message in the identified queue, or await one to be received.

        The unique id must have come from registering to follow updates for a particular job through
        ::method:`register_follow_updates`.

        Parameters
        ----------
        unique_queue_id : uuid.UUID
            The unique id for the update queue to listen through, received when registering for updates for a job.

        Returns
        -------
        UpdateMessage
            The next available update, either immediately if any are queued, or once the next one is received.
        See Also
        -------
        queue_updates
        register_follow_updates
        """
        if unique_queue_id not in self._job_update_queues:
            raise DmodRuntimeError("Unrecognized update queue identifier to follow: {}".format(str(unique_queue_id)))
        return await self._job_update_queues[unique_queue_id].get()

    async def list_datasets(self, category: Optional[DataCategory] = None):
        return await self.dataset_client.list_datasets(category)

    async def request_job_info(self, job_id: str, *args, **kwargs) -> dict:
        """
        Request the full state of the provided job, formatted as a JSON dictionary.

        Parameters
        ----------
        job_id : str
            The id of the job in question.
        args
            (Unused) variable positional args.
        kwargs
            (Unused) variable keyword args.

        Returns
        -------
        dict
            The full state of the provided job, formatted as a JSON dictionary.
        """
        # TODO: implement
        raise NotImplementedError('{} function "request_job_info" not implemented yet'.format(self.__class__.__name__))

    async def request_job_release(self, job_id: str, *args, **kwargs) -> bool:
        """
        Request the allocated resources for the provided job be released.

        Parameters
        ----------
        job_id : str
            The id of the job in question.
        args
            (Unused) variable positional args.
        kwargs
            (Unused) variable keyword args.

        Returns
        -------
        bool
            Whether there had been allocated resources for the job, all of which are now released.
        """
        # TODO: implement
        raise NotImplementedError('{} function "request_job_release" not implemented yet'.format(self.__class__.__name__))

    async def request_job_status(self, job_id: str, *args, **kwargs) -> str:
        """
        Request the status of the provided job, represented in string form.

        Parameters
        ----------
        job_id : str
            The id of the job in question.
        args
            (Unused) variable positional args.
        kwargs
            (Unused) variable keyword args.

        Returns
        -------
        str
            The status of the provided job, represented in string form.
        """
        # TODO: implement
        raise NotImplementedError('{} function "request_job_status" not implemented yet'.format(self.__class__.__name__))

    async def request_job_stop(self, job_id: str, *args, **kwargs) -> bool:
        """
        Request the provided job be stopped; i.e., transitioned to the ``STOPPED`` exec step.

        Parameters
        ----------
        job_id : str
            The id of the job in question.
        args
            (Unused) variable positional args.
        kwargs
            (Unused) variable keyword args.

        Returns
        -------
        bool
            Whether the job was stopped as requested.
        """
        # TODO: implement
        raise NotImplementedError('{} function "request_job_stop" not implemented yet'.format(self.__class__.__name__))

    async def request_jobs_list(self, jobs_list_active_only: bool, *args, **kwargs) -> List[str]:
        """
        Request a list of ids of existing jobs.

        Parameters
        ----------
        jobs_list_active_only : bool
            Whether to exclusively include jobs with "active" status values.
        args
            (Unused) variable positional args.
        kwargs
            (Unused) variable keyword args.

        Returns
        -------
        List[str]
            A list of ids of existing jobs.
        """
        # TODO: implement
        raise NotImplementedError('{} function "request_jobs_list" not implemented yet'.format(self.__class__.__name__))

    @property
    def requests_endpoint_uri(self) -> str:
        return self.client_config.requests_endpoint_uri

    @property
    def requests_ssl_dir(self) -> Path:
        return self.client_config.requests_ssl_dir

    def register_follow_updates(self, job_id: str) -> uuid.UUID:
        """
        Register to follow updates for a running job.

        Parameters
        ----------
        job_id : str
            The job id of interest.

        Returns
        -------
        uuid.UUID
            The unique queue id of the queue from which this job's followed updates can be retrieved.

        See Also
        -------
        queue_updates
        get_followed_update
        unregister_follow_updates
        """
        if job_id not in self._followed_jobs:
            raise DmodRuntimeError("Can't register {} to follow unknown job {}".format(self.__class__.__name__, job_id))
        unique_queue_id = uuid.uuid4()
        self._followed_jobs[job_id].add(unique_queue_id)
        self._job_update_queues[unique_queue_id] = asyncio.Queue()
        return unique_queue_id

    async def submit_ngen_request(self, start: datetime, end: datetime, hydrofabric_data_id: str, hydrofabric_uid: str,
                                  cpu_count: int, realization_cfg_data_id: str, bmi_cfg_data_id: str,
                                  partition_cfg_data_id: Optional[str] = None, cat_ids: Optional[List[str]] = None,
                                  allocation_paradigm: Optional[AllocationParadigm] = None, *args,
                                  **kwargs) -> ResultIndicator:
        # TODO: document this keyword arg
        follow_locally = kwargs.get('follow_updates_locally', False)
        time_range = TimeRange(begin=start, end=end)
        request_obj = await self.ngen_request_client.build_message(time_range, hydrofabric_data_id, hydrofabric_uid,
                                                                   cpu_count, realization_cfg_data_id, bmi_cfg_data_id,
                                                                   partition_cfg_data_id, cat_ids, allocation_paradigm)
        # Create runtime context to make sure the client's connection is in place
        with self.ngen_request_client:
            job_response = await self.ngen_request_client.request_exec(request=request_obj)
            if not job_response.success:
                return job_response
            job_id = job_response.job_id
            logging.info('Received successful response from job request, with job id {}'.format(job_id))
            # Prepare the set of update queues following updates of this job
            self._followed_jobs[job_id] = set()
            # Optionally, set up a queue for this function to also read and print from
            if follow_locally:
                unique_queue_id = self.register_follow_updates(job_id)
            try:
                # Create async tasks to follow updates within the request client and here
                client_updates_task = asyncio.create_task(self.ngen_request_client.follow_exec(job_id))
                follow_updates_task = asyncio.create_task(self.queue_updates(job_id, self.ngen_request_client))
                # Output updates, if locally we are supposed to and they could still be coming in
                while follow_locally and self.ngen_request_client.is_following_updates(job_id):
                    logging.info(str(await self._job_update_queues[unique_queue_id].get()))
                # Await the completion of the async tasks (i.e., the client following updates) before proceeding
                await client_updates_task
                await follow_updates_task
                # Return the previously received job request response
                return job_response
            except Exception as e:
                msg = 'Job {} successfully requested, but encountered {} while following status updates ({})'
                return BasicResultIndicator(success=False, reason='Encountered {} Following Updates',
                                            message=msg.format(job_id, e.__class__.__name__, str(e)))
            finally:
                self.unregister_follow_updates(job_id=job_id,
                                               unique_queue_id=unique_queue_id if follow_locally else uuid.uuid4())

    def print_config(self):
        print(self.client_config.config_file.read_text())

    async def queue_updates(self, job_id: str, client: FollowableClient):
        """
        Async function for adding updates from a followable client to this instance's update queues.

        Parameters
        ----------
        job_id : str
            The unique id for the job for which updates should be queue.
        client : FollowableClient
            The client through which to get updates, which itself is expected to be following updates.
        """
        while client.is_following_updates(job_id=job_id) and self._followed_jobs.get(job_id):
            update_object = await client.get_update_from_queue(job_id=job_id)
            if job_id in self._followed_jobs:
                for queue_id, update_queue in self._job_update_queues.items():
                    await update_queue.put(update_object)

    def unregister_follow_updates(self, job_id: str, unique_queue_id: uuid.UUID):
        """
        Unregister to stop following updates for a running job.

        Note that parameter values not found to be registered or expected - an unrecognized ``job_id`` results in steps
        being skipped but no errors being thrown.  I.e., it is safe to unregister bogus values.

        Parameters
        ----------
        job_id : str
            The job id for which to unregister.
        unique_queue_id : uuid.UUID
            The id of the update queue to deregister and remove.

        Returns
        -------
        uuid.UUID
            The unique queue id of the queue from which this job's followed updates can be retrieved.

        See Also
        -------
        queue_updates
        get_followed_update
        unregister_follow_updates
        """
        if unique_queue_id in self._job_update_queues:
            self._job_update_queues.pop(unique_queue_id)

        if job_id in self._followed_jobs:
            if unique_queue_id in self._followed_jobs[job_id]:
                self._followed_jobs[job_id].remove(unique_queue_id)
            if len(self._followed_jobs[job_id]) == 0:
                self._followed_jobs.pop(job_id)

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
        return await self.dataset_client.upload_to_dataset(dataset_name, paths)

    def validate_config(self):
        # TODO:
        raise NotImplementedError("Function validate_config not yet implemented")
