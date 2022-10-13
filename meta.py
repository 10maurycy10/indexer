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
from io import BytesIO

fulltext = False
unparsed_counters = {}
error_counters = {}

def file_email(file, path, d):
    """
    Extract metadata from email, then dump data of attachments
    """
    msg = email.parser.BytesParser().parse(file)
    d[path]["title.main"] = msg.get("subject")
    d[path]["message.destination"] = msg.get("to")
    d[path]["message.source"] = msg.get("from")
    counter = 0
    for attachment in msg.walk():
        if not attachment.is_multipart():
            payload = BytesIO(bytes(attachment.get_payload(), "utf-8"))
            attachment_path = f"{path};{str(counter)}"
            counter = counter + 1
            dumpdata_file(payload, attachment_path, d)

def file_zip(file, path, d):
    """
    Extract metadata of contained files in a zip archive
    """
    archive = zipfile.ZipFile(file)
    for entry in archive.infolist():
        entry_name = f"{path};{entry.filename}"
        try:
            dumpdata_file(archive.open(entry.filename,"r"), entry_name, d)
        except RuntimeError:
            pass

def file_tar(file, path, d):
    """
    Extracts metadata of Contained files
    """
    archive = tarfile.TarFile(fileobj=file)
    for entry in archive.getmembers():
        if entry.isfile():
            entry_name = f"{path};{entry.name}"
            dumpdata_file(archive.extractfile(entry.name), entry_name, d)


def file_gzip(file, path, d):
    """
    Unzips a file and dumps metadata
    """
    d[path]["gzip.extracted"] = "yes"
    innerpath = f"{path};decompressed"
    internal = gzip.open(file, "rb")
    dumpdata_file(internal, innerpath, d)

def file_mutagen(file, path, d):
    """
    Uses the mutagen library to extract metadata from audio files
    """
    tag = mutagen.File(file)
    if tag:
        d[path]["author"] = tag.get("artist")
        d[path]["title.series"] = tag.get("album")
        d[path]["title.main"] = tag.get("title")
        d[path]["title.number"] = tag.get("tracknumber")
        d[path]["date.publication"] = tag.get("date")
        d[path]["generator"] = tag.get("software") or tag.get("encoder")

def file_pdf(file, path, d):
        from pdfminer.pdfparser import PDFParser
        from pdfminer.pdfdocument import PDFDocument
        parser = PDFParser(file)
        doc = PDFDocument(parser)
        for meta in doc.info:
            if "Producer" in meta:
                d[path]["generator"] = meta["Producer"]
            if "Author" in meta:
                d[path]["author"] = meta["Author"]
            if "ISBN" in meta:
                d[path]["literature.ISBN"] = meta["ISBN"]
            if "Title" in meta:
                d[path]["title.main"] = meta["Title"]
            if "Type" in meta:
                d[path]["literature.type"] = meta["Type"]
            if "Subject" in meta:
                d[path]["title.sub"] = meta["Subject"]
            if "Publisher" in meta:
                d[path]["publisher"] = meta["Publisher"]
            if "Publish Date" in meta:
                d[path]["date.publication"] = meta["Publish Date"]

        for key in list(d[path].keys()):
            if type(d[path][key]) != bytes and type(d[path][key]) != str:
                del d[path][key]

        if fulltext:
            from pdfminer.converter import TextConverter
            from pdfminer.layout import LAParams
            from pdfminer.pdfdocument import PDFDocument
            from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
            from pdfminer.pdfpage import PDFPage
            from pdfminer.pdfparser import PDFParser

            output_string = StringIO()
            rsrcmgr = PDFResourceManager()
            device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.create_pages(doc):
                interpreter.process_page(page)
            d[path]["fulltext"] = output_string.getvalue()




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
    "video/webm": file_mutagen,
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
    # Read the first 2k, run libmagic, then seek back to the start
    header = file.read(2048)
    t = magic.from_buffer(header,mime=True)
    file.seek(0)
    d[name] = {"type": t}
    if t in MIME_TYPES:
        try:
            MIME_TYPES[t](file,name,d)
        except NotImplementedError:
            pass
        except zipfile.BadZipFile:
            pass
        except Exception as e:
            raise e
            d[name]["bulk.error"] = str(e)
            if t in unparsed_counters:
                error_counters[t] = error_counters[t] + 1
            else:
                error_counters[t] = 1
    else:
        d[name]["bulk.parsed"] = "no"
        if t in unparsed_counters:
            unparsed_counters[t] = unparsed_counters[t] + 1
        else:
            unparsed_counters[t] = 1

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
    
