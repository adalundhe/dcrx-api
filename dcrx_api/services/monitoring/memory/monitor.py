import os
import psutil
from dcrx_api.services.monitoring.base.monitor import BaseMonitor


class MemoryMonitor(BaseMonitor):

    def __init__(self) -> None:
        super().__init__()
        self.total_memory = int(psutil.virtual_memory().total/10**6)
    
    def get_percent_used(self, monitor_name) -> float:
        precentile_usage_metric = f'{monitor_name}_pct_usage'
        return self.active.get(precentile_usage_metric, 0)

    def update_monitor(self, monitor_name: str):
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()

        memory_percent_used = int(mem_info.rss/10**6)

        self.active[monitor_name] = memory_percent_used

        precentile_usage_metric = f'{monitor_name}_pct_usage'
        self.active[precentile_usage_metric] = round(
            memory_percent_used/self.total_memory,
            3
        )