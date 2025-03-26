"""
Real-Time Process Management System
----------------------------------
A system resource monitoring and process management application
that provides a detailed view of running processes and system resources,
including CPU usage, memory consumption, and disk utilization.

Authors: Kartik, Kanha, Manish
"""

import logging
from process_data import ProcessDataManager
from visualization import SystemVisualizer
from ui_manager import ProcessUI

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ProcessManager')

def main():
    """Main entry point for the application"""
    try:
        # Initialize the data manager
        logger.info("Initializing Process Data Manager")
        data_manager = ProcessDataManager()
        
        # Create the UI first (without showing it)
        logger.info("Creating UI")
        ui = ProcessUI(data_manager=data_manager)
        
        # Initialize and set up UI components first
        logger.info("Setting up UI")
        ui.setup_ui()
        
        # Create visualizer AFTER UI is set up so we can access main_frame
        logger.info("Creating System Visualizer")
        visualizer = SystemVisualizer(ui.main_frame)
        ui.visualizer = visualizer
        
        # Add visualizer's plot frame to UI
        ui.add_visualizer(visualizer)
        
        # Start the application
        logger.info("Starting application")
        ui.start_updates()
        ui.root.mainloop()
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
