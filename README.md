# Bulk File Indexer

With high capacity disks and tools like RAID,ZFS,BTRFS it has become possible to acumulate many terrabytes (sometimes even petabytes of data).

But this presents a problem: How do you organize many terrabytes (somtimes petabytes) of assorted files?

You could sit and tag individual files, but this could take years. Most files already have metadata but it is all in incompatable formats and is not easly searchable.

## What this is

This is a tool to take all this disimilar and incompatable data, and load it into a database for easy searching.

## What this is not

- A file manager

- A backup tool

- A file taxonomy

## How to use

The main entry point is ``cli.py``. The script has a few subcommands (more soon):


- ``add_indexed DIR`` Add a directory to be indexed.

- ``freshen [--fulltext]`` Populate the index. if ``--fulltext`` is passed, the fulltext of files are indexed, but this results in large indexes and longer runtimes. If a new file is added, run this to add it to the index.

- ``drop`` Delete the index (doent touch the indexed files).

- ``search [keywords]`` Searches the index for keywords, uses sqlite3's FTSS syntax.

- 
