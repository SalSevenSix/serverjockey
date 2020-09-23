#!/usr/bin/env python3

import asyncio
import sys
from core import bootstrap


if __name__ == '__main__':
    sys.exit(asyncio.run(bootstrap.main(sys.argv)))
