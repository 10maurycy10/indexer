"""
meta.py: Dispach metadata extraction
"""

import magic
import zipfile

class Cfg:
    fulltext = False
    use_tempfile = True
    unparsed_counters = {}
    error_counters = {}

from filetypes.zip import file_zip
from filetypes.gzip import file_gzip
from filetypes.tar import file_tar
from filetypes.pdf import file_pdf
from filetypes.mutagen import file_mutagen
from filetypes.text import file_text
from filetypes.csv import file_csv
from filetypes.email import file_email

MIME_TYPES = {
    "application/zip": file_zip,
    "application/pdf": file_pdf,
    "application/x-tar": file_tar,
    "message/rfc822": file_email,
    "text/csv": file_csv,
    "audio/ogg": file_mutagen,
    "video/webm": file_mutagen,
    "video/mp4": file_mutagen,
    "audio/mpeg": file_mutagen,
    "audio/mp3": file_mutagen,
    "audio/webm": file_mutagen,
    "text/plain": file_text,
    "application/gzip": file_gzip
}

def dumpdata(path, d, cfg):
    """
    Writes the metadata of a file into d[path]
    """
    return dumpdata_file(open(path, "rb"), path, d, cfg)

def dumpdata_file(file,name,d, cfg):
    """
    Writes the metadata of a file into d[name]
    """
    # Read the first 2k, run libmagic, then seek back to the start
    header = file.read(2048)
    t = magic.from_buffer(header,mime=True)
    file.seek(0)
    d[name] = {"type": t}
    if t in MIME_TYPES:
        try:
            MIME_TYPES[t](file,name, dumpdata_file,d, cfg)
        except NotImplementedError:
            pass
        except zipfile.BadZipFile:
            pass
        except Exception as e:
            d[name]["bulk.error"] = str(e)
            if t in cfg.unparsed_counters:
                cfg.error_counters[t] = cfg.error_counters[t] + 1
            else:
                cfg.error_counters[t] = 1
    else:
        d[name]["bulk.parsed"] = "no"
        if t in cfg.unparsed_counters:
            cfg.unparsed_counters[t] = cfg.unparsed_counters[t] + 1
        else:
            cfg.unparsed_counters[t] = 1

    # Convert list to semicolon delimited files
    for file in d.keys():
        metadata = d[file]
        for key in metadata.keys():
            if type(metadata[key]) == bytes:
                try:
                    metadata[key] = metadata[key].decode("utf-8")
                except Exception as e:
                    metadata[key] = "INVALIDUTF8"
            if type(metadata[key]) == list:
                metadata[key] = "; ".join(metadata[key])
    return d
    
