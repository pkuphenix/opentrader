# stock main class
class Stock(object): 
    def __init__(self, code=None, info=None):
        self.code = code
        if info is None:
            self.info = DB.get_stock_info(self.code)
        
    @property
    def name(self)
    
class TestStock(object):
    def test_get_basic_info(self):
        s = Stock.get_by_code('SZ002736')
        assert s is not None
        assert s.name == "XXX"
        
        
        