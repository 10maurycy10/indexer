# extractor(file, path, file_callback, dictionary, options)
def file_csv(file,path, file_callback, d, options):
    header = file.readline()
    d[path]["csv.header"] = header.decode("utf-8") 
