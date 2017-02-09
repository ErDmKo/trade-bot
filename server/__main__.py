import sys
import pathlib
from server.main import main
from .db import run_script as sql
from .trade.player import run_script as play

if len(sys.argv) > 1:
    prog = sys.argv[1]
    if prog == 'sql':
        sql()
    if prog == 'play':
        play()
else:
    main()
