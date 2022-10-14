import tempfile
import tarfile

# extractor(file, path, file_callback, dictionary, options)
def file_tar(file, path, callback, d, cfg):
    """
    Extracts metadata of Contained files
    """
    archive = tarfile.TarFile(fileobj=file)
    for entry in archive.getmembers():
        if entry.isfile():
            entry_name = f"{path};{entry.name}"
            if cfg.use_tempfile:
                tfile = tempfile.TemporaryFile()
                tfile.write(archive.extractfile(entry.name).read())
                tfile.seek(0)
                callback(tfile, entry_name, d, cfg)
                tfile.close()
            else:
                callback(archive.extractfile(entry.name), entry_name, d, cfg)
