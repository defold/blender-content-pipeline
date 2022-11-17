import os
import platform
import shutil
import stat
import subprocess
import sys
import urllib.request
import zipfile

import defold_content_helpers

# Build paths
BUILD_TOOLS_FOLDER           = "build_tools"
DEFOLD_HTTP_BASE             = "https://d.defold.com/archive/stable"
DEFOLD_SHA                   = "9c44c4a9b6cbc9d0cb66b7027b7c984bf364a568"
DEFOLD_BOB_JAR_URL           = "%s/%s/bob/bob.jar" % (DEFOLD_HTTP_BASE, DEFOLD_SHA)
DEFOLD_DMENGINE_URL_TEMPLATE = "%s/%s/engine/x86_64-%s/dmengine%s"
DEFOLD_PREVIEW_PROJECT_URL   = "https://github.com/defold/pbr-viewer/archive/refs/heads/master.zip"

# Scene content paths
MODEL_PATH    = "main/preview.glb"
MATERIAL_PATH = "main/materials"
TEXTURE_PATH  = "main/textures"
VERTEX_PATH   = "/builtins/materials/model.vp"
FRAGMENT_PATH = "/main/preview.fp"

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

def download_file(path, url):
    if not os.path.exists(path):
        print("Downloading %s" % url)
        urllib.request.urlretrieve(url, path)
    else:
        print("Using cached %s" % path)

def download_and_extract_zip(path, extract_path, url):
    if not os.path.exists(path):
        print("Downloading %s" % url)
        zip_path = path + ".zip"
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path,"r") as zip_ref:
            zip_ref.extractall(extract_path)
        os.remove(zip_path)
    else:
        print("Using cached %s" % path)

def get_bob():
    download_file(get_bob_build_path(), DEFOLD_BOB_JAR_URL)

def get_dmengine():
    os_name, bin_ext = get_host_platform_desc()
    dmengine_path = get_dmengine_build_path()
    dmengine_http_path = DEFOLD_DMENGINE_URL_TEMPLATE % (DEFOLD_HTTP_BASE, DEFOLD_SHA, os_name, bin_ext)
    download_file(dmengine_path, dmengine_http_path)
    os.chmod(dmengine_path, stat.S_IEXEC)

def get_template_project():
    download_and_extract_zip(get_template_project_path(), BUILD_TOOLS_FOLDER, DEFOLD_PREVIEW_PROJECT_URL)

def make_build_tools():
    os.makedirs(BUILD_TOOLS_FOLDER, exist_ok=True)
    get_bob()
    get_dmengine()

def write_material(material):
    data = material.serialize()
    path = "%s/%s/%s.material" % (get_template_project_path(), MATERIAL_PATH, material.name)
    with open(path, "w") as f:
        f.write(data)

def make_project_content(gltf):
    template_project_path = get_template_project_path()
    template_model_path = "%s/%s" % (template_project_path, MODEL_PATH)
    shutil.copy(gltf, template_model_path)
    subprocess.run(["java", "-jar", "../bob.jar", "resolve", "build"], cwd=get_template_project_path())

def make_project(gltf):
    get_template_project()

    import pygltflib
    from pygltflib.utils import ImageFormat
    gltf_file = pygltflib.GLTF2().load(gltf)

    image_base_path = "%s/%s" % (get_template_project_path(), TEXTURE_PATH)
    os.makedirs(image_base_path, exist_ok=True)

    material_base_path = "%s/%s" % (get_template_project_path(), MATERIAL_PATH)
    os.makedirs(material_base_path, exist_ok=True)

    # pygltflib doesn't seem to support exporting images that great,
    # so we have to do this awkward thing for now..
    gltf_file.convert_images(ImageFormat.FILE, path=image_base_path)
    for i in range(len(gltf_file.images)):
        image_path_i     = "%s/%s.png" % (image_base_path, i)
        image_path_named = "%s/%s.png" % (image_base_path, gltf_file.images[i].name)
        shutil.move(image_path_i, image_path_named)

    for i in range(len(gltf_file.materials)):
        defold_material = defold_content_helpers.material(gltf_file.materials[i].name)

        defold_material.set_vertex_space(defold_content_helpers.VERTEX_SPACE_WORLD)
        defold_material.set_vertex_program(VERTEX_PATH)
        defold_material.set_fragment_program(FRAGMENT_PATH)

        defold_material.add_tag("model")
        defold_material.add_sampler(gltf_file.materials[i].normalTexture,    "tex_normal")
        defold_material.add_sampler(gltf_file.materials[i].occlusionTexture, "tex_occlusion")
        defold_material.add_sampler(gltf_file.materials[i].emissiveTexture,  "tex_emissive")

        defold_material.add_constant(defold_content_helpers.CONSTANT_VERTEX, defold_content_helpers.CONSTANT_TYPE_VIEW,       "u_mtx_view")
        defold_material.add_constant(defold_content_helpers.CONSTANT_VERTEX, defold_content_helpers.CONSTANT_TYPE_WORLD,      "u_mtx_world")
        defold_material.add_constant(defold_content_helpers.CONSTANT_VERTEX, defold_content_helpers.CONSTANT_TYPE_WORLDVIEW,  "u_mtx_worldview")
        defold_material.add_constant(defold_content_helpers.CONSTANT_VERTEX, defold_content_helpers.CONSTANT_TYPE_PROJECTION, "u_mtx_projection")
        defold_material.add_constant(defold_content_helpers.CONSTANT_VERTEX, defold_content_helpers.CONSTANT_TYPE_NORMAL,     "u_mtx_normal")

        write_material(defold_material)

    make_project_content(gltf)

def run_dmengine():
    subprocess.run("../%s" % get_dmengine_platform_path(), cwd=get_template_project_path())

def check_prereqs():
    try:
        import pygltflib
    except:
        print("Could not import PyGLTFLib, did you install all prerequisites?")
        sys.exit(-1)

def do_preview(gltf):
    print("Previewing %s file" % gltf)
    check_prereqs()
    make_build_tools()
    make_project(gltf)
    run_dmengine()

def do_clean():
    try:
        os.remove(BUILD_TOOLS_FOLDER)
    except:
        pass
    print("Finished cleaning build folder %s" % BUILD_TOOLS_FOLDER)
