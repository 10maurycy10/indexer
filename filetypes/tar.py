import tempfile
import tarfile
import tqdm

# extractor(file, path, file_callback, dictionary, options)
def file_tar(file, path, callback, d, cfg):
    """
    Extracts metadata of Contained files
    """
    archive = tarfile.TarFile(fileobj=file)
    for entry in tqdm.tqdm(archive.getmembers(), position=cfg.depth, postfix="TAR"):
        if entry.isfile():
            entry_name = f"{path};{entry.name}"
            if cfg.use_tempfile:
                tfile = tempfile.TemporaryFile()
                tfile.write(archive.extractfile(entry.name).read())
                tfile.seek(0)
                cfg.depth = cfg.depth + 1
                callback(tfile, entry_name, d, cfg)
                cfg.depth = cfg.depth - 1
                tfile.close()
            else:
                callback(archive.extractfile(entry.name), entry_name, d, cfg)
