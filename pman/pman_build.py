import sys
import os

import bpy
import addon_utils

def main():
    # Make sure BlenderPanda addon is enabled
    addon_utils.enable("BlenderPanda", persistent=True)

    #print(sys.argv)
    srcdir, dstdir = sys.argv[1], sys.argv[2]

    #print('Exporting:', srcdir)
    #print('Export to:', dstdir)

    for root, _dirs, files in os.walk(srcdir):
        for asset in files:
            src = os.path.join(root, asset)
            dst = src.replace(srcdir, dstdir).replace('.blend', '.bam')

            if not asset.endswith('.blend'):
                # Only convert blend files with pman_build stub
                continue

            if os.path.exists(dst) and os.stat(src).st_mtime <= os.stat(dst).st_mtime:
                # Don't convert up-to-date-files
                continue

            if asset.endswith('.blend'):
                print('Converting .blend file ({}) to .bam ({})'.format(src, dst))
                try:
                    os.makedirs(os.path.dirname(dst))
                except FileExistsError:
                    pass
                bpy.ops.wm.open_mainfile(filepath=src)
                bpy.ops.panda_engine.export_bam(filepath=dst, copy_images=False, skip_up_to_date=True)


if __name__ == '__main__':
    main()
