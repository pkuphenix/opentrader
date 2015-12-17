# unit tests for the agent system
from .worker import *
#from db.persistent import *

class TestIndexWorker:
    def test_list_indexes(self):
        worker = IndexWorker(("CNSH","CNSZ"))
        assert worker
        (total, appended) = worker.fetch_index_list()
        assert total > 0
        #db = PersistDB()
        #db.get_

