import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
import time
import threading
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('UIManager')

class ProcessUI:
    def __init__(self, data_manager=None, visualizer=None):
        self.data_manager = data_manager
        self.visualizer = visualizer
        self.running = True
        self.data_ready = False
        self.sort_column = "Memory (MB)"
        self.sort_reverse = True
        self.update_interval = 2000  # 2 seconds in milliseconds
        
    def setup_ui(self):
        """Setup the main UI components"""
        # Create main window
        self.root = ttkb.Window(themename="darkly")
        self.root.title("Real-Time Process Management System")
        self.root.geometry("1000x700")
        
        # Setup loading screen
        self.setup_loading_screen()
        
        # Setup main UI (initially hidden)
        self.setup_main_ui()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_loading_screen(self):
        """Setup the loading screen UI"""
        self.loading_frame = ttk.Frame(self.root)
        self.loading_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Add project title and attribution
        project_title = ttk.Label(self.loading_frame, 
                                text="Real-Time Process Management System", 
                                font=("Helvetica", 18, "bold"))
        project_title.pack(pady=(0, 5))
        
        # Add attribution
        attribution = ttk.Label(self.loading_frame, 
                              text="by Kartik, Kanha, Manish", 
                              font=("Helvetica", 12))
        attribution.pack(pady=(0, 30))
        
        loading_label = ttk.Label(self.loading_frame, text="Please wait, loading processes...", font=("Helvetica", 14))
        loading_label.pack(pady=10)
        
        # Use determinate progress bar
        self.progress = ttk.Progressbar(self.loading_frame, mode="determinate", length=300, bootstyle=SUCCESS)
        self.progress.pack(pady=10)
        
        data_source_label = ttk.Label(self.loading_frame, text="Monitoring system processes in real-time", 
                                     font=("Helvetica", 8), foreground="gray")
        data_source_label.pack(pady=(20, 0))
        
        # Start the progress animation
        self.update_progress()
        
    def update_progress(self, value=0):
        """Update the loading progress bar"""
        if value <= 100 and not self.data_ready:
            self.progress['value'] = value
            self.root.after(50, lambda: self.update_progress(value + 2))
        
    def setup_main_ui(self):
        """Setup the main UI components"""
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack_forget()  # Hide initially, will be shown after loading
        
        # System Info Frame
        self.info_frame = ttk.LabelFrame(self.main_frame, text="System Information", padding=10)
        self.info_frame.pack(pady=5, fill="x", padx=10)
        
        # Default system info (will be updated later)
        self.system_info_label = ttk.Label(self.info_frame, text="Loading system information...")
        self.system_info_label.pack()
        
        # Visualization frame with better spacing
        self.viz_container = ttk.LabelFrame(self.main_frame, text="System Resources", padding=(10, 10))
        self.viz_container.pack(pady=5, padx=10, fill="x")
        
        # Process table section with label - adjusted height for better proportions
        process_section = ttk.LabelFrame(self.main_frame, text="Running Processes", padding=(10, 5))
        process_section.pack(pady=5, padx=10, fill="both", expand=True)
        
        # Tree frame for process list - reduced height to give more space to visualizations
        tree_frame = ttk.Frame(process_section)
        tree_frame.pack(pady=5, fill="both", expand=True)
        
        # Create Treeview with further reduced height
        columns = ("Name", "Memory (MB)", "Status", "PIDs", "Uptime")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)  # Reduced from 15 to 12
        
        # Configure columns
        self.tree.heading("Name", text="Name", command=lambda: self.sort_by("Name", not self.sort_reverse))
        self.tree.heading("Memory (MB)", text="Memory (MB)", command=lambda: self.sort_by("Memory (MB)", not self.sort_reverse))
        self.tree.heading("Status", text="Status")
        self.tree.heading("PIDs", text="Count")
        self.tree.heading("Uptime", text="Uptime", command=lambda: self.sort_by("Start Time", not self.sort_reverse))
        
        self.tree.column("Name", width=250, anchor="w")
        self.tree.column("Memory (MB)", width=120, anchor="center")
        self.tree.column("Status", width=100, anchor="center")
        self.tree.column("PIDs", width=60, anchor="center")
        self.tree.column("Uptime", width=80, anchor="center")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        
        # Control frame
        control_frame = ttk.LabelFrame(self.main_frame, text="Controls", padding=10)
        control_frame.pack(pady=5, fill="x", padx=10)
        
        # Filter controls
        ttk.Label(control_frame, text="Search App Name:").grid(row=0, column=0, padx=5)
        self.app_filter_var = tk.StringVar()
        app_filter_entry = ttk.Entry(control_frame, textvariable=self.app_filter_var)
        app_filter_entry.grid(row=0, column=1, padx=5)
        app_filter_entry.bind("<Return>", self.filter_table)
        
        ttk.Button(control_frame, text="Search", command=self.filter_table, bootstyle=PRIMARY).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="Clear Search", command=self.clear_filter, bootstyle=SECONDARY).grid(row=0, column=3, padx=5)
        ttk.Button(control_frame, text="Kill Selected", command=self.kill_process, bootstyle=DANGER).grid(row=0, column=4, padx=5)
        
        # Sort buttons
        sort_frame = ttk.Frame(control_frame)
        sort_frame.grid(row=0, column=5, padx=5)
        ttk.Button(sort_frame, text="Mem ↓", command=lambda: self.sort_by("Memory (MB)", True), bootstyle=SECONDARY).pack(side=tk.LEFT, padx=2)
        ttk.Button(sort_frame, text="Mem ↑", command=lambda: self.sort_by("Memory (MB)", False), bootstyle=SECONDARY).pack(side=tk.LEFT, padx=2)
        ttk.Button(sort_frame, text="Name ↓", command=lambda: self.sort_by("Name", True), bootstyle=SECONDARY).pack(side=tk.LEFT, padx=2)
        ttk.Button(sort_frame, text="Name ↑", command=lambda: self.sort_by("Name", False), bootstyle=SECONDARY).pack(side=tk.LEFT, padx=2)
        
        # Bind events
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)
        
    def sort_by(self, col, reverse):
        """Sort the process table by column"""
        self.sort_column = col
        self.sort_reverse = reverse
        self.update_table()
        
    def filter_table(self, event=None):
        """Apply filter to the process table"""
        self.update_table()
        
    def clear_filter(self):
        """Clear the filter"""
        self.app_filter_var.set("")
        self.update_table()
        
    def kill_process(self):
        """Kill the selected process"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a process to kill.")
            return
        
        # Get the process name from the selected item
        name = self.tree.item(selected[0])['values'][0]
        logger.info(f"Attempting to kill process: {name}")
        
        # Use the data manager to kill the process
        if self.data_manager:
            self.data_manager.kill_process_by_name(name, self.report_kill_results)
            
    def report_kill_results(self, process_name, killed_count, message):
        """Report the results of killing a process"""
        try:
            if killed_count > 0:
                messagebox.showinfo("Success", f"Initiated termination of {killed_count} instances of {process_name}")
            else:
                messagebox.showwarning("Warning", f"{message}. Try running as administrator.")
        except Exception as e:
            logger.error(f"Error reporting kill results: {str(e)}")
        
        # Force an update of the table
        self.update_table()
        
    def on_double_click(self, event):
        """Handle double-click on a process"""
        item = self.tree.identify_row(event.y)
        if item:
            name = self.tree.item(item, "values")[0]
            self.show_instances(name)
            
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        selected = self.tree.identify_row(event.y)
        if selected:
            self.tree.selection_set(selected)
            menu = tk.Menu(self.root, tearoff=0)
            name = self.tree.item(selected, "values")[0]
            menu.add_command(label="Show Instances", command=lambda: self.show_instances(name))
            menu.add_command(label="Kill Process", command=self.kill_process)
            menu.post(event.x_root, event.y_root)
            
    def show_instances(self, name):
        """Show instances of a process"""
        if not name or not self.data_manager:
            return
            
        # Create a new window for showing instances
        instance_window = ttkb.Toplevel(self.root)
        instance_window.title(f"Instances of {name}")
        instance_window.geometry("700x400")  # Increased width for CPU column
        
        # Create a loading indicator
        loading_frame = ttk.Frame(instance_window)
        loading_frame.pack(fill="both", expand=True)
        ttk.Label(loading_frame, text="Loading process instances...", font=("Helvetica", 12)).pack(pady=20)
        progress = ttk.Progressbar(loading_frame, mode="indeterminate", length=300, bootstyle=INFO)
        progress.pack(pady=10)
        progress.start(10)
        
        # Create main content frame (hidden initially)
        content_frame = ttk.Frame(instance_window)
        
        # Create a treeview in the new window with CPU column
        columns = ("PID", "Memory (MB)", "CPU %", "Status")
        instance_tree = ttk.Treeview(content_frame, columns=columns, show="headings")
        
        for col in columns:
            instance_tree.heading(col, text=col)
            instance_tree.column(col, width=100, anchor="center")
        
        instance_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=instance_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        instance_tree.configure(yscrollcommand=scrollbar.set)
        
        # Add a refresh button
        refresh_button = ttk.Button(
            content_frame, 
            text="Refresh", 
            command=lambda: self.refresh_instances(name, instance_tree),
            bootstyle=PRIMARY
        )
        refresh_button.pack(pady=10)
        
        # Load instances in a separate thread to avoid blocking the UI
        def threaded_instance_load():
            self.refresh_instances(name, instance_tree)
            # Switch from loading screen to content
            loading_frame.pack_forget()
            content_frame.pack(fill="both", expand=True)
        
        # Start loading thread
        threading.Thread(target=threaded_instance_load, daemon=True).start()
            
    def refresh_instances(self, name, tree_widget):
        """Refresh process instances in the tree"""
        tree_widget.delete(*tree_widget.get_children())
        
        if not self.data_manager:
            return
            
        # Get instances from data manager
        instances = self.data_manager.get_process_instances(name)
        
        # Variables to track total memory
        total_memory = 0.0
        
        # Populate the tree
        for instance in instances:
            memory_value = float(instance['memory'])
            total_memory += memory_value
            
            # Add CPU column to values
            tree_widget.insert(
                "", "end", 
                values=(instance['pid'], instance['memory'], instance['cpu'], instance['status']),
                tags=(instance['tag'])
            )
        
        # Configure tags for highlighting
        tree_widget.tag_configure("high_mem", background="#ffcc99")
        tree_widget.tag_configure("high_cpu", background="#ff9999")
        
        # Add a summary row with total memory
        tree_widget.insert("", "end", values=("TOTAL", f"{total_memory:.1f}", "", ""), tags=("total_row"))
        tree_widget.tag_configure("total_row", background="#666666", foreground="white")
            
    def update_table(self):
        """Update the process table with current data"""
        if not self.data_ready or not self.data_manager:
            self.root.after(100, self.update_table)
            return
        
        try:
            # Get filtered processes from data manager
            filter_text = self.app_filter_var.get()
            filtered_items = self.data_manager.get_filtered_processes(
                filter_text, self.sort_column, self.sort_reverse)
            
            # Clear the tree
            self.tree.delete(*self.tree.get_children())
            
            # Insert the sorted and filtered items
            current_time = time.time()
            for i, (name, data) in enumerate(filtered_items):
                pid_count = data['pids']
                
                # Skip processes with no PIDs (may have terminated)
                if pid_count == 0 and data['status'] != 'Terminating':
                    continue
                
                # Calculate uptime if available
                uptime_str = ""
                if data['start_time'] > 0:
                    uptime_secs = current_time - data['start_time']
                    if uptime_secs < 60:
                        uptime_str = f"{int(uptime_secs)}s"
                    elif uptime_secs < 3600:
                        uptime_str = f"{int(uptime_secs/60)}m"
                    elif uptime_secs < 86400:
                        uptime_str = f"{int(uptime_secs/3600)}h"
                    else:
                        uptime_str = f"{int(uptime_secs/86400)}d"
                    
                self.tree.insert(
                    "", "end", 
                    iid=f"{name}_{i}", 
                    values=(name, f"{data['memory']:.1f}", data['status'], pid_count, uptime_str),
                    tags=("high_mem" if data['memory'] > 1000 else "")
                )
                
            # Configure tags for highlighting
            self.tree.tag_configure("high_mem", background="#ffcc99")
                
        except Exception as e:
            logger.error(f"Table update error: {str(e)}")
        
        # Schedule next update if application is still running
        if self.running:
            self.root.after(self.update_interval, self.update_table)
            
    def update_system_info(self):
        """Update the system information display"""
        if not self.data_manager:
            return
            
        # Get system info from data manager
        system_info = self.data_manager.get_system_info()
        if system_info:
            # Update the system info label
            system_info_text = f"CPU: {system_info['cpu_count']} cores | Memory: {system_info['memory_total']:.1f} GB | System Uptime: {system_info['uptime']}"
            self.system_info_label.config(text=system_info_text)
            
            # Update the visualizer if available
            if self.visualizer:
                self.visualizer.update_plots(system_info)
        
        # Schedule next update
        if self.running:
            self.root.after(self.update_interval, self.update_system_info)
            
    def start_updates(self):
        """Start updating the UI with system data"""
        # Start data manager if available
        if self.data_manager:
            self.data_manager.start_collection()
            
            # Check if data is ready and show main UI
            def check_data():
                if hasattr(self.data_manager, 'data_ready') and self.data_manager.data_ready:
                    self.data_ready = True
                    self.loading_frame.destroy()
                    self.main_frame.pack(fill="both", expand=True)
                    
                    # Initialize visualizer if available
                    if self.visualizer:
                        system_info = self.data_manager.get_system_info()
                        if system_info:
                            self.visualizer.initialize_memory_data(system_info['memory_percent'])
                    
                    # Start UI updates
                    self.update_table()
                    self.update_system_info()
                else:
                    self.root.after(100, check_data)
                    
            self.root.after(100, check_data)
            
    def run(self):
        """Start the application"""
        self.setup_ui()
        self.start_updates()
        self.root.mainloop()
        
    def on_closing(self):
        """Handle application shutdown"""
        self.running = False
        # Shut down data manager if available
        if self.data_manager:
            self.data_manager.shutdown()
        logger.info("Shutting down application")
        self.root.destroy()
        
    def add_visualizer(self, visualizer):
        """Add the visualizer to the UI after it has been created"""
        if visualizer:
            plot_frame = visualizer.get_plot_frame()
            if plot_frame:
                # Add visualization frame to container
                plot_frame.pack(in_=self.viz_container, fill="both", expand=True)
