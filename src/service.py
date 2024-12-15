import win32serviceutil
import win32event
import servicemanager
import logging
from watchdog.observers import Observer
from watchdog.observers.api import EventQueue
from watchdog.events import FileSystemEventHandler
import time

logging.basicConfig(
    level=logging.INFO,  # Set the logging level (e.g., DEBUG, INFO, WARNING)
    format="%(asctime)s - %(levelname)s - %(message)s"  # Define the log message format
)
class ArXivFileTagger(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.pending_crdownload_files = {}
        self.timeout_threshold = 1.0
    
    def on_created(self,event):
        if not event.is_directory and event.src_path.endswith('.crdownload'):
            self.pending_crdownload_files[event.src_path] = time.time()
    
    def on_moved(self, event):
        if not event.is_directory and event.src_path in self.pending_crdownload_files:
            self.download_complete_callback(event.dest_path)
            del self.pending_crdownload_files[event.src_path]

        
    def download_complete_callback(self,filepath):
        # TODO: Put the rename and move logic here
        logging.info(f'Download complete. Downloaded file path: {filepath}')

    def _cleanup_stale_crdownload_files(self):
        current_time = time.time()
        self.pending_crdownload_files = {
            path: timestamp
            for path, timestamp in self.pending_crdownload_files.items()
            if current_time - timestamp <= self.timeout_threshold
        }
            

class ArxivTaggingService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ArXivTaggingService"
    _svc_display_name = "ArXiv Tagger"
    _svc_description_ = "This service automatically renames and moves downloaded arxiv articles according to a schema of your choice."

    def __init__(self, args) -> None:
        super().__init__(args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        self.running = True
    
    def SvcDoRun(self):
        # Called when service starts
        servicemanager.LogInfoMsg(f"{self._svc_name_} - Service is starting...")
        self.main()

    def SvcStop(self):
        # Called when service stops
        pass

    
    def main(self) -> None:
        pass

if __name__ == "__main__":
    logging.info("app start")

    observer = Observer()
    handler=ArXivFileTagger()
    path = "C:\\Users\\Leems\\desktop"
    observer.schedule(event_handler=handler,path=path,recursive=False)
    
    logging.info(f'monitoring changes in dir {path}')
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()


    ## TODO: Handle the fact that downloads create tmp files and rename them.
