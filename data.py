import sqlite3

class DB:
    def connect(self, path):
        self.db = sqlite3.connect(path)
        dbc = self.db.cursor()
        dbc.execute("CREATE TABLE IF NOT EXISTS tags (filename TEXT, tagname TEXT, tagvalue TEXT);")
        dbc.execute("CREATE INDEX IF NOT EXISTS name ON tags (filename)")
        dbc.execute("CREATE TABLE IF NOT EXISTS fulltext (filename TEXT, fulltext TEXT);")
        dbc.execute("CREATE TABLE IF NOT EXISTS indexed_dirs (filepath TEXT);")
        self.db.commit()

    def get_tagged_files(self):
        dbc = self.db.cursor()
        dbc.execute("SELECT filename FROM tags GROUP BY filename")
        return [name for (name,) in dbc]

    def get_indexed_dirs(self):
        dbc = self.db.cursor()
        dbc.execute("SELECT filepath FROM indexed_dirs;")
        return [name for (name,) in dbc]

    def indexed(self, filepath):
        dbc = self.db.cursor()
        dbc.execute("SELECT tagname FROM tags WHERE filename=?", (filepath,))
        return len(list(dbc)) > 0

    def cursor(self):
        return self.db.cursor()
        
    def commit(self):
        self.db.commit()
