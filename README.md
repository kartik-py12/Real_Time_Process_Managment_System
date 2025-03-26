# Real-Time Process Management System

A modern system monitoring and management tool that provides comprehensive real-time insights into running processes on your Windows system. Built with Python and featuring a sleek dark theme UI, this application offers detailed resource usage monitoring and process control capabilities.

## Features

- **Real-time Process Monitoring**: Track all running processes with continuously updating information
- **CPU Usage Visualization**: Monitor system CPU utilization with an intuitive gauge chart
- **Memory Usage Analysis**: View memory consumption with real-time historical graphs
- **Disk Space Visualization**: Monitor disk usage with intuitive pie charts
- **Process Management**: Terminate processes or view detailed instance information
- **Efficient Search & Filtering**: Quickly locate specific applications with instant filtering
- **Resource Usage Highlighting**: Easily identify high memory/CPU-consuming processes
- **Process Uptime Tracking**: See how long each process has been running
- **Multi-instance Support**: View and manage multiple instances of the same process
- **Responsive User Interface**: Clean, modern dark-themed interface built with ttkbootstrap

## Project Architecture

The application uses a modular architecture with three main components:

1. **Process Data Module** (`process_data.py`)
   - Collects system process data using the psutil library
   - Manages process information in a thread-safe manner
   - Provides accurate memory and CPU usage tracking
   - Handles process termination and detailed information retrieval

2. **Visualization Module** (`visualization.py`)
   - Renders real-time memory usage history using matplotlib
   - Displays CPU utilization with a color-coded gauge chart
   - Creates disk usage pie charts with detailed information
   - Updates visualizations on fixed intervals for smooth transitions

3. **User Interface Module** (`ui_manager.py`)
   - Builds the application interface with tkinter and ttkbootstrap
   - Manages user interactions and event handling
   - Creates responsive layouts for optimal user experience
   - Provides search, filtering, and sorting capabilities

4. **Main Application** (`main.py`)
   - Initializes and connects all modules
   - Manages the application lifecycle
   - Provides the entry point for the application

## System Requirements

- Windows 10/11
- Python 3.7 or higher
- Minimum 4GB RAM recommended
- 50MB disk space for installation

## Dependencies

- **psutil**: System information and process management
- **matplotlib**: Data visualization and graphing
- **ttkbootstrap**: Modern UI theming for tkinter
- **Pillow**: Image support for matplotlib
- **numpy**: Required for advanced visualization calculations

## Installation

1. Clone this repository or download the source code
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python main.py
   ```

## Usage Guide

- **Viewing Processes**: The main window shows all running processes with memory usage details
- **Sorting**: Click any column header to sort processes by that attribute
- **Filtering**: Enter text in the search box to find specific applications
- **Process Details**: Double-click any process to see all instances with CPU and memory usage
- **Terminating Processes**: Select a process and click "Kill Selected" or use the right-click menu
- **Monitoring Resources**: View real-time CPU, memory and disk usage in the graphs section

## Technical Notes

### CPU Measurement

The application's CPU usage measurements may differ from Windows Task Manager due to several technical factors:

1. **Sampling Rate Differences**: Task Manager uses a variable sampling algorithm that adjusts based on CPU activity levels, while our application uses fixed interval sampling through psutil.

2. **Kernel vs. User-Space Measurement**: Task Manager has privileged access to kernel-level CPU accounting via the Windows Management Instrumentation (WMI) subsystem, whereas psutil operates primarily in user-space.

3. **CPU Time Accounting Models**: The Windows kernel uses different CPU time accounting models for its internal tools versus what it exposes through public APIs.

4. **CPU Throttling and Frequency Scaling**: Modern CPUs implement dynamic frequency scaling which can cause fluctuations in how CPU percentage is calculated.

## Development

The application is structured for easy extension:

- Add new metrics by extending the `ProcessDataManager` class
- Create additional visualizations by adding to the `SystemVisualizer` class
- Enhance the UI by modifying the `ProcessUI` class

## Contributors

- **Kartik**: Lead developer, core architecture and data collection systems
- **Manish**: Process management and user interface implementation
- **Kanha**: Integration, testing, and documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.
