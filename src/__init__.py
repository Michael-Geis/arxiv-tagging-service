import win32serviceutil
import win32event
import servicemanager
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import shutil
import time
import arxiv
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,  # Set the logging level (e.g., DEBUG, INFO, WARNING)
    format="%(asctime)s - %(levelname)s - %(message)s"  # Define the log message format
)

load_dotenv()
for k,v in os.environ.items():
    os.environ[k] = os.path.expandvars(v)

print(os.getenv('TARGET_DIR'))
    

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
        self.client = arxiv.Client() # Does arxiv provide an api to pass in a logger?
        self.arxiv_tagger = ArXivTagger(destination_dir=os.getenv('target_dir'))
    
    def on_created(self,event):
        if not event.is_directory and event.src_path.endswith('.crdownload'):
            self.pending_crdownload_files[event.src_path] = time.time()
    
    def on_moved(self, event):
        if not event.is_directory and event.src_path in self.pending_crdownload_files:
            self.download_complete_callback(event.dest_path)
            del self.pending_crdownload_files[event.src_path]
        
    def download_complete_callback(self,filepath):

        logging.info(f'Download completed at: {filepath}')
        if not filepath.endswith('.pdf'):
            return None
        self._handle_pdf_download(filepath) 
    
    def _handle_pdf_download(self,filepath):

        metadata = self._get_arxiv_metadata(filepath=filepath)
        if not metadata:
            logging.info(f'Downloaded file: {filepath} was not found on the arxiv')
            return None
        logging.info(f'arxiv metadata found: {metadata}')
        logging.info(f'renaming and moving...')
        self.arxiv_tagger.rename(source_path=filepath,metadata=metadata)

    def _cleanup_stale_crdownload_files(self):

        current_time = time.time()
        self.pending_crdownload_files = {
            path: timestamp
            for path, timestamp in self.pending_crdownload_files.items()
            if current_time - timestamp <= self.timeout_threshold
        }
    
    def _get_arxiv_metadata(self,filepath) -> dict[str,object] | None:
        """Takes a file path and returns the paper metadata if it is an arxiv paper. Otherwise, returns None

        Args:
            filepath (str): Path to the file to check
            client (arxiv.Client): Client used to query the arxiv api

        Returns:
            obj: Either None, if the file name does not correspond to an arxiv article, or the metadata of the paper.
        """
        
        # The basename will always correspond to an arxiv id if it is an arxiv paper

        file_name = os.path.splitext(os.path.basename(filepath))[0]
        search = arxiv.Search(id_list=[file_name])
        try:
            result = next(self.client.results(search=search))
            logging.info(f'Found arXiv article corresponding to path: "{filepath}".')
        except StopIteration:
            logging.info(f'No results returned for path: "{filepath}". No action taken.') 
            return None 
        author_list = [author.name for author in result.authors]

        ## Could these attributes be missing?
        return {'title': result.title, 'author_list': author_list, 'primary_category':result.primary_category}
            

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

logging.info("app start")
observer = Observer()
handler=FileDownloadHandler()
SOURCE_DIR = os.getenv('SOURCE_DIR')
observer.schedule(event_handler=handler,path=SOURCE_DIR,recursive=False)

logging.info(f'monitoring changes in dir {SOURCE_DIR}')
observer.start()
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()