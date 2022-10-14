import gzip

# extractor(file, path, file_callback, dictionary, options)
def file_gzip(file, path, callback, d, spec):
    """
    Unzips a file and dumps metadata
    """
    d[path]["gzip.extracted"] = "yes"
    innerpath = f"{path};decompressed"
    internal = gzip.open(file, "rb")
    callback(internal, innerpath, d, spec)
