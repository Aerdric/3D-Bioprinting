bl_info = {
    "name": "Pores Gradient",
    "author": "Alexander Benz",
    "version": (1, 0),
    "blender": (3, 3, 1),
    "location": "View3D",
    "description": "Add a 3D scaffold to an object",
    "warning": "",
    "doc_url": "",
    "category": "Modify Mesh",
}

import bpy
import addon_utils


"""###############"""
"""### Methods ###"""
"""###############"""

def enable_addon(addon_module_name):
    loaded_default, loaded_state = addon_utils.check(addon_module_name)
    if not loaded_state:
        addon_utils.enable(addon_module_name)

def enable_mod_tools():
    """enable Modifier Tools addon"""
    enable_addon(addon_module_name="space_view3d_modifier_tools")

def init():
    clean_scene()
    enable_mod_tools()
    """ set units to micrometers and set the grid to 10μm """
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 0.000001
    bpy.context.scene.unit_settings.length_unit = 'MICROMETERS'
    bpy.context.scene.use_gravity = False

    c_area = 'VIEW_3D'
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if not area.type == c_area:
                continue

            for s in area.spaces:
                if s.type == c_area:
                    s.overlay.grid_scale = 1e-05
                    break
    
    for a in bpy.context.screen.areas:
        if a.type == c_area:
            a.spaces.active.clip_start = 5
            a.spaces.active.clip_end = 1e+06
            break
    """create collections"""
    #scene_collection = bpy.context.scene.collection
    body_collection = bpy.data.collections.new("Body Collection")
    scaffold_collection = bpy.data.collections.new("Scaffold Collection")
    bpy.context.scene.collection.children.link(body_collection)
    bpy.context.scene.collection.children.link(scaffold_collection)

def unlink_object(collection, object):    
    collection.objects.unlink(object)


def clean_scene():
    """
    Removing all of the objects, collection, materials, particles,
    textures, images, curves, meshes, actions, nodes, and worlds from the scene
    """
    # make sure the active object is not in Edit Mode
    if bpy.context.active_object and bpy.context.active_object.mode == "EDIT":
        bpy.ops.object.editmode_toggle()

    # make sure non of the objects are hidden from the viewport, selection, or disabled
    for obj in bpy.data.objects:
        obj.hide_set(False)
        obj.hide_select = False
        obj.hide_viewport = False

    # select all the object and delete them (just like pressing A + X + D in the viewport)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    # find all the collections and remove them
    collection_names = [col.name for col in bpy.data.collections]
    for name in collection_names:
        bpy.data.collections.remove(bpy.data.collections[name])
    purge_orphans()



def purge_orphans():
    """Remove all orphan data blocks"""
    if bpy.app.version >= (3, 0, 0):
        # run this only for Blender versions 3.0 and higher
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    else:
        # run this only for Blender versions lower than 3.0
        # call purge_orphans() recursively until there are no more orphan data blocks to purge
        result = bpy.ops.outliner.orphans_purge()
        if result.pop() != "CANCELLED":
            purge_orphans()


def make_active(object):
    # deselect all objects and make object active
    bpy.ops.object.select_all(action='DESELECT')
    object.select_set(True)
    bpy.context.view_layer.objects.active = object


def active_object():
    return bpy.context.active_object


def merge_to_object(target, object):
    # merge object to target
    make_active(target)
    bpy.ops.object.modifier_add(type='BOOLEAN')
    target.modifiers["Boolean"].operation = 'UNION'
    target.modifiers["Boolean"].solver = 'EXACT'
    target.modifiers["Boolean"].object = object
    bpy.ops.object.apply_all_modifiers()



"""##############"""
"""### Meshes ###"""
"""##############"""




def create_default_body():
    # create a cube in size 2x1x0.15 [mm] with corner at Location (0,0,0)
    collection = bpy.data.collections["Body Collection"]
    bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(1000, 500, 75), scale=(1000, 500, 75))
    obj = active_object()
    obj.name = "Body"
    collection.objects.link(obj)
    make_active(obj)
    bpy.context.scene.collection.objects.unlink(obj)
    

def create_scaffold(wall, body_x, body_y, body_z, diameter_sph, grad_sph_x, grad_sph_y, grad_sph_z, diameter_cyl, grad_cyl_x, grad_cyl_y, grad_cyl_z, ppmm, ppmm_grad_x, ppmm_grad_y, ppmm_grad_z):
    # set collection in use
    collection = bpy.data.collections["Scaffold Collection"]
    # create empty mesh
    scaffold_mesh = bpy.data.meshes.new('scaffold_mesh')
    scaffold_object = bpy.data.objects.new('scaffold_object', scaffold_mesh)
    collection.objects.link(scaffold_object)
    # distance between spheres
    dist = int(1000/ppmm)
    x_dist = dist
    y_dist = dist
    z_dist = dist
    # radius sphere
    rad_sph = diameter_sph/2
    rad_sph_x = rad_sph
    rad_sph_y = rad_sph
    rad_sph_z = rad_sph
    # radius cylinder
    rad_cyl = diameter_cyl/2
    rad_cyl_x = rad_cyl -(body_x/1000 * grad_cyl_x)
    rad_cyl_y = rad_cyl -(body_y/1000 * grad_cyl_x)
    rad_cyl_z = rad_cyl -(body_z/1000 * grad_cyl_x)
    # parameters x, y, z
    x0 = int(wall + rad_sph)
    x1 = int(body_x - (wall + rad_sph))
    y0 = int(wall + rad_sph)
    y1 = int(body_y - (wall + rad_sph))
    z0 = int(wall + rad_sph)
    z1 = int(body_z - (wall + rad_sph))
    
    """### Create Mesh Loop ###"""
    """ init """
    c0=1
    """ reset before z loop """
    z=z0
    z_dist = dist
    while z <= z1:
        rad_sph_y = rad_sph_z
        
        """ reset before y loop """
        y=y0
        y_dist = dist
        while y <= y1:
            y_dist += ppmm_grad_y
            rad_sph_x = rad_sph_y
            
            """ reset before x loop """
            x=x0
            x_dist = dist
            while x <= x1:
                x_dist += ppmm_grad_x
                
                """ runtime test """
                print(c0," - ",x,y,z)
                c0+=1
                
                """ create sphere """          
                create_sphere(collection, scaffold_object, rad_sph_x, (x, y, z))
                
                """ create channels """
                # needs to be added: second cylinder radius calculation
                if x==x0:
                    create_cylinder(collection, scaffold_object, rad_cyl, rad_cyl_x, (x1/2, y, z), (0, 1.5708, 0), body_x+100)
                if y==y0:
                    create_cylinder(collection, scaffold_object, rad_cyl, rad_cyl_y, (x, y1/2, z), (1.5708, 0, 0), body_y+100)
                if z==z0:
                    create_cylinder(collection, scaffold_object, rad_cyl, rad_cyl_z, (x, y, z1/2), (0, 0, 0), body_z+100)
                
                """run at the end of each x loop"""
                rad_sph_x += grad_sph_x
                if x_dist >= diameter_sph:
                    x += x_dist
                else:
                    x += diameter_sph
                
            """run at the end of each y loop"""
            rad_sph_y += grad_sph_y
            if y_dist >= diameter_sph:
                y += y_dist
            else:
                y += diameter_sph
            
        """run at the end of each z loop"""
        rad_sph_z += grad_sph_z
        if z_dist >= diameter_sph:
            z += z_dist
        else:
            z += diameter_sph



""" remove scaffold object from body object"""
def modify_body():
    # set collections
    collection = bpy.data.collections["Body Collection"]
    scaffold_collection = bpy.data.collections["Scaffold Collection"]
    # set body object
    body = collection.objects["Body"]
    make_active(body)
    # create and apply boolean modifiers
    bpy.ops.object.modifier_add(type='BOOLEAN')
    body.modifiers["Boolean"].operation = 'DIFFERENCE'
    body.modifiers["Boolean"].solver = 'EXACT'
    body.modifiers["Boolean"].object = scaffold_collection.objects["scaffold_object"]
    bpy.ops.object.apply_all_modifiers()
    # remove scaffold object when done
    scaffold_collection.objects.unlink(scaffold_collection.objects["scaffold_object"])
    


def create_sphere(collection, scaffold_object, i_rad, i_location):
    # create a sphere and add it to the given object in the given collection
    bpy.ops.mesh.primitive_uv_sphere_add(segments= 12, ring_count= 6,radius=i_rad, enter_editmode=False, align='WORLD', location=i_location, scale=(1, 1, 1))
    obj = active_object()
    collection.objects.link(obj)
    bpy.context.scene.collection.objects.unlink(obj)
    #reduce_polygons(obj)
    merge_to_object(scaffold_object, obj)
    unlink_object(collection, obj)

def create_cylinder(collection, scaffold_object, w_rad_cyl, w_rad_cyl_2, i_location, i_rot, i_length):
    bpy.ops.mesh.primitive_cone_add(radius1=w_rad_cyl, radius2=w_rad_cyl_2, depth=i_length, enter_editmode=False, align='WORLD', location=i_location, rotation=i_rot, scale=(1, 1, 1))

    #bpy.ops.mesh.primitive_cylinder_add(radius=w_rad_cyl, depth=i_length, enter_editmode=False, align='WORLD', location=i_location, rotation=i_rot, scale=(1, 1, 1))
    obj = active_object()
    collection.objects.link(obj)
    bpy.context.scene.collection.objects.unlink(obj)
    #reduce_polygons(obj)
    merge_to_object(scaffold_object, obj)
    unlink_object(collection, obj)

    
"""#################"""
"""### Operators ###"""
"""#################"""

""" init Operator """
class OperatorInit(bpy.types.Operator):
    bl_idname = "object.init_operator"
    bl_label = "Reset Scene"
    def execute(self, context):
        init()
        return {'FINISHED'}

""" set body operator """
class OperatorSetBody(bpy.types.Operator):
    bl_idname = "object.set_body_operator"
    bl_label = "Set Active object as Body"
    
    def execute(self, context):
        obj = active_object()
        obj.name = "Body"
        return {'FINISHED'}

""" create body operator """
class OperatorCreateBody(bpy.types.Operator):
    bl_idname = "object.create_body_operator"
    bl_label = "Create Default Body"
    
    def execute(self, context):
        create_default_body()
        return {'FINISHED'}

""" create scaffold operator sphere """
class OperatorCreateScaffold(bpy.types.Operator):
    bl_idname = "object.create_scaffold_operator"
    bl_label = "Create Scaffold Sphere"
    
    # create user variables
    wall : bpy.props.IntProperty(name="Wall")
    body_x : bpy.props.IntProperty(name="Body size x")
    body_y : bpy.props.IntProperty(name="Body size y")
    body_z : bpy.props.IntProperty(name="Body size z")
    
    diameter_sph : bpy.props.IntProperty(name="Ø Sphere [μm]", min= 50, max= 500)
    grad_sph_x : bpy.props.IntProperty(name="x grad")
    grad_sph_y : bpy.props.IntProperty(name="y grad")
    grad_sph_z : bpy.props.IntProperty(name="z grad")
    
    diameter_cyl : bpy.props.IntProperty(name="Ø Cylinder [μm]", min= 5, max= 150)
    grad_cyl_x : bpy.props.IntProperty(name="x grad")
    grad_cyl_y : bpy.props.IntProperty(name="y grad")
    grad_cyl_z : bpy.props.IntProperty(name="z grad")
    
    ppmm : bpy.props.IntProperty(name="Pores per mm", min= 1, max= 10)
    ppmm_grad_x : bpy.props.IntProperty(name="x grad [μm]", min= -100, max= 100)
    ppmm_grad_y : bpy.props.IntProperty(name="y grad [μm]", min= -100, max= 100)
    ppmm_grad_z : bpy.props.IntProperty(name="z grad [μm]", min= -100, max= 100)
    
    def invoke(self, context, event):
        # set default values, if not mentioned default = 0
        self.wall = 20
        self.body_x = 2000
        self.body_y = 1000
        self.body_z = 150
        
        self.diameter_sph = 100
        self.grad_sph_x = -2
        self.grad_sph_y = -2
        self.grad_sph_z = 0
        
        self.diameter_cyl = 20
        self.grad_cyl_x = -5
        self.grad_cyl_y = -5
        self.grad_cyl_z = 0
        
        self.ppmm = 2
        self.ppmm_grad_x = -5
        self.ppmm_grad_y = -5
        self.ppmm_grad_z = 0
        
        
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
 
    def execute(self, context):
        # create sphere scaffold mesh with the given parameters
        #mesh.create_scaffold_sphere(self.int_por_dia, self.int_por_grad_x, self.int_por_grad_y, self.int_por_grad_z, self.int_cyl_dia, self.int_cyl_grad_x, self.int_ppmm, self.int_ppmm_grad_x, self.int_ppmm_grad_y, self.int_ppmm_grad_z)
        create_scaffold(self.wall,self.body_x,self.body_y,self.body_z,self.diameter_sph, self.grad_sph_x, self.grad_sph_y, self.grad_sph_z, self.diameter_cyl, self.grad_cyl_x, self.grad_cyl_y, self.grad_cyl_z, self.ppmm, self.ppmm_grad_x, self.ppmm_grad_y, self.ppmm_grad_z)
        return {'FINISHED'}

    

""" modify body operator """
class OperatorModifyBody(bpy.types.Operator):
    bl_idname = "object.modify_body_operator"
    bl_label = "Modify Body"
    
    def invoke(self, context, event):
        collection = bpy.data.collections["Scaffold Collection"]
        # set body object
        #body = collection.objects["scaffold_object"]
        
        for item in collection.objects:
            if item == None:
                continue
            print(item)
        
        w_enum : bpy.props.EnumProperty(
        name= "",
        description= "what object shall be used as scaffold",
        items= [
                ]
        )
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def execute(self, context):
        if bpy.data.collections["Body Collection"].objects["Body"] != None:
            modify_body()
        else:
            print("Holz")
        return {'FINISHED'}


    
"""##############"""
"""### Panels ###"""
"""##############"""

class CustomProperties(bpy.types.PropertyGroup):
    w_enum : bpy.props.EnumProperty(
        name= "",
        description= "which scaffold option is beeing used",
        items= [ ('OP1',"Spheres",""),
                ('OP2',"Diamond",""),
                ('OP3',"Gyroid","")
                ]
        )



""" Init Panel """
class InitPanel(bpy.types.Panel):
    bl_idname = "panel_init"
    bl_label = "Initialization"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Bioprinting"

    def draw(self,context):
        layout = self.layout
        scene = context.scene
        
        row = layout.row()
        row.operator("object.init_operator")

        

""" Body Panel """
class BodyPanel(bpy.types.Panel):
    bl_idname = "panel_set_body"
    bl_label = "Set Body"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Bioprinting"

    def draw(self,context):
        layout = self.layout
        scene = context.scene
        
        row = layout.row()
        row.label(text= "Body")
        row = layout.row()
        row.operator("object.create_body_operator")
        row = layout.row()
        row.operator("object.set_body_operator")
        


""" Scaffold Panel """
class ScaffoldPanel(bpy.types.Panel):
    bl_idname = "panel_create_scaffold"
    bl_label = "Create Scaffold"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Bioprinting"
    
    def draw(self,context):
        layout = self.layout
        scene = context.scene
        
        row = layout.row()
        row.label(text= "Choose scaffold")
        row = layout.row()
        row.operator('object.create_scaffold_operator', text='Execute')
      
        
""" Modify Panel """
class ModifyPanel(bpy.types.Panel):
    bl_idname = "panel_modify_object"
    bl_label = "Modify Body"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Bioprinting"
    

    def draw(self,context):
        layout = self.layout
        scene = context.scene
        # modify body   	 
        row = layout.row()
        row.operator("object.modify_body_operator", text='Execute')




"""################"""
"""### Register ###"""
"""################"""

classes = [
    OperatorInit, 
    OperatorSetBody, 
    OperatorCreateBody, 
    OperatorCreateScaffold,
    OperatorModifyBody,
    InitPanel,
    BodyPanel,
    ScaffoldPanel,
    ModifyPanel,
    ]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    init()
    register()