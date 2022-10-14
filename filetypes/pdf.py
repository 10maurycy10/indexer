import func_timeout
from io import StringIO

def file_pdf_inner(file, path, d, cfg):
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

        # For improved indexing, use text on first page if no title is found
        if cfg.fulltext or not "title.main" in d[path]:
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
                # If fulltext is not neded stop after a sigle page
                if not cfg.fulltext:
                    d[path]["pdf.firstpage"] = output_string.getvalue()
                    return
            d[path]["fulltext"] = output_string.getvalue()

def file_pdf(file, path, callback, d, cfg):
    # Attempt to save to tempfile
    try:
        return func_timeout.func_timeout(120, file_pdf_inner, args=(file, path, d, cfg))
    except func_timeout.FunctionTimedOut:
        d[path]["pdf.timeout"] = "yes"

