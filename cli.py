#!/bin/python3
import data
import argparse
import meta
import os
import tqdm

db = data.DB()
db.connect("db.sqlite")
print("Opened database")

# Setup argparse
parser = argparse.ArgumentParser(prog="bulk tagger")
subparsers = parser.add_subparsers(dest="subcommand")
subparsers.required = True

# Decorator for argparse, this would be nice to have in stdlib
def subcommand(args=[], parent=subparsers):
    def decorator(func):
        parser = parent.add_parser(func.__name__, description=func.__doc__)
        parser.set_defaults(func=func)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
    return decorator
def argument(*name_or_flags, **kwargs):
    return ([*name_or_flags], kwargs)

@subcommand([argument("directory")])
def add_indexed(args):
    """
    Marks a file or directory for indexind
    """
    path = os.path.abspath(args.directory)
    if os.path.exists(path):
        db.cursor().execute("INSERT INTO indexed_dirs (filepath) VALUES (?)", (path,));
        db.commit()
        print(f"Inserted {path}")
    else:
        print(f"File/Directory {path} does not exit")

def insert(metadata_dict):
    for filepath in metadata_dict.keys():
        metadata = metadata_dict[filepath]
        for key in metadata.keys():
            if metadata[key]:
                value = metadata[key]
                db.cursor().execute("INSERT INTO tags (filename, tagname, tagvalue) values (?,?,?);", (filepath, key, value))
                db.cursor().execute("INSERT INTO searchindex (filename, tagvalue) values (?,?);", (filepath, value))

@subcommand([argument("--fulltext", action='store_true')])
def freshen(args):
    if args.fulltext:
        print("Saving fulltext of files, this results in very *large* index.")
        meta.fulltext = True
    indexed = db.get_tagged_files()
    to_index = db.get_indexed_dirs()
    files_to_index = []
    for dir_to_index in to_index[::-1]:
        print(dir_to_index)
        for root, dirs, files in os.walk(dir_to_index, topdown=False):
           for name in files:
                filepath = os.path.join(root, name)
                if not db.indexed(filepath):
                    files_to_index.append(filepath)

    for filepath in tqdm.tqdm(files_to_index):
        metadata = {}
        meta.dumpdata(filepath, metadata)
        insert(metadata)
        db.commit()


@subcommand([argument("keywords", nargs="*")])
#TODO implement intersection in sql
def search(args):
    dbc = db.cursor()
    keywords = " ".join(args.keywords)
    print("Performing filename search...")
    dbc.execute("SELECT filename FROM searchindex WHERE filename MATCH ? GROUP BY filename;", (keywords,))
    for (file,) in dbc:
        print("> ",file)
    print("Performing fulltext search...")
    dbc.execute("SELECT filename FROM searchindex WHERE tagvalue MATCH ? GROUP BY filename;", (keywords,))
    for (file,) in dbc:
        print("> ",file)

@subcommand([])
def drop(args):
    db.cursor().execute("delete from tags")
    db.cursor().execute("delete from searchindex")
    db.commit()

if __name__ == "__main__":
    args = parser.parse_args()
    if args.subcommand is None:
        parser.print_help()
    else:
        args.func(args)

for key in meta.error_counters.keys():
    print(f"WARNING {meta.error_counters[key]} files of type {key} could not be parsed.")
