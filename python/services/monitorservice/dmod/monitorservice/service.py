from dmod.communication import SchedulerClient, WebSocketInterface
from dmod.monitor import QueMonitor
from dmod.scheduler import Job, JobStatus
from pathlib import Path
from typing import List, Union
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

import asyncio
import json
import logging

# TODO: improve logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler()]
)


class MonitorService(WebSocketInterface):

    def __init__(self, monitor: QueMonitor, scheduler_host: str, scheduler_port: Union[int, str],
                 scheduler_ssl_directory: Path, *args, **kwargs):
        """
        Initialize the WebSocketInterface with any user defined custom server config
        """
        super(WebSocketInterface).__init__(*args, **kwargs)
        self._monitor = monitor
        scheduler_uri = SchedulerClient.build_endpoint_uri(host=scheduler_host, port=scheduler_port)
        self._scheduler_client = SchedulerClient(endpoint_uri=scheduler_uri, ssl_directory=scheduler_ssl_directory)

    async def get_monitorable_jobs(self) -> List[Job]:
        """
        Get a list of all job objects in a status that makes them eligible to be monitored (i.e., something worth
        monitoring could happen to them).

        Returns
        -------
        List[Job]
            A list of all job objects in a status that makes them eligible to be monitored
        """
        # TODO: get all jobs that should be monitored
        monitorable_jobs = []
        # TODO: decide which statuses belong to this group
        # TODO: write unit test so that these statuses are handled, others explicitly defined are ignored, but any
        #  other unknowns fail test.
        return monitorable_jobs

    async def listener(self, websocket: WebSocketServerProtocol, path):
        """
        Process incoming messages via websocket.
        """
        try:
            message = await websocket.recv()
            logging.info(f"Monitor received message: {message}")
            data = json.loads(message)
            logging.info(f"Monitor messsage payload was: {data}")

            # TODO: implement some kind of logic to do something, probably depending on the particular type of message

            # TODO: implement logic to properly respond in various situations

        except TypeError as te:
            logging.error("Problem with object types when processing received message", te)
        except ConnectionClosed:
            logging.info("Connection Closed at Consumer")
        except asyncio.CancelledError:
            logging.info("Cancelling listener task")

    async def monitor_jobs(self):
        """
        Monitor the status of known executing jobs, ensuring that their status remains consistent with their actual,
        real-world state.
        """
        while True:
            monitorable_jobs = await self.get_monitorable_jobs()

            ### Collect jobs where state and status don't match
            # Dict of changed job status value (when different from expected/current), keyed by relevant job
            jobs_with_changed_status = {}
            for job in monitorable_jobs:
                # TODO: check job's real-world state
                actual_status = ''
                if job.status != actual_status:
                    jobs_with_changed_status[job] = actual_status
                pass

            # TODO: for every job where state and status don't match, send update through to JobManager via websocket

            # TODO: either sleep or await some event trigger that something in Docker has changed (if that is available)
            pass


if __name__ == '__main__':
    raise RuntimeError('Module {} called directly; use main package entrypoint instead')
