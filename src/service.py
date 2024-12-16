import win32serviceutil
import win32event
import servicemanager
import logging
from watchdog.observers import Observer
from watchdog.observers.api import EventQueue
from watchdog.events import FileSystemEventHandler
import os
import shutil
import time
from main import get_arxiv_metadata
import arxiv

logging.basicConfig(
    level=logging.INFO,  # Set the logging level (e.g., DEBUG, INFO, WARNING)
    format="%(asctime)s - %(levelname)s - %(message)s"  # Define the log message format
)

class ArXivTagger:
    
    def __init__(self,destination_dir):
        self.destination_dir = destination_dir
        if not os.path.exists(self.destination_dir):
            logging.info(f'destination directory {destination_dir} not found, creating it instead.')
            os.makedirs(destination_dir)
        else:
            logging.info(f'destination directory {destination_dir} found.')
    
    def rename(self,source_path,metadata):

        new_basename = metadata['title'].lower().replace(' ','_')
        target_path = os.path.join(self.destination_dir,f'{new_basename}.pdf')
        if os.path.exists(source_path):
            shutil.move(source_path,target_path)
            logging.info(f'renamed {source_path} to {target_path}.')
            return target_path
        else:
            raise FileNotFoundError('e')
        

class FileDownloadHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.pending_crdownload_files = {}
        self.timeout_threshold = 1.0
        self.client = arxiv.Client()
        self.tagger = ArXivTagger(destination_dir='C:\\Users\\Leems\\Desktop\\test-dir')
    
    def on_created(self,event):
        if not event.is_directory and event.src_path.endswith('.crdownload'):
            self.pending_crdownload_files[event.src_path] = time.time()
    
    def on_moved(self, event):
        if not event.is_directory and event.src_path in self.pending_crdownload_files:
            self.download_complete_callback(event.dest_path)
            del self.pending_crdownload_files[event.src_path]

        
    def download_complete_callback(self,filepath):
        logging.info(f'Download complete. Downloaded file path: {filepath}')
        if not filepath.endswith('.pdf'):
            return None
        
        self._handle_pdf_download(filepath) 
    
    def _handle_pdf_download(self,filepath):

        results = get_arxiv_metadata(
            filepath = filepath,
            client=self.client
        )

        if not results:
            logging.info(f'Downloaded file: {filepath} was not found on the arxiv')
            return None
        
        logging.info(f'arxiv metadata found: {results}')
        logging.info(f'renaming and moving...')
        self.tagger.rename(filepath,metadata=results)

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
    handler=FileDownloadHandler()
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
