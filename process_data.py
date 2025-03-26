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

    def kill_process_by_name(self, process_name, callback=None):
        """Kill all instances of a process by name"""
        def kill_process_thread():
            try:
                # Create a copy of the PIDs to avoid modification during iteration
                pids_to_kill = []
                with self.lock:
                    if process_name not in self.process_groups:
                        if callback:
                            callback(process_name, 0, "Process already terminated")
                        return
                    
                    pids_to_kill = self.process_groups[process_name]['pids'].copy()
                    
                if not pids_to_kill:
                    if callback:
                        callback(process_name, 0, "No running instances found")
                    return
                
                killed_count = 0
                for pid in pids_to_kill:
                    try:
                        # Don't use interval when getting process - it causes hanging
                        proc = psutil.Process(pid)
                        proc.terminate()  # Use terminate instead of kill for safer operation
                        
                        # Don't wait inside the loop - this was causing the hang
                        killed_count += 1
                        logger.info(f"Terminated process with PID {pid}")
                        
                    except psutil.NoSuchProcess:
                        logger.info(f"Process {pid} already gone")
                    except psutil.AccessDenied:
                        logger.warning(f"Access denied when killing process {pid}")
                    except Exception as e:
                        logger.error(f"Error killing {pid}: {str(e)}")
                
                # Report results
                if callback:
                    callback(process_name, killed_count, "Success" if killed_count > 0 else "Failed to kill any processes")
                
            except Exception as e:
                logger.error(f"Kill process thread error: {str(e)}")
                if callback:
                    callback(process_name, 0, f"Error: {str(e)}")
        
        # Start a thread to handle the killing
        kill_thread = threading.Thread(target=kill_process_thread, daemon=True)
        kill_thread.start()
        
    def get_filtered_processes(self, filter_text="", sort_column="Memory (MB)", sort_reverse=True):
        """Get filtered and sorted list of processes"""
        filtered_items = []
        with self.lock:
            for name, data in self.process_groups.items():
                if not filter_text or filter_text.lower() in name.lower():
                    # Make a copy to avoid reference issues
                    filtered_items.append((name, {
                        'memory': data['memory'],
                        'cpu': data['cpu'],
                        'status': data['status'],
                        'pids': len(data['pids']),
                        'start_time': data.get('start_time', 0)
                    }))
        
        # Sort the filtered items
        if sort_column == "Memory (MB)":
            filtered_items.sort(key=lambda x: x[1]['memory'], reverse=sort_reverse)
        elif sort_column == "CPU%":
            filtered_items.sort(key=lambda x: x[1]['cpu'], reverse=sort_reverse)
        elif sort_column == "Name":
            filtered_items.sort(key=lambda x: x[0].lower(), reverse=sort_reverse)
        elif sort_column == "Start Time":
            filtered_items.sort(key=lambda x: x[1]['start_time'], reverse=sort_reverse)
            
        return filtered_items
    
    def get_process_instances(self, name):
        """Get details about individual process instances"""
        # Check if we have cached data first
        if name in self.process_instances_cache and time.time() - self.process_instances_cache[name]['timestamp'] < 2:
            # Use cached data if less than 2 seconds old
            return self.process_instances_cache[name]['instances']
        
        # Otherwise collect fresh data
        instances = []
        try:
            # First get all potential PIDs to check
            with self.lock:
                if name in self.process_groups:
                    pids_to_check = self.process_groups[name]['pids'].copy()
                    # Get stored memory values if available for consistency
                    pid_memory = self.process_groups[name].get('pid_memory', {})
                else:
                    pids_to_check = []
                    pid_memory = {}
            
            # Collect all process names from system if needed
            if not pids_to_check:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.info['name'] == name:
                            pids_to_check.append(proc.info['pid'])
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            
            # Now process each PID
            for pid in pids_to_check:
                try:
                    proc = psutil.Process(pid)
                    
                    # Use stored memory value if available for consistency with main view
                    if pid in pid_memory:
                        mem_mb = pid_memory[pid]
                    else:
                        # Otherwise recalculate
                        try:
                            # Use private bytes if available (Windows)
                            if hasattr(proc.memory_info(), 'private'):
                                mem_mb = proc.memory_info().private / 1024**2
                            else:
                                # Fall back to RSS if private bytes not available
                                mem_mb = proc.memory_info().rss / 1024**2
                        except:
                            mem_mb = proc.memory_info().rss / 1024**2
                    
                    status = proc.status()
                    cpu_pct = proc.cpu_percent(interval=0.1)
                    
                    # Scale CPU percentage to match Task Manager display
                    cpu_count = psutil.cpu_count(logical=True)
                    if cpu_count > 0:
                        cpu_pct = min(cpu_pct / cpu_count, 100.0)
                    
                    instance = {
                        'pid': pid,
                        'memory': f"{mem_mb:.1f}",
                        'cpu': f"{cpu_pct:.1f}",
                        'status': status,
                        'tag': "high_mem" if mem_mb > 500 else ("high_cpu" if cpu_pct > 50 else "")
                    }
                    instances.append(instance)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            # Save to cache
            self.process_instances_cache[name] = {
                'timestamp': time.time(),
                'instances': instances
            }
            
        except Exception as e:
            logger.error(f"Instance retrieval error: {str(e)}")
            
        return instances
    
    def get_system_info(self):
        """Get system information"""
        try:
            cpu_count = psutil.cpu_count()
            
            # Get overall CPU usage - use interval for better accuracy
            # This matches Task Manager's measure more closely
            current_cpu = psutil.cpu_percent(interval=0.1)
            self.cpu_data_history.append(current_cpu)
            
            mem_total_gb = psutil.virtual_memory().total / (1024**3)
            
            # Add system uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_days = int(uptime_seconds // 86400)
            uptime_hours = int((uptime_seconds % 86400) // 3600)
            uptime_mins = int((uptime_seconds % 3600) // 60)
            
            uptime_str = f"{uptime_days}d {uptime_hours}h {uptime_mins}m"
            
            # Get memory usage
            mem = psutil.virtual_memory()
            total_phys_kb = mem.total / 1024
            avail_phys_kb = mem.available / 1024
            used_phys_kb = total_phys_kb - avail_phys_kb
            mem_percent = (used_phys_kb / total_phys_kb) * 100
            
            # Get disk usage
            disk_usage = []
            for disk in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(disk.mountpoint)
                    if usage.total > 0:  # Avoid division by zero
                        disk_usage.append({
                            'mountpoint': disk.mountpoint,
                            'percent': usage.percent,
                            'used': usage.used / (1024**3),  # in GB
                            'total': usage.total / (1024**3)  # in GB
                        })
                except (PermissionError, FileNotFoundError):
                    continue
            
            return {
                'cpu_count': cpu_count,
                'cpu_percent': current_cpu,
                'cpu_history': list(self.cpu_data_history),
                'memory_total': mem_total_gb,
                'uptime': uptime_str,
                'memory_percent': mem_percent,
                'disk_usage': disk_usage
            }
            
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            return None
    
    def shutdown(self):
        """Stop data collection"""
        self.running = False

            