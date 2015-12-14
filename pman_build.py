import sys

import bpy

print(sys.argv)
frompath, topath = sys.argv[-2:]

print('Exporting:', frompath)
print('Export to:', topath)

bpy.ops.wm.open_mainfile(filepath=frompath)
bpy.ops.panda_engine.export_bam(filepath=topath)
