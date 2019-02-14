import os
import sys
sys.path.append(os.path.join(
    os.path.dirname(__file__),
    'panda3d-blend2bam',
))

from blend2bam.cli import main
sys.exit(main())
