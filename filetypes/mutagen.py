# extractor(file, path, file_callback, dictionary, options)
def file_mutagen(file, path, callback, d, cfg):
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
