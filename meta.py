"""
meta.py: Metadata extraction code
"""

import magic
import mutagen
import pikepdf
import dateparser
import gzip
import zipfile
import tarfile
import email
from io import StringIO

fulltext = False
unparsed_counters = {}
error_counters = {}

def file_email(file, path, d):
    msg = email.parser.BytesParser().parse(file)
    d[path]["title.main"] = msg.get("subject")
    d[path]["message.destination"] = msg.get("to")
    d[path]["message.source"] = msg.get("from")
    counter = 0
    for attachment in msg.walk():
        if not attachment.is_multipart():
            payload = StringIO(attachment.get_payload())
            attachment_path = f"{path};{str(counter)}"
            counter = counter + 1
            dumpdata_file(payload, attachment_path, d)

## TODO open the zip and recurse
def file_zip(file, path, d):
    """
    Extract a zip file and extract metadata of contained files
    """
    archive = zipfile.ZipFile(file)
#    archive_info = archive.getinfo()
    for entry in archive.infolist():
        entry_name = f"{path};{entry.filename}"
        dumpdata_file(archive.open(entry.filename,"r"), entry_name, d)

def file_tar(file, path, d):
    archive = tarfile.open(file)
    for entry in archive.getmembers():
        if entry.isfile():
            entry_name = f"{path};{entry.filename}"
            dumpdata_file(archive.extract(entry.filename), entry_name, d)


def file_gzip(file, path, d):
    """
    gzip files dont have usefull metadata, so open it and extract metadata from the contained file
    """
    d[path]["gzip.extracted"] = "yes"
    innerpath = f"{path};decompressed"
    internal = gzip.open(file, "rb")
    dumpdata_file(internal, innerpath, d)

def file_mutagen(file, path, d):
    tag = mutagen.File(file)
    if tag:
        d[path]["author"] = tag.get("artist")
        d[path]["title.series"] = tag.get("album")
        d[path]["title.main"] = tag.get("title")
        d[path]["title.number"] = tag.get("tracknumber")
        d[path]["date.publication"] = tag.get("date")
        d[path]["generator"] = tag.get("software") or tag.get("encoder")

def file_pdf(file, path, d):
    pdf = pikepdf.Pdf.open(file)
    print("Got pdf")
    meta = pdf.open_metadata()
    print("Got meta")
    docinfo = pdf.docinfo
    for key, value in docinfo.items():
        # Skip keys which are not strings
        try:
            value = str(value)
        except:
            continue;
        # Record the value
        d[path][f"pdf.{key}"] = value
        # Additionaly, record kown keys in a non pdf specific form.
        match key:
            case "/Author":
                d[path]["author"] = value
            case "/Creator":
                d[path]["pdf.creator"] = value
            case "/Producer":
                d[path]["generator"] = value
            case "/Title":
                d[path]["title.main"] = value
            case "/ModDate":
                d[path]["date.modification"] = value
            case "/CreationDate":
                d[path]["date.creation"] = value
            case "/ISBN":
                d[path]["literature.ISBN"] = value
    if fulltext:
        from pdfminer.high_level import extract_text
        text = extract_text(file)
        d[path]["fulltext"] = text

def file_text(file,path, d):
    """
    Text files don have any metadata, and the filesystem cant be trusted
    """
    if fulltext:
        d[path]["fulltext"] = file.read()

def file_csv(file,path,d):
    header = file.readline()
    d[path]["csv.header"] = header.decode("utf-8") 

MIME_TYPES = {
    "application/zip": file_zip,
    "application/pdf": file_pdf,
    "application/x-tar": file_tar,
    "message/rfc822": file_email,
    "text/csv": file_csv,
    "audio/ogg": file_mutagen,
    "video/mp4": file_mutagen,
    "audio/mp3": file_mutagen,
    "audio/webm": file_mutagen,
    "text/plain": file_text,
    "application/gzip": file_gzip
}

def dumpdata(path, d):
    """
    Writes the metadata of a file into d[path]
    """
    return dumpdata_file(open(path, "rb"), path, d)

def dumpdata_file(file,name,d):
    """
    Writes the metadata of a file into d[name]
    """
    print(name)
    # Read the first 2k, run libmagic, then seek back to the start
    header = file.read(2048)
    t = magic.from_buffer(header,mime=True)
    file.seek(0)
    d[name] = {"type": t}
    if t in MIME_TYPES:
        try:
            MIME_TYPES[t](file,name,d)
        except Exception as e:
            d[name]["bulk.error"] = str(e)
            if t in unparsed_counters:
                error_counters[t] = error_counters[t] + 1
            else:
                error_counters[t] = 1
    else:
        if t in unparsed_counters:
            unparsed_counters[t] = unparsed_counters[t] + 1
        else:
            unparsed_counters[t] = 1
        return {} # Avoid taging unrecognized files for now

    # Convert list to semicolon delimited files
    for file in d.keys():
        metadata = d[file]
        for key in metadata.keys():
            if type(metadata[key]) == list:
                metadata[key] = "; ".join(metadata[key])
    return d
    
