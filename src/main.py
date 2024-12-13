import arxiv
import logging
import os

##TODO: Configure logging

def get_arxiv_metadata(file_name: str, client: arxiv.Client) -> dict[str,str] | None:
    """Takes a file name and returns the paper metadata if it is an arxiv paper. Otherwise, returns None

    Args:
        file_name (str): Path of the form <filename>.<extension>
        client (arxiv.Client): Client used to query the arxiv api

    Returns:
        obj: Either None, if the file name does not correspond to an arxiv article, or the metadata of the paper.
    """
    
    # The basename will always correspond to an arxiv id if it is an arxiv paper
    base_name = os.path.splitext(file_name)[0]

    search = arxiv.Search(id_list=[base_name])
    try:
        result = next(client.results(search=search))
        logging.info(f'Found arXiv article corresponding to file "{file_name}".')
    except StopIteration:
        logging.info(f'No results returned for file "{file_name}". No action taken.') 
        return None 
    authors = ', '.join([author.name for author in result.authors])

    ## Could these attributes be missing?
    return {'title': result.title, 'authors': authors, 'primary_category':result.primary_category}

def format_name(file_name: str, metadata: dict[str,str]) -> str:
    """Returns string to rename paper to based on returned metadata of title, authors, and primary category.

    Args:
        file_name (str): The name of the file
        metadata (dict[str,str]): Dictionary containing the paper's metadata

    Returns:
        str: Formatted name
    """
    ## Handle missing data; return original file name if title is missing.
    if not metadata.get('title'):
        return file_name

    formatted_name = f'{metadata['title']}.pdf'
    return formatted_name
    
