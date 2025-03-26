import psutil
import time
import logging
from collections import defaultdict, deque
import threading

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ProcessData')

class ProcessDataManager:
    def __init__(self, update_interval=2):
        self.running = True
        self.process_groups = defaultdict(lambda: {'pids': [], 'memory': 0.0, 'cpu': 0.0, 'status': 'Running'})
        self.lock = threading.Lock()
        self.data_ready = False
        self.update_interval = update_interval
        self.process_instances_cache = {}
        self.cpu_data_history = deque(maxlen=60)  # Store CPU history
        
    def start_collection(self):
        """Start the data collection in a separate thread"""
        threading.Thread(target=self.collect_data, daemon=True).start()
        
    def collect_data(self):
        """Continuously collect process data"""
        # Initial data collection
        self.update_process_data()
        time.sleep(1.5)  # Ensure loading screen is visible for a moment
        self.data_ready = True
        
        # Continue collecting data at regular intervals
        while self.running:
            try:
                self.update_process_data()
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Data collection loop error: {str(e)}")
                time.sleep(1)  # Shorter interval on error
                
    def update_process_data(self):
        """Update process data from system"""
        temp_groups = defaultdict(lambda: {'pids': [], 'memory': 0.0, 'cpu': 0.0, 'status': 'Running'})
        
        try:
            # Get system CPU usage with a shorter interval for better accuracy
            # Task Manager uses a different algorithm - we'll try to get closer to it
            system_cpu = psutil.cpu_percent(interval=0.2)
            
            # Save to history for visualization
            self.cpu_data_history.append(system_cpu)
            
            # Process information collection
            cpu_count = psutil.cpu_count(logical=True)  # Get number of logical processors
            
            # Collect process information
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'exe', 'status', 'create_time', 'cpu_percent']):
                try:
                    proc_info = proc.info
                    if not proc_info['exe'] or "System" in proc_info['name'] or proc_info['name'].startswith("svchost"):
                        continue
                    
                    pid = proc_info['pid']
                    name = proc_info['name'] or "Unknown"
                    
                    # Get memory info - use private working set (same as Task Manager)
                    # On Windows, wset is closer to Task Manager's "Memory (private working set)"
                    if proc_info['memory_info']:
                        try:
                            # Use private bytes if available (Windows)
                            if hasattr(proc_info['memory_info'], 'private'):
                                mem_mb = proc_info['memory_info'].private / 1024**2
                            else:
                                # Fall back to RSS if private bytes not available
                                mem_mb = proc_info['memory_info'].rss / 1024**2
                        except:
                            mem_mb = proc_info['memory_info'].rss / 1024**2
                    else:
                        mem_mb = 0
                    
                    status = proc_info['status'] or "Running"
                    
                    # Get CPU usage - scale it to represent absolute percentage of total CPU
                    # to make it more similar to Task Manager
                    cpu_usage = proc_info.get('cpu_percent', 0)
                    
                    # Adjust CPU usage calculation to better match Task Manager on multi-core systems
                    # Task Manager shows % of one CPU core, so scale accordingly
                    if cpu_count > 0:
                        cpu_usage = min(cpu_usage / cpu_count, 100.0)
                    
                    # Store data in the temporary groups dictionary
                    temp_groups[name]['pids'].append(pid)
                    temp_groups[name]['memory'] += mem_mb
                    temp_groups[name]['cpu'] += cpu_usage  # Aggregate CPU usage across instances
                    temp_groups[name]['status'] = status
                    
                    # Store PID-specific memory for accurate instance viewing
                    if 'pid_memory' not in temp_groups[name]:
                        temp_groups[name]['pid_memory'] = {}
                    temp_groups[name]['pid_memory'][pid] = mem_mb
                    
                    # Add uptime information if available
                    if 'create_time' in proc_info and proc_info['create_time']:
                        if 'start_time' not in temp_groups[name]:
                            temp_groups[name]['start_time'] = proc_info['create_time']
                        else:
                            # Use the oldest start time for multiple instances
                            temp_groups[name]['start_time'] = min(temp_groups[name]['start_time'], proc_info['create_time'])
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            logger.error(f"Process iteration error: {str(e)}")
        
        # Update the global process_groups dictionary with the lock
        try:
            with self.lock:
                self.process_groups.clear()
                self.process_groups.update(temp_groups)
        except Exception as e:
            logger.error(f"Error updating process groups: {str(e)}")
            