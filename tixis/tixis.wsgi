import sys
sys.path.insert(0, '/home/qianli/pro/opentrader/tixis')
from werkzeug.debug import DebuggedApplication
from main import app

application = DebuggedApplication(app, True)
