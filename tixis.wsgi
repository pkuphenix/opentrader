import sys
sys.path.insert(0, '/home/qianli/pro/opentrader')
from werkzeug.debug import DebuggedApplication
from tixis import app

application = DebuggedApplication(app, True)
