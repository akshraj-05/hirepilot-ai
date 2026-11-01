# pysqlite3 workaround for ChromaDB in-memory mode (not needed for HTTP client)
# __import__("pysqlite3")
# import sys
# sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
