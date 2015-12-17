from .ability import *

# workers does the pooling jobs and save data into databases
# 
class Worker:
    pass

# all indexes of the market
class IndexWorker(Worker):
    def __init__(self, market=('CNSH', 'CNSZ')):
        self.market = market

    def fetch_index_list(self):
        agent = ability_pool.acquire(ListAbility(market=self.market, target_type="index"))
        targets = agent.list(target_type="index") # [(<name>, <code>), ...]
        return (len(targets), 0)