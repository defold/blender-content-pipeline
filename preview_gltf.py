import os
import platform
import shutil
import stat
import subprocess
import urllib.request
import zipfile

BUILD_TOOLS_FOLDER           = "build_tools"
DEFOLD_HTTP_BASE             = "https://d.defold.com/archive/stable"
DEFOLD_SHA                   = "9c44c4a9b6cbc9d0cb66b7027b7c984bf364a568"
DEFOLD_BOB_JAR_URL           = "%s/%s/bob/bob.jar" % (DEFOLD_HTTP_BASE, DEFOLD_SHA)
DEFOLD_DMENGINE_URL_TEMPLATE = "%s/%s/engine/x86_64-%s/dmengine%s"
DEFOLD_PREVIEW_PROJECT_URL   = "https://github.com/defold/pbr-viewer/archive/refs/heads/master.zip"

MODEL_PATH = "main/preview.glb"

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
def get_dmengine_platform_path():
    os_name, bin_ext = get_host_platform_desc()
    return "dmengine%s" % (bin_ext)
def get_dmengine_build_path():
    return "%s/%s" % (BUILD_TOOLS_FOLDER, get_dmengine_platform_path())
def get_template_project_path():
    return "%s/pbr-viewer-master" % BUILD_TOOLS_FOLDER

def get_bob():
    bob_path = get_bob_build_path()
    if not os.path.exists(bob_path):
        print("Downloading bob.jar from %s" % DEFOLD_BOB_JAR_URL)
        urllib.request.urlretrieve(DEFOLD_BOB_JAR_URL, bob_path)
    else:
        print("Using cached bob.jar")

def get_dmengine():
    os_name, bin_ext = get_host_platform_desc()
    dmengine_path = get_dmengine_build_path()
    if not os.path.exists(dmengine_path):
        dmengine_http_path = DEFOLD_DMENGINE_URL_TEMPLATE % (DEFOLD_HTTP_BASE, DEFOLD_SHA, os_name, bin_ext)
        print("Downloading dmengine%s from %s" % (bin_ext, dmengine_http_path))
        urllib.request.urlretrieve(dmengine_http_path, dmengine_path)

        os.chmod(dmengine_path, stat.S_IEXEC)
    else:
        print("Using cached dmengine%s" % bin_ext)

def get_template_project():
    template_project_path = get_template_project_path()
    if not os.path.exists(template_project_path):
        print("Downloading template project from %s" % DEFOLD_PREVIEW_PROJECT_URL)
        template_zip_path = template_project_path + ".zip"
        urllib.request.urlretrieve(DEFOLD_PREVIEW_PROJECT_URL, template_zip_path)

        with zipfile.ZipFile(template_zip_path,"r") as zip_ref:
            zip_ref.extractall(BUILD_TOOLS_FOLDER)
    else:
        print("Using cached template project")

def make_build_tools():
    os.makedirs(BUILD_TOOLS_FOLDER, exist_ok=True)
    get_bob()
    get_dmengine()

def make_project(gltf):
    get_template_project()

    template_project_path = get_template_project_path()
    template_model_path = "%s/%s" % (template_project_path, MODEL_PATH)
    shutil.copy(gltf, template_model_path)
    subprocess.run(["java", "-jar", "../bob.jar", "resolve", "build"], cwd=get_template_project_path())

def do_preview(gltf):
    print("Previewing %s file" % gltf)
    make_build_tools()
    make_project(gltf)

    dmengine_path = get_dmengine_platform_path()
    subprocess.run("../%s" % dmengine_path, cwd=get_template_project_path())

def do_clean():
    try:
        os.remove(BUILD_TOOLS_FOLDER)
    except:
        pass
    print("Finished cleaning build folder %s" % BUILD_TOOLS_FOLDER)
