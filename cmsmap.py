#!/usr/bin/env python3
# CMSmap is now CMScout. Keeps old command lines and scripts working.
import os, runpy, sys

sys.stderr.write("cmsmap.py is now cmscout.py\n")
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cmscout.py"),
               run_name="__main__")
