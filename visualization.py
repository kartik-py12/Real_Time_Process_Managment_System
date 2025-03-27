import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Wedge
from collections import deque
import logging
import tkinter as tk
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Visualization')

class SystemVisualizer:
    def __init__(self, master):
        self.master = master
        self.memory_data = deque(maxlen=60)  # Keep 60 data points for memory history
        self.cpu_data = deque(maxlen=10)     # Keep latest CPU readings
        self.update_interval = 1000  # Update every second (in ms)
        
        # Initialize plots
        self.setup_plots()
        
    def setup_plots(self):
        """Setup the matplotlib plots for CPU, memory and disk"""
        # Create a frame for the plots with proper background
        self.plot_frame = tk.Frame(self.master, bg="#2c2c2c")
        
        # Create the figure frame with fixed height to ensure visibility
        figure_frame = tk.Frame(self.plot_frame, bg="#2c2c2c", height=280)
        figure_frame.pack(fill="both", expand=True, pady=10)
        figure_frame.pack_propagate(False)  # Prevent resizing
        
        # Create two side-by-side frames with adjusted width ratio (55% left, 45% right)
        left_charts = tk.Frame(figure_frame, bg="#2c2c2c", width=550)
        left_charts.pack(side=tk.LEFT, fill="both", expand=True, padx=(10, 5))
        
        right_charts = tk.Frame(figure_frame, bg="#2c2c2c", width=450)
        right_charts.pack(side=tk.LEFT, fill="both", expand=True, padx=(5, 10))
        
        # Create frames for each chart within the left side
        mem_frame = tk.Frame(left_charts, bg="#2c2c2c", height=260)
        mem_frame.pack(fill="both", expand=True, pady=5)
        
        # Create frames for each chart within the right side with adjusted width ratio
        cpu_frame = tk.Frame(right_charts, bg="#2c2c2c", height=130, width=200)
        cpu_frame.pack(side=tk.LEFT, fill="both", expand=True, pady=5)
        
        disk_frame = tk.Frame(right_charts, bg="#2c2c2c", height=130, width=250)
        disk_frame.pack(side=tk.LEFT, fill="both", expand=True, pady=5)
        
        # Set up the style for the plots
        plt.style.use('dark_background')
        
        # Memory usage history plot - bar chart
        self.fig_mem_usage = plt.Figure(figsize=(6, 3.5), dpi=100)
        self.ax_mem_usage = self.fig_mem_usage.add_subplot(111)
        self.canvas_mem_usage = FigureCanvasTkAgg(self.fig_mem_usage, master=mem_frame)
        self.canvas_mem_usage.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # CPU usage gauge
        self.fig_cpu = plt.Figure(figsize=(3, 3.5), dpi=100)
        self.ax_cpu = self.fig_cpu.add_subplot(111, polar=True)
        self.canvas_cpu = FigureCanvasTkAgg(self.fig_cpu, master=cpu_frame)
        self.canvas_cpu.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # Disk usage pie chart - increased size and margins
        self.fig_disk = plt.Figure(figsize=(3.5, 3.5), dpi=100)
        self.ax_disk = self.fig_disk.add_subplot(111)
        self.canvas_disk = FigureCanvasTkAgg(self.fig_disk, master=disk_frame)
        self.canvas_disk.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)  # Increased padding
        
        # Initialize the data with zeros
        self.memory_data.extend([0] * 30)
        self.cpu_data.extend([0] * 5)
        
        # Initial plot update
        self.update_cpu_plot(0)
        self.update_memory_plot(0)
        self.update_disk_plot([])
        
    def initialize_memory_data(self, initial_value):
        """Initialize memory data with actual values"""
        self.memory_data.clear()
        self.memory_data.extend([initial_value] * 30)
        
    def initialize_cpu_data(self, initial_value):
        """Initialize CPU data with actual values"""
        self.cpu_data.clear()
        self.cpu_data.extend([initial_value] * 5)
        
    def update_cpu_plot(self, cpu_percent):
        """Update the CPU usage gauge chart"""
        try:
            # Keep track of CPU data
            self.cpu_data.append(cpu_percent)
            avg_cpu = sum(self.cpu_data) / len(self.cpu_data)
            
            # Clear the axis
            self.ax_cpu.clear()
            
            # Setup the gauge
            self.ax_cpu.set_theta_zero_location('N')  # 0 at the top
            self.ax_cpu.set_theta_direction(-1)  # clockwise
            
            # Remove radial labels and grid
            self.ax_cpu.set_rticks([])  # No radial ticks
            self.ax_cpu.grid(False)  # No grid
            
            # Set the limits for the gauge (0 to 100%)
            self.ax_cpu.set_ylim(0, 100)
            
            # Create background arc (gray)
            theta = np.linspace(0, 2*np.pi, 100)
            r = 90  # radius of arc
            self.ax_cpu.plot(theta, [r]*100, color='gray', alpha=0.3, linewidth=20)
            
            # Create foreground arc (colored based on CPU usage)
            end_angle = 2*np.pi * (avg_cpu / 100)
            theta = np.linspace(0, end_angle, 100)
            
            # Choose color based on CPU percentage (green<30%, yellow<70%, orange<90%, red>90%)
            if avg_cpu < 30:
                color = '#66ff66'  # green
            elif avg_cpu < 70:
                color = '#ffff66'  # yellow
            elif avg_cpu < 90:
                color = '#ffaa33'  # orange
            else:
                color = '#ff3333'  # red
                
            if len(theta) > 0:  # Avoid empty plot error
                self.ax_cpu.plot(theta, [r]*len(theta), color=color, linewidth=20)
            
            # Add CPU percentage text in the center
            self.ax_cpu.text(0, 0, f"{avg_cpu:.1f}%", 
                             horizontalalignment='center',
                             verticalalignment='center',
                             fontsize=14, fontweight='bold')
                             
            # Add "CPU" label
            self.ax_cpu.text(0, 40, "CPU", 
                             horizontalalignment='center',
                             verticalalignment='center',
                             fontsize=12)
                             
            # Remove all tick labels
            self.ax_cpu.set_xticklabels([])
            
            # Adjust margins
            self.fig_cpu.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
            
            # Force redraw
            self.canvas_cpu.draw()
            
        except Exception as e:
            logger.error(f"CPU plot update error: {e}")
            
    def update_memory_plot(self, memory_percent):
        """Update the memory usage history plot"""
        try:
            # Add new data point
            self.memory_data.append(memory_percent)
            
            # Clear the axis
            self.ax_mem_usage.clear()
            
            # Draw the bar chart
            bar_width = 0.8
            bar_positions = list(range(len(self.memory_data)))
            
            # Use gradient colors based on memory level
            colors = []
            for value in self.memory_data:
                if value < 30:
                    colors.append('#66b3ff')  # blue for low memory
                elif value < 70:
                    colors.append('#aa66ff')  # purple for medium memory
                else:
                    colors.append('#ff6666')  # red for high memory
            
            bars = self.ax_mem_usage.bar(bar_positions, list(self.memory_data), 
                                         width=bar_width, color=colors, alpha=0.7)
            
            # Add a line on top of the bars for trend visualization
            self.ax_mem_usage.plot(bar_positions, list(self.memory_data), 
                                 color='white', alpha=0.5, linewidth=1.5)
            
            # Configure the plot
            self.ax_mem_usage.set_ylim(0, 100)
            self.ax_mem_usage.set_title(f"Memory Usage: {memory_percent:.1f}%", fontsize=12)
            self.ax_mem_usage.set_facecolor('#2c2c2c')
            self.ax_mem_usage.grid(True, color='gray', linestyle='--', alpha=0.3)
            
            # Add time indicator
            self.ax_mem_usage.set_xlabel("Time (last 60 seconds)", fontsize=10)
            self.ax_mem_usage.set_xticks([0, len(self.memory_data)//2, len(self.memory_data)-1])
            self.ax_mem_usage.set_xticklabels(["-60s", "-30s", "now"], fontsize=8)
            
            # Add percentage marker on y-axis
            self.ax_mem_usage.set_ylabel("Memory %", fontsize=10)
            
            # Adjust margins
            self.fig_mem_usage.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.15)
            
            # Force redraw
            self.canvas_mem_usage.draw()
            
        except Exception as e:
            logger.error(f"Memory plot update error: {e}")
            
    def update_disk_plot(self, disk_usage):
        """Update the disk usage pie chart"""
        try:
            # Clear the axis
            self.ax_disk.clear()
            
            if disk_usage:
                # Use the first disk (usually C:) for the pie chart
                disk = disk_usage[0]
                used_gb = disk['used']
                total_gb = disk['total']
                free_gb = total_gb - used_gb
                
                # Create pie chart with better styling and increased size
                wedges, texts, autotexts = self.ax_disk.pie(
                    [disk['percent'], 100 - disk['percent']], 
                    colors=["#ff9999", "#99ff99"], 
                    startangle=90,
                    autopct="%1.1f%%",
                    textprops={'color': 'white', 'fontsize': 10, 'fontweight': 'bold'},  # Increased font size
                    wedgeprops={'linewidth': 1, 'edgecolor': '#2c2c2c'},
                    radius=0.8  # Slightly smaller radius for better fit
                )
                
                # Add title with improved visibility
                self.ax_disk.set_title(f"Disk Usage", fontsize=12, pad=10)
                
                # Add subtitle with more details but better formatting
                subtitle = f"{disk['mountpoint']}: {used_gb:.1f}GB / {total_gb:.1f}GB"
                self.ax_disk.text(0, -1.1, subtitle, 
                                 horizontalalignment='center', 
                                 verticalalignment='center',
                                 fontsize=9,
                                 color='white',
                                 fontweight='bold')
                
                # Add legend with better positioning
                self.ax_disk.legend(
                    [f"Used: {used_gb:.1f}GB", f"Free: {free_gb:.1f}GB"],
                    loc="upper center",
                    bbox_to_anchor=(0.5, 0),
                    fontsize=9,
                    frameon=False,
                    ncol=2
                )
                
                # Ensure text visibility
                for text in texts:
                    text.set_color('white')
                
                # Better margin adjustment for disk chart
                self.fig_disk.subplots_adjust(left=0.05, right=0.95, top=0.85, bottom=0.05)
                
            else:
                self.ax_disk.text(0.5, 0.5, "No disk data", 
                                 horizontalalignment='center', verticalalignment='center')
            
            # Force redraw
            self.canvas_disk.draw()
            
        except Exception as e:
            logger.error(f"Disk plot update error: {e}")
            
    def update_plots(self, system_info):
        """Update all plots based on system info"""
        if system_info:
            self.update_cpu_plot(system_info['cpu_percent'])
            self.update_memory_plot(system_info['memory_percent'])
            self.update_disk_plot(system_info['disk_usage'])
        
    def get_plot_frame(self):
        """Return the plot frame to be placed in the UI"""
        return self.plot_frame
