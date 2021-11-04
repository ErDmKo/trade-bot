import sys
from server.main import main
from .db import run_script as sql
from .trade.player import run_script as play
from .tinkoff import main as api
import logging

logger = logging.getLogger(__name__)

if len(sys.argv) > 1:
    prog = sys.argv[1]
    if prog == 'api':
        api()
    elif prog == 'sql':
        sql()
    elif prog == 'play':
        play()
    else:
        print('NO Action! main start')
        main()
else:
    main()
