"""
meta.py: Metadata extraction code
"""
import email
from io import StringIO
from io import BytesIO

# extractor(file, path, file_callback, dictionary, options)
def file_email(file, path, dumpdata_file, d, cfg):
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
            dumpdata_file(payload, attachment_path, d, cfg)
