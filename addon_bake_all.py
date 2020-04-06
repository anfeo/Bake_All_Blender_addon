bl_info = {
    "name": "Bake All",
    "author": "Alfonso Annarumma",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "Toolshelf > Layers Tab",
    "description": "Bake All the selected Mesh to a new textures",
    "warning": "",
    "wiki_url": "",
    "category": "Bake",
    }


import bpy
import os
from bpy.types import Operator, Panel, UIList, PropertyGroup
from bpy.props import StringProperty, BoolProperty, IntProperty, CollectionProperty, BoolVectorProperty, PointerProperty

class SCENE_PG_BakeAllProp(PropertyGroup):
    
    float : BoolProperty (name="32 bit Float")
    
    res_x : IntProperty (name="X",
            description="X Resolution of the image", 
            default=1024, 
             min=1, 
            max=2**31-1, 
            soft_min=1, 
            soft_max=1024*4, 
            step=1, 
            subtype='PIXEL')
     
    res_y : IntProperty (name="Y",
            description="Y Resolution of the image", 
            default=1024, 
            min=1, 
            max=2**31-1, 
            soft_min=1, 
            soft_max=1024*4, 
            step=1, 
            subtype='PIXEL')
     
    #name = StringProperty(name="Layer Name")
    save_image : BoolProperty(name="Save Image", default=False)

    image_dir_path : StringProperty(
                    name="Directory Path", 
                    description="The directory to save the baked image", 
                    subtype="DIR_PATH",
                    default="//")
    
class SCENE_BakeAllItem(PropertyGroup):
    name : StringProperty(name="Name")
    
class SCENE_BakeAll_UL_ItemsList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        bakeall_item = item

        

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(bakeall_item, "name", text="", emboss=False)
            


        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            
            

class SCENE_OT_BakeAll_Item_add(bpy.types.Operator):
    """Add Selected Object to list for Baking"""
    bl_idname = "scene.bakeall_add"
    bl_label = "Add Selected Object to list for Baking"

    

    def execute(self, context):
        scene = context.scene
        bakeallitems = scene.bakeallitems
        
        for ob in context.selected_objects:
            if (ob.type == 'MESH') and (ob.name not in bakeallitems):
                 
                bakeall_idx = len(bakeallitems)
                bakeall_item = bakeallitems.add()
                bakeall_item.name = ob.name
                
                scene.bakeallitems_index = bakeall_idx

        return {'FINISHED'}

class SCENE_OT_BakeAll_Item_move(bpy.types.Operator):
    """Add and select a new layer group"""
    bl_idname = "scene.bakeall_item_move"
    bl_label = "Move Object in list for Bake Priority"
    
    move : StringProperty()
    bakeall_idx : IntProperty()
    
    @classmethod
    def poll(cls, context):
        return bool(context.scene)

    def execute(self, context):
        scene = context.scene
        bakeallitems = scene.bakeallitems
        bakeall_idx = self.bakeall_idx
        if self.move == 'UP':
            bakeallitems.move(bakeall_idx, bakeall_idx-1)
            scene.bakeallitems_index = bakeall_idx-1    
        if self.move == 'DOWN':
            bakeallitems.move(bakeall_idx, bakeall_idx+1)
            scene.bakeallitems_index = bakeall_idx+1

        return {'FINISHED'}
        
class SCENE_OT_BakeAll_Item_remove(bpy.types.Operator):
    """Remove object from Bake list"""
    bl_idname = "scene.bake_all_remove"
    bl_label = "Remove object from Bake list"
    
    bakeall_idx : bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        bakeall_idx = self.bakeall_idx

        scene.bakeallitems.remove(bakeall_idx)
        if scene.bakeallitems_index > len(scene.bakeallitems) - 1:
            scene.bakeallitems_index = len(scene.bakeallitems) - 1

        return {'FINISHED'}
    

class SCENE_OT_BakeAll(bpy.types.Operator):
    bl_idname = "object.bake_all"
    bl_label = "Bake All"

    def execute(self, context):
        scn = context.scene
        data =bpy.data
        materials = set()
        #bake_pass = 'AO'
        #scn.cycles.samples = bake_pass.samples
        res_x = scn.bakeallprop.res_x
        res_y = scn.bakeallprop.res_y
        float = scn.bakeallprop.float
        
        image_dir_path = scn.bakeallprop.image_dir_path
        save_image = scn.bakeallprop.save_image
        
        directory = bpy.path.abspath(image_dir_path)
        
        bake_type = context.scene.cycles.bake_type
        bpy.ops.object.select_all(action='DESELECT')
        if not os.path.exists(directory) and save_image:
            os.makedirs(directory)
        
        context.view_layer.objects.active = data.objects[scn.bakeallitems[0].name]
        for item in scn.bakeallitems:
            o = data.objects[item.name]
            if o.type == 'MESH':
                o.select_set(True)
                #controllo che ci siano degli slot pieni
                if o.material_slots.items():
                    
                    
                    #controllo se c'è un materiale assegnato al primo slot
                    if o.material_slots[0].material == False:
                        
                        #se non c'è un materiale lo creo e lo assegno allo slot 0
                        mat = bpy.data.materials.new(name=o.name+"Material_bake")
                        o.material_slots[0].material = mat
                    
                    #se c'è un materiale lo prelevo e lo metto nella variabile mat
                    else:
                        if o.material_slots[0].material.users >1:
                            mat = o.material_slots[0].material.copy()    
                            o.material_slots[0].material = mat
                        else:
                            mat = o.material_slots[0].material
                             
                
                else:
                    #se non c'è neanche uno slot, creo un material e lo appendo all'oggetto
                                   
                    mat = data.materials.new(name=o.name+"Material_bake")
                    o.data.materials.append(mat)
                    
                for slot in o.material_slots:
                    if slot.name != '':
                        mat = slot.material 
                
                        #setto come materiale attivo il primo
                        #o.active_material_index = 0
                        
                        #abilito i nodi nel materiali e assegno l'immagine ad un nodo
                        bpy.data.materials[mat.name].use_nodes = True
                        
                        node_tree = bpy.data.materials[mat.name].node_tree
                        
                        #variabili per la generazione del nodo immagine
                        
                        
                        
                        image_dir_path = scn.bakeallprop.image_dir_path
                        
                        node_name = bake_type+"bake_all_image_jxk"
                        
                        img_name = bake_type+"_"+o.name+"_bake"
                        
                        filepath = image_dir_path+img_name
                        
                        
                        # controllo che l'immagine non sia già presente in libreria
                        if img_name in data.images:
                            img = data.images[img_name]
                        # se no ne creo una
                        else:
                            img = data.images.new(img_name, res_x, res_y, alpha=True, float_buffer=float)
                            img.filepath = filepath+"."+img.file_format
                        
                        #controllo che il nodo non ci sia già
                        #se non c'è lo creo
                        if not node_name in node_tree.nodes:
                            
                            node = node_tree.nodes.new("ShaderNodeTexImage")
                            node.name = node_name
                        
                        else:    
                            node = node_tree.nodes[node_name]
                        
                        node.image = img   
                        node.select = True
                        node_tree.nodes.active = node
                
            else:
                o.select_set(False)
                      
        if save_image:
            
            bpy.ops.object.bake(type = bake_type)
            bpy.ops.object.bake_all_save_image()
        
        else:    
            bpy.ops.object.bake("INVOKE_SCREEN",type = bake_type)
        
        
        
       
        
        
        return {'FINISHED'}
    
#    def execute(context):
#        if save_image:
#            bpy.ops.object.object.bake_all_save_image()
#        return {'FINISHED'}
#                    
class SCENE_OT_BakeAllSaveImage(bpy.types.Operator):
    """Save All baked image"""
    bl_idname = "object.bake_all_save_image"
    bl_label = "Save Image"

    

    def execute(self, context):
        images = bpy.data.images
        scene = context.scene
        image_dir_path = scene.bakeallprop.image_dir_path
        
        
        for img in images:
            
            if "_bake" in img.name and img.users == 1 and img.has_data:
                
                
                #ext = "."+img.file_format
                
                #img.filepath = image_dir_path+img.name+ext
                
                img.save()
            
                
                       
    

        return {'FINISHED'}
    
        
class SCENE_PT_BakeAllPanel(bpy.types.Panel):
    """Panel for Bake All"""
    bl_label = "Bake All Settings"
    bl_idname = "RENDER_PT_Bake_All"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_category = "Bake All"
    COMPAT_ENGINES = {'CYCLES'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.object
        prop = context.scene.bakeallprop
        group_idx = scene.bakeallitems_index
        
        layout = self.layout
        
        

        
        
        row = layout.row()
        col = row.column()
        
        col.template_list("SCENE_BakeAll_UL_ItemsList", "", scene, "bakeallitems", scene, "bakeallitems_index", rows=3)

        col = row.column(align=True)
        col.operator("scene.bakeall_add", icon='ADD', text="")
        col.operator("scene.bake_all_remove", icon='REMOVE', text="").bakeall_idx = group_idx
        
        
        up = col.operator("scene.bakeall_item_move", icon='TRIA_UP', text="")
        down =col.operator("scene.bakeall_item_move", icon='TRIA_DOWN', text="")
        up.bakeall_idx = group_idx
        down.bakeall_idx = group_idx
        up.move = 'UP'
        down.move = 'DOWN'
        
        if len(scene.bakeallitems)>0:
            row = layout.row()
            
            row.prop(scene.cycles, "samples")
            
            
            row = layout.row()
            col =row.column(align=True)
            col.label(text="Image Resolution:")
            col.prop(prop, "res_x")
            col.prop(prop, "res_y")
            col.prop(prop, "float")
            
            
            
            if bpy.data.is_saved:
                enable = True
                
            else:
                enable = False
            
            
            
            row = layout.row()
            row.operator("object.bake_all")
            
            
            
            row = layout.row()
            row.enabled = enable
            row.prop(prop, "save_image", text="Auto Save images")
            
            if prop.save_image:
                
                row = layout.row()
                row.enabled = enable
                row.prop(prop, "image_dir_path")


classes = ( 
    SCENE_OT_BakeAll,
    SCENE_OT_BakeAllSaveImage,
    SCENE_OT_BakeAll_Item_remove,
    SCENE_OT_BakeAll_Item_move,
    SCENE_OT_BakeAll_Item_add,
    SCENE_PT_BakeAllPanel,
    SCENE_PG_BakeAllProp,
    SCENE_BakeAll_UL_ItemsList,
    SCENE_BakeAllItem,
    
)




def register():
    
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
    
    
    bpy.types.Scene.bakeallitems = CollectionProperty(type=SCENE_BakeAllItem)
    # Unused, but this is needed for the TemplateList to work...
    bpy.types.Scene.bakeallitems_index = IntProperty(default=-1)
    
    bpy.types.Scene.bakeallprop = PointerProperty(type=SCENE_PG_BakeAllProp)
    
def unregister():
   
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    
    del bpy.types.Scene.bakeallitems_index
    del bpy.types.Scene.bakeallitems
    del bpy.types.Scene.bakeallprop


if __name__ == "__main__":
    register()