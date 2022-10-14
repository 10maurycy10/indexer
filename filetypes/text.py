# extractor(file, path, file_callback, dictionary, options)
def file_text(file,path, callback, d, cfg):
    """
    Text files don have any metadata, and the filesystem cant be trusted
    """
    if cfg.fulltext:
        d[path]["fulltext"] = file.read()
