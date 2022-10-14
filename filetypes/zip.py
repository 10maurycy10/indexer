import zipfile
import tempfile

# extractor(file, path, file_callback, dictionary, options)
def file_zip(file, path, dumpdata_file, d, cfg):
    """
    Extract metadata of contained files in a zip archive
    """
    archive = zipfile.ZipFile(file)
    for entry in archive.infolist():
        entry_name = f"{path};{entry.filename}"
        try:
            if cfg.use_tempfile:
                # Extract into tempfile
                tfile = tempfile.TemporaryFile()
                tfile.write(archive.open(entry.filename).read())
                tfile.seek(0)
                dumpdata_file(tfile, entry_name, d, cfg)
                tfile.close()
            else:
                dumpdata_file(archive.open(entry.filename), entry_name, d, cfg)

        except RuntimeError:
            tfile.close()
            pass
