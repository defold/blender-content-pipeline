#!/usr/bin/env python
import argparse
import platform
import os
import subprocess
import sys

def get_blender_bin():
	host_platform = platform.system()
	if host_platform == "Darwin":
		return "/Applications/Blender.app/Contents/MacOS/Blender"
	else:
		print("Unable to find blender installation")
		os.exit(-1)

def run_blender_script(path, args):
	blender_bin = get_blender_bin()
	subprocess.run([blender_bin, '-b', '-P', path, "--"] + args)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Convert blender content to Defold')
	parser.add_argument('--fbx-to-blend', nargs='+')
	parser.add_argument('--verify-blend', nargs='+')
	parser.add_argument('--blend-to-gltf', nargs='+')
	parser.add_argument('--preview-gltf', nargs=1)
	parser.add_argument('--clean')

	args = parser.parse_args()
	if args.fbx_to_blend:
		print("Converting .fbx files to Blender")
		run_blender_script("convert_fbx_to_blender.py", args.fbx_to_blend)
	if args.blend_to_gltf:
		print("Converting .blend files to GLTF")
		run_blender_script("convert_blend_to_gltf.py", args.blend_to_gltf)
	if args.preview_gltf:
		print("Previewing .gltf in Defold")
		import preview_gltf
		preview_gltf.do_preview(args.preview_gltf[0])
	if args.clean:
		print("Cleaning build folder")
		import preview_gltf
		preview_gltf.do_clean()

	if not any(vars(args).values()):
		parser.print_help(sys.stderr)
