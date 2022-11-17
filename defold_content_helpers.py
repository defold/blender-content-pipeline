import inspect

## Constants
CONSTANT_VERTEX   = 0
CONSTANT_FRAGMENT = 1

## Constant types
CONSTANT_TYPE_VEC4       = "CONSTANT_TYPE_USER"
CONSTANT_TYPE_MAT4       = "CONSTANT_TYPE_USER_MATRIX4"
CONSTANT_TYPE_WORLDVIEW  = "CONSTANT_TYPE_WORLDVIEW"
CONSTANT_TYPE_WORLD      = "CONSTANT_TYPE_WORLD"
CONSTANT_TYPE_VIEW       = "CONSTANT_TYPE_VIEW"
CONSTANT_TYPE_PROJECTION = "CONSTANT_TYPE_PROJECTION"
CONSTANT_TYPE_NORMAL     = "CONSTANT_TYPE_NORMAL"

VERTEX_SPACE_WORLD       = "VERTEX_SPACE_WORLD"
VERTEX_SPACE_LOCAL       = "VERTEX_SPACE_LOCAL"

def serialize_tag(tag):
    return "tags: \"%s\"" % tag

def serialize_sampler(sampler):
    SAMPLER_TEMPLATE = inspect.cleandoc("""
            samplers {{
                name: \"{name}\"
                wrap_u: WRAP_MODE_REPEAT
                wrap_v: WRAP_MODE_REPEAT
                filter_min: FILTER_MODE_MIN_LINEAR
                filter_mag: FILTER_MODE_MAG_LINEAR
            }}
            """)
    return SAMPLER_TEMPLATE.format(name = sampler)

def serialize_vec4(self, value):
    VEC4_VALUE_TEMPLATE = inspect.cleandoc("""
        value: {{
            x: {x}
            y: {y}
            z: {z}
            w: {w}
        }}
        """)
    return VEC4_VALUE_TEMPLATE.format(
        x = value[0],
        y = value[1],
        z = value[2],
        w = value[3])

def serialize_constant(sh_type, c_entry):
    sh_type_str = ""
    if sh_type == CONSTANT_VERTEX:
        sh_type_str = "vertex_constants"
    elif sh_type == CONSTANT_FRAGMENT:
        sh_type_str = "fragment_constants"

    CONSTANT_TEMPLATE = inspect.cleandoc("""
        {shader} {{
            name: \"{name}\"
            type: {type}
            {value}
        }}
        """)

    val = ""
    if c_entry["value"] != None:
        if c_entry["type"] == CONSTANT_TYPE_MAT4:
            for v in c_entry["value"]:
                val += serialize_vec4(v)
        if c_entry["type"] == CONSTANT_TYPE_VEC4:
            val += serialize_vec4(c_entry["value"])

    return CONSTANT_TEMPLATE.format(
        shader = sh_type_str,
        name   = c_entry["name"],
        type   = c_entry["type"],
        value  = val)

class material(object):
    def __init__(self, name):
        self.name               = name
        self.vertex_space       = ""
        self.vertex_program     = ""
        self.vertex_constants   = []
        self.fragment_program   = ""
        self.fragment_constants = []
        self.samplers           = []
        self.tags               = []

    def set_vertex_space(self, space):
        self.vertex_space = space

    def set_vertex_program(self, path):
        self.vertex_program = path

    def set_fragment_program(self, path):
        self.fragment_program = path

    def add_sampler(self, tex_obj, sampler_name):
        self.samplers.append(sampler_name)

    def add_tag(self, tag):
        self.tags.append(tag)

    def add_constant(self, sh_type, c_type, c_name, c_value = None):
        constants = None
        if sh_type == CONSTANT_VERTEX:
            constants = self.vertex_constants
        elif sh_type == CONSTANT_FRAGMENT:
            constants = self.fragment_constants
        constants.append({
            "name"  : c_name,
            "type"  : c_type,
            "value" : c_value
        })

    def serialize(self):
        print("Serializing " + self.name)

        output_template = inspect.cleandoc(
            """
            {name}
            {tags}
            {vertex_program}
            {fragment_program}
            {vertex_space}
            {vertex_constants}
            {fragment_constants}
            {samplers}
            """)

        mat_name        = "name: \"%s\"" % self.name
        fs_program_path = "fragment_program: \"%s\"" % self.fragment_program
        vx_program_path = "vertex_program: \"%s\"" % self.vertex_program
        vx_space        = "vertex_space: %s" % self.vertex_space

        samplers_str = ""
        for x in self.samplers:
            samplers_str += serialize_sampler(x) + "\n"

        vx_constants_str = ""
        for x in self.vertex_constants:
            vx_constants_str += serialize_constant(CONSTANT_VERTEX, x) + "\n"

        fs_constants_str = ""
        for x in self.fragment_constants:
            fs_constants_str += serialize_constant(CONSTANT_FRAGMENT, x) + "\n"

        tags_str = ""
        for x in self.tags:
            tags_str += serialize_tag(x)

        return output_template.format(
            name               = mat_name,
            tags               = tags_str,
            vertex_program     = vx_program_path,
            fragment_program   = fs_program_path,
            vertex_space       = vx_space,
            vertex_constants   = vx_constants_str,
            fragment_constants = fs_constants_str,
            samplers           = samplers_str)
