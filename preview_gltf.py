import os
import platform
import shutil
import stat
import subprocess
import sys
import urllib.request
import zipfile

import defold_content_helpers
import blender_utils

# Build paths
BUILD_TOOLS_FOLDER           = "build_tools"
DEFOLD_HTTP_BASE             = "https://d.defold.com/archive/stable"
DEFOLD_SHA                   = "9c44c4a9b6cbc9d0cb66b7027b7c984bf364a568"
DEFOLD_BOB_JAR_URL           = "%s/%s/bob/bob.jar" % (DEFOLD_HTTP_BASE, DEFOLD_SHA)
DEFOLD_DMENGINE_URL_TEMPLATE = "%s/%s/engine/x86_64-%s/dmengine%s"
DEFOLD_PREVIEW_PROJECT_URL   = "https://github.com/defold/pbr-viewer/archive/refs/heads/master.zip"

# Scene content paths
NONE_TEXTURE_PATH = "/builtins/graphics/particle_blob.png"
VERTEX_PATH       = "/assets/shaders/preview.vp"
FRAGMENT_PATH     = "/assets/shaders/preview.fp"

# Generated output paths
MATERIAL_PATH     = "main/%s/materials"
MESH_PATH         = "main/%s/meshes"
TEXTURE_PATH      = "main/%s/textures"
MODEL_PATH        = "main/%s/models"
GAMEOBJECT_PATH   = "main/%s/gameobjects"
COLLECTION_PATH   = "main/%s/collections"

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

def write_material(project_path, material):
    data = material.serialize()
    path = "%s/%s/%s.material" % (get_template_project_path(), MATERIAL_PATH % project_path, material.name)
    with open(path, "w") as f:
        f.write(data)

def write_model(project_path, model):
    data = model.serialize()
    path = "%s/%s/%s.model" % (get_template_project_path(), MODEL_PATH % project_path, model.name)
    with open(path, "w") as f:
        f.write(data)

def write_gameobject(project_path, go):
    data = go.serialize()
    path = "%s/%s/%s.go" % (get_template_project_path(), GAMEOBJECT_PATH % project_path, go.name)
    with open(path, "w") as f:
        f.write(data)

def write_collection(project_path, col):
    data = col.serialize()
    path = "%s/%s/%s.collection" % (get_template_project_path(), COLLECTION_PATH % project_path, col.name)
    with open(path, "w") as f:
        f.write(data)

def write_collection_proxy(col_proxy):
    data = col_proxy.serialize()
    path = "%s/main/preview.collectionproxy" % (get_template_project_path())
    with open(path, "w") as f:
        f.write(data)

def make_project_content(gltf):
    subprocess.run(["java", "-jar", "../bob.jar", "resolve", "build"], cwd=get_template_project_path())

def make_project(gltf):
    project_path = os.path.basename(gltf)

    get_template_project()

    import pygltflib
    from pygltflib.utils import ImageFormat
    gltf_file = pygltflib.GLTF2().load(gltf)

    for x in [TEXTURE_PATH, MATERIAL_PATH, MODEL_PATH, GAMEOBJECT_PATH, COLLECTION_PATH]:
        folder = "%s/%s" % (get_template_project_path(), x % project_path)
        os.makedirs(folder, exist_ok=True)

    image_base_path = "%s/%s" % (get_template_project_path(), TEXTURE_PATH % project_path)
    gltf_base_path = "%s/%s" % (get_template_project_path(), MESH_PATH % project_path)
    blender_utils.run_blender_script("convert_gltf_separate_files.py", [gltf, gltf_base_path])

    defold_collection = defold_content_helpers.collection("content")

    defold_collection_proxy = defold_content_helpers.collection_proxy("preview")
    defold_collection_proxy.set_collection("/main/%s/collections/content.collection" % project_path)

    defold_material_lut = {}
    defold_texture_lut = {}

    def get_texture(tex):
        if tex != None:
            return defold_texture_lut[tex.index]

    gltf_file.convert_images(ImageFormat.FILE, path=image_base_path)
    for i in range(len(gltf_file.images)):
        defold_texture_lut[i] = gltf_file.images[i].name
        image_path_i     = "%s/%s.png" % (image_base_path, i)
        image_path_named = "%s/%s.png" % (image_base_path, gltf_file.images[i].name)
        shutil.move(image_path_i, image_path_named)

    for i in range(len(gltf_file.materials)):
        defold_material = defold_content_helpers.material(gltf_file.materials[i].name)

        defold_material.set_vertex_space(defold_content_helpers.VERTEX_SPACE_WORLD)
        defold_material.set_vertex_program(VERTEX_PATH)
        defold_material.set_fragment_program(FRAGMENT_PATH)

        defold_material.add_tag("model")
        defold_material.add_sampler("tex_base")
        defold_material.add_sampler("tex_metallic_roughness")
        defold_material.add_sampler("tex_normal")
        defold_material.add_sampler("tex_occlusion")
        defold_material.add_sampler("tex_emissive")

        defold_material.add_texture(defold_content_helpers.TEXTURE_BASE,               get_texture(gltf_file.materials[i].pbrMetallicRoughness.baseColorTexture))
        defold_material.add_texture(defold_content_helpers.TEXTURE_METALLIC_ROUGHNESS, get_texture(gltf_file.materials[i].pbrMetallicRoughness.metallicRoughnessTexture))

        defold_material.add_texture(defold_content_helpers.TEXTURE_NORMAL,    get_texture(gltf_file.materials[i].normalTexture))
        defold_material.add_texture(defold_content_helpers.TEXTURE_OCCLUSION, get_texture(gltf_file.materials[i].occlusionTexture))
        defold_material.add_texture(defold_content_helpers.TEXTURE_EMISSIVE,  get_texture(gltf_file.materials[i].emissiveTexture))

        defold_material.add_constant(defold_content_helpers.CONSTANT_VERTEX, defold_content_helpers.CONSTANT_TYPE_VIEW,       "u_mtx_view")
        defold_material.add_constant(defold_content_helpers.CONSTANT_VERTEX, defold_content_helpers.CONSTANT_TYPE_WORLD,      "u_mtx_world")
        defold_material.add_constant(defold_content_helpers.CONSTANT_VERTEX, defold_content_helpers.CONSTANT_TYPE_WORLDVIEW,  "u_mtx_worldview")
        defold_material.add_constant(defold_content_helpers.CONSTANT_VERTEX, defold_content_helpers.CONSTANT_TYPE_PROJECTION, "u_mtx_projection")
        defold_material.add_constant(defold_content_helpers.CONSTANT_VERTEX, defold_content_helpers.CONSTANT_TYPE_NORMAL,     "u_mtx_normal")

        write_material(project_path, defold_material)

        defold_material_lut[defold_material.name] = defold_material

    for i in range(len(gltf_file.nodes)):
        mesh         = gltf_file.meshes[gltf_file.nodes[i].mesh]
        primitive    = mesh.primitives[0]
        material     = gltf_file.materials[primitive.material]

        mesh_path     = "/%s/%s.glb" % (MESH_PATH % project_path, gltf_file.nodes[i].name)
        material_path = "/%s/%s.material" % (MATERIAL_PATH % project_path, material.name)

        defold_model = defold_content_helpers.model(gltf_file.nodes[i].name)
        defold_model.set_mesh(mesh_path)
        defold_model.set_material(material_path)

        defold_material = defold_material_lut[material.name]
        for k,v in defold_material.textures.items():
            tex = v
            if v == None:
                tex = NONE_TEXTURE_PATH
            else:
                tex = "/%s/%s.png" % (TEXTURE_PATH % project_path, v)
            defold_model.add_texture(tex)
        write_model(project_path, defold_model)

        defold_go = defold_content_helpers.gameobject(gltf_file.nodes[i].name)
        defold_go.set_model("/%s/%s.model" % (MODEL_PATH % project_path, gltf_file.nodes[i].name))
        write_gameobject(project_path, defold_go)

        defold_go_path = "/%s/%s.go" % (GAMEOBJECT_PATH % project_path, gltf_file.nodes[i].name)
        defold_collection.add_go(gltf_file.nodes[i].name, defold_go_path)

    write_collection(project_path, defold_collection)

    write_collection_proxy(defold_collection_proxy)

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
