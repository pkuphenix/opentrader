from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.dates import MONDAY
#from matplotlib.finance import quotes_historical_yahoo_ochl
from matplotlib.dates import MonthLocator, WeekdayLocator, DateFormatter

# lines: [{"value":[...], "label":"..."}]
def draw_line(title, dates, lines, width=6, height=4):
    # every monday
    mondays = WeekdayLocator(MONDAY)

    # every 3rd month
    months = MonthLocator(range(1, 13), bymonthday=1, interval=1)
    monthsFmt = DateFormatter("%b '%y")

    fig, ax = plt.subplots()
    ax.set_title(title)
    for line in lines:
        val = line['value']
        del line['value']
        ax.plot_date(dates, val, '-', **line)
    #ax.xaxis.set_major_locator(months)
    #ax.xaxis.set_major_formatter(monthsFmt)
    #ax.xaxis.set_minor_locator(mondays)
    ax.autoscale_view()
    #ax.xaxis.grid(False, 'major')
    #ax.xaxis.grid(True, 'minor')
    ax.grid(True)
    fig.autofmt_xdate()
    fig.set_size_inches(width, height)
    plt.show()
