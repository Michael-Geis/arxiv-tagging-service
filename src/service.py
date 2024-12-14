import win32serviceutil
import win32event
import servicemanager
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

logging.basicConfig(
    level=logging.INFO,  # Set the logging level (e.g., DEBUG, INFO, WARNING)
    format="%(asctime)s - %(levelname)s - %(message)s"  # Define the log message format
)
class ArXivPaperHandler(FileSystemEventHandler):

    def on_created(self, event):
        logging.info(f"file created: {event.src_path}")

    def on_moved(self, event):
        logging.info(f"file moved from {event.src_path} to {event.dest_path}")

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
    handler=ArXivPaperHandler()
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
