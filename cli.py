#!/bin/python3
import data
import argparse
import meta
import os
import tqdm

db = data.DB()
db.connect("db.sqlite")

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

@subcommand([argument("directory")])
def rm_indexed(args):
    path = os.path.abspath(args.directory)
    db.cursor().execute("DELETE FROM indexed_dirs WHERE filepath = ?", (path,));
    db.commit()

def insert(metadata_dict):
    print(f"Inserting {len(metadata_dict)}")
    for filepath in list(metadata_dict.keys()):
        metadata = metadata_dict[filepath]
        for key in list(metadata.keys()):
            if metadata[key]:
                value = metadata[key]
                db.cursor().execute("INSERT INTO tags (filename, tagname, tagvalue) values (?,?,?);", (filepath, key, value))
                db.cursor().execute("INSERT INTO searchindex (filename, tagvalue) values (?,?);", (filepath, value))
            del metadata[key]
        del metadata_dict[filepath]

@subcommand([argument("--fulltext", action='store_true'), argument("--no-tempfile", action="store_true")])
def freshen(args):
    cfg = meta.Cfg()
    cfg.callback = insert
    if args.fulltext:
        cfg.fulltext = True
    if args.no_tempfile:
        cfg.use_tempfile = False
    indexed = db.get_tagged_files()
    to_index = db.get_indexed_dirs()
    files_to_index = []
    for dir_to_index in to_index[::-1]:
        #files_to_index.append(dir_to_index)
        print(dir_to_index)
        for root, dirs, files in os.walk(dir_to_index, topdown=False):
            print()
            for name in files:
                filepath = os.path.join(root, name)
                if not db.indexed(filepath):
                    files_to_index.append(filepath)
                else:
                    print(f"Disregarding {filepath}")

    for filepath in tqdm.tqdm(files_to_index):
        metadata = {}
        print(filepath)
        meta.dumpdata(filepath, metadata, cfg)
        insert(metadata)
        db.commit()
    for key in cfg.error_counters.keys():
        print(f"WARNING {cfg.error_counters[key]} files of type {key} could not be parsed.")
        print(cfg.error_counters[key])


@subcommand([argument("keywords", nargs="*"), argument("-l","--limit", default=50)])
#TODO implement intersection in sql
def search(args):
    """
    Searches for keywords in index, by defualt shows the 50 most relevent results, this can be changed with --limit
    """
    dbc = db.cursor()
    keywords = " ".join(args.keywords)
    print("Performing filename search...")
    dbc.execute("SELECT filename FROM searchindex WHERE filename MATCH ? GROUP BY filename ORDER BY RANK LIMIT ?;", (keywords,args.limit))
    for (file,) in dbc:
        print("> ",file)
    print("Performing fulltext search...")
    dbc.execute("SELECT filename FROM searchindex WHERE tagvalue MATCH ? GROUP BY filename ORDER BY RANK LIMIT ?;", (keywords,args.limit))
    for (file,) in dbc:
        print("> ",file)

@subcommand([argument("--filename",required=False)])
def drop(args):
    """
    Remove selected files from db
    """
    if args.filename:
        db.cursor().execute("delete from tags where filename like ?", (f"{args.filename}%",))
        db.cursor().execute("delete from searchindex where filename like ?", (f"{args.filename}%",))
    else:
        db.cursor().execute("delete from tags")
        db.cursor().execute("delete from searchindex")
    db.commit()

@subcommand([argument("filename")])
def gettext(args):
    """
    Remove selected files from db
    """
    dbc = db.cursor()
    dbc.execute("SELECT tagvalue FROM tags WHERE filename=? and tagname='fulltext';", (args.filename,))
    for (x,) in dbc:
        import sys
        if type(x) == bytes:
            try:
                sys.stdout.write(x.decode("utf-8"))
            except UnicodeDecodeError:
                print("Falling back to latin-1")
                sys.stdout.write(x.decode("latin-1"))
        else:
            print(x)

if __name__ == "__main__":
    args = parser.parse_args()
    if args.subcommand is None:
        parser.print_help()
    else:
        args.func(args)

