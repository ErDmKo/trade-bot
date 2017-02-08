import sys
import pathlib
from server.main import main
from .db import run_script

if len(sys.argv) > 1:
    prog = sys.argv[1]
    if prog == 'sql':
        run_script()
else:
    main()
