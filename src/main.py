import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import shutil
import time
import arxiv
from dotenv import load_dotenv
import re

def is_valid_arxiv_filename(filepath: str) -> bool:
    """Does a basic regex check for valid arxiv pdf filenames

    Args:
        filepath (str): The path to the downloaded file to check

    Returns:
        bool: True or False depending on whether the basename of the filepath passes the regex filter.
    """

    basename = os.path.basename(filepath)
    pattern = r'^\d{4}\.?\d{3,5}([vV]\d+)?\.pdf$'
    return re.match(pattern=pattern,string=basename) is not None
    



class ArXivTagger:
    
    def __init__(self,target_dir):
        self.target_dir = target_dir
        if not os.path.exists(self.target_dir):
            logging.info(f'destination directory {target_dir} not found, creating it instead.')
            os.makedirs(target_dir)
    
    def rename(self,source_path,metadata):

        new_basename = metadata['title'].lower().replace(' ','_')
        target_path = os.path.join(self.target_dir,f'{new_basename}.pdf')
        if os.path.exists(source_path):
            shutil.move(source_path,target_path)
            logging.info(f'renamed {source_path} to {target_path}.')
            return target_path
        else:
            raise FileNotFoundError('e')
        

class FileDownloadHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.client = arxiv.Client() # Does arxiv provide an api to pass in a logger?
        self.arxiv_tagger = ArXivTagger(target_dir=os.getenv('TARGET_DIR'))
    
    def on_moved(self, event):
        ## A download always ends with a temporary .crdownload file being moved to the final filepath
        if not event.is_directory and event.src_path.endswith('.crdownload'):
            self.download_complete_callback(event.dest_path)
        
    def download_complete_callback(self,filepath) -> None:

        logging.info(f'Download completed at: {filepath}')
        if not is_valid_arxiv_filename(filepath):
            return None
        logging.info(f'Downloaded filename "{os.path.basename(filepath)}" matches arxiv format, fetching metadata...')
        self._handle_arxiv_download(filepath) 
    
    def _handle_arxiv_download(self,filepath) -> None:

        metadata = self._get_arxiv_metadata(filepath=filepath)
        if not metadata:
            logging.info(f'Downloaded file: {filepath} was not found on the arxiv.')
            return None
        logging.info(f'Arxiv metadata found: {metadata}.')
        self.arxiv_tagger.rename(source_path=filepath,metadata=metadata)

    def _get_arxiv_metadata(self,filepath) -> dict[str,object] | None:
        """Takes a file path and returns the paper metadata if it is an arxiv paper. Otherwise, returns None

        Args:
            filepath (str): The path of the downloaded file to pull arxiv metadata for.

        Returns:
            obj: Either None, if a search for the filepath's basename as an arxiv id returns nothing,
            or the metadata of the paper returned by the search.
        """
        
        filename = os.path.splitext(os.path.basename(filepath))[0]
        search = arxiv.Search(id_list=[filename])
        try:
            result = next(self.client.results(search=search))
        except StopIteration: # If the generator is empty, return None
            return None 

        author_list = [author.name for author in result.authors]
        ## Could these attributes be missing?
        return {'title': result.title, 'author_list': author_list, 'primary_category':result.primary_category}
            

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,  
        format="%(asctime)s - %(levelname)s - %(message)s"  
    )
    logging.info("App start")

    load_dotenv()
    for k,v in os.environ.items():
        os.environ[k] = os.path.expandvars(v)

    observer = Observer()
    handler=FileDownloadHandler()
    SOURCE_DIR = os.getenv('SOURCE_DIR')
    observer.schedule(event_handler=handler,path=SOURCE_DIR,recursive=False)

    logging.info(f'monitoring changes in dir {SOURCE_DIR}')
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt as e:
        logging.info('User killed the process.')
        observer.stop()
        observer.join()
    except Exception:
        observer.stop()
        observer.join()