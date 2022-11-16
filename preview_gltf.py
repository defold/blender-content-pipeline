import os
import platform
import urllib.request

BUILD_TOOLS_FOLDER            = "build_tools"
DEFOLD_HTTP_BASE              = "https://d.defold.com/archive/stable"
DEFOLD_SHA                    = "9c44c4a9b6cbc9d0cb66b7027b7c984bf364a568"
DEFOLD_BOB_JAR_PATH           = "%s/%s/bob/bob.jar" % (DEFOLD_HTTP_BASE, DEFOLD_SHA)
DEFOLD_DMENGINE_PATH_TEMPLATE = "%s/%s/engine/x86_64-%s/dmengine%s"

def get_host_platform_desc():
	# platform, extension
	platforms = {
		"Darwin"  : ("macos", ""),
		"Windows" : ("win32", ".exe"),
		"Linux"   : ("linux", "")
	}
	return platforms[platform.system()]

def get_bob_build_path():
	return "%s/bob.jar" % BUILD_TOOLS_FOLDER
def get_dmengine_build_path():
	os_name, bin_ext = get_host_platform_desc()
	return "%s/dmengine%s" % (BUILD_TOOLS_FOLDER, bin_ext)

def get_bob():
	bob_path = get_bob_build_path()
	if not os.path.exists(bob_path):
		print("Downloading bob.jar from %s" % DEFOLD_BOB_JAR_PATH)
		urllib.request.urlretrieve(DEFOLD_BOB_JAR_PATH, bob_path)
	else:
		print("Using cached bob.jar")

def get_dmengine():
	os_name, bin_ext = get_host_platform_desc()
	dmengine_path = get_dmengine_build_path()
	if not os.path.exists(dmengine_path):
		dmengine_http_path = DEFOLD_DMENGINE_PATH_TEMPLATE % (DEFOLD_HTTP_BASE, DEFOLD_SHA, os_name, bin_ext)
		print("Downloading dmengine%s from %s" % (bin_ext, dmengine_http_path))
		urllib.request.urlretrieve(dmengine_http_path, dmengine_path)
	else:
		print("Using cached dmengine%s" % bin_ext)

def make_build_tools():
	os.makedirs(BUILD_TOOLS_FOLDER, exist_ok=True)
	get_bob()
	get_dmengine()

def do_preview(gltf):
	print("Previewing %s file" % gltf)
	make_build_tools()