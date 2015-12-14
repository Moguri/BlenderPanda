import sys
import os

import bpy

print(sys.argv)
srcdir, dstdir = sys.argv[-2:]

print('Exporting:', srcdir)
print('Export to:', dstdir)

for asset in os.listdir(srcdir):
    if asset.endswith('.blend'):
        frompath = os.path.join(srcdir, asset)
        topath = os.path.join(dstdir, asset.replace('.blend', '.bam'))
        bpy.ops.wm.open_mainfile(filepath=frompath)
        bpy.ops.panda_engine.export_bam(filepath=topath)
