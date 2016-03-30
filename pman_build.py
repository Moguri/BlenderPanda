import sys
import os
import shutil

import bpy

print(sys.argv)
srcdir, dstdir = sys.argv[-2:]

print('Exporting:', srcdir)
print('Export to:', dstdir)

for asset in os.listdir(srcdir):
    src = os.path.join(srcdir, asset)
    dst = os.path.join(dstdir, asset)

    if os.path.exists(dst) and os.stat(src).st_mtime <= os.stat(dst).st_mtime:
        print('Skip building up-to-date file: {}'.format(dst))
        continue

    if asset.endswith('.blend'):
        print('Converting .blend file ({}) to .bam ({})'.format(src, dst))
        topath = os.path.join(dstdir, asset.replace('.blend', '.bam'))
        dst = dst.replace('.blend', '.bam')
        bpy.ops.wm.open_mainfile(filepath=src)
        bpy.ops.panda_engine.export_bam(filepath=dst)
    else:
        print('Copying non .blend file from "{}" to "{}'.format(src, dst))
        shutil.copyfile(src, dst)
