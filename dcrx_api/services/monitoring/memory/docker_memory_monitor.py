import docker
import psutil
from dcrx_api.env import Env
from dcrx_api.services.jobs.queue import JobQueue
from dcrx_api.services.monitoring.base.monitor import BaseMonitor
from typing import List


class DockerMemoryMonitor(BaseMonitor):

    def __init__(
        self, 
        env: Env,
        queue: JobQueue
    ) -> None:
        super().__init__()
        self.total_memory = int(psutil.virtual_memory().total/10**6)
        self.docker_process_name = 'dockerd'
        self.docker_process_ids: List[int] = []
        self.client = docker.DockerClient(
            max_pool_size=env.DCRX_API_JOB_POOL_SIZE
        )

        self.queue = queue

        for proc in psutil.process_iter():
            if self.docker_process_name in proc.name():
                self.docker_process_ids.append(proc.pid)

    def get_percent_used(self, monitor_name) -> float:
        precentile_usage_metric = f'{monitor_name}_pct_usage'
        return self.active.get(precentile_usage_metric, 0)

    def update_monitor(self, monitor_name: str):

        total_active_images_memory = 0

        active_images = self.queue.active_images

        image_sizes: List[int] = []
        for active in active_images:
            if active is not None:
                image_sizes.append(
                    active.attrs.get('Size', 0)
                )
            
        total_active_images_memory = sum(image_sizes)


        process_memory_stats: List[float] = []

        for pid in self.docker_process_ids:

            try:

                process = psutil.Process(pid)
                mem_info = process.memory_info()

                process_memory_stats.append(
                    int(mem_info.rss/10**6)
                )

            except (psutil.NoSuchProcess, RuntimeError):
                pass

        total_memory_usage = sum(process_memory_stats) + total_active_images_memory

        self.active[monitor_name] = total_memory_usage

        precentile_usage_metric = f'{monitor_name}_pct_usage'
        self.active[precentile_usage_metric] = round(
            total_memory_usage/self.total_memory,
            3
        )
