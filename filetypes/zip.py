import zipfile
import tempfile
import tqdm

# extractor(file, path, file_callback, dictionary, options)
def file_zip(file, path, dumpdata_file, d):
    """
    Extract metadata of contained files in a zip archive
    """
    archive = zipfile.ZipFile(file)
    d[path]["extracted"] = "yes"
    for entry in tqdm.tqdm(archive.infolist(), position=cfg.depth, postfix="ZIP"):
        entry_name = f"{path};{entry.filename}"
        try:
            if cfg.use_tempfile:
                # Extract into tempfile
                tfile = tempfile.TemporaryFile()
                tfile.write(archive.open(entry.filename).read())
                tfile.seek(0)
                cfg.depth = cfg.depth + 1
                dumpdata_file(tfile, entry_name, d, cfg)
                cfg.depth = cfg.depth - 1
                tfile.close()
            else:
                dumpdata_file(archive.open(entry.filename), entry_name, d, cfg)

        except RuntimeError:
            tfile.close()
            pass
