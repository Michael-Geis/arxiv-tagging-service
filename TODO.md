# List of all features that need to be added

## configuration

1. add gui to set configuration on service startup
1. allow configuration to set up how the service renames the file (how the arxiv metadata is used)
1. add option to retroactively search through directory and rename/move old files when the service starts

## internals

1. handle sanitizing file name so that we don't die when we try to rename the file
1. gracefully handle duplicate files

## features

1. fully configurable file naming convention
1. saving files in datetime subdirectories corresponding download date or posted date 
1. saving files in subdirectories according to subject tag
1. check for regular file moves -- e.g. if I move an arxiv pdf into the watched directory, it should recognize it and tag and move it.
1. allow multiple watched directories
1. add optional scanning of a given directory and tagging on startup
1. One way to package this is as a CLI tool
    - tagger cleanup-dir
    - tagger watch
    - tagger stop
    - tagger add-watched-dir 

## naming strategies

1. name a paper (FIRST AUTHOR'S NAME). When there are multiple, ones increment. E.g. MCLEEREY 1, MCCLEEREY 2, etc