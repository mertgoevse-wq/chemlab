"""
Module 6: Blender Mantaflow Liquid Physics Simulation.
Sets up a complete real-time fluid simulation inside the active chemistry laboratory:
  • Liquid Domain with Level-Set Polygon Meshing (EEVEE / Cycles)
  • Cylindrical Glass Beaker as Collision Effector
  • Continuous Chemical Inflow Emitter (Aqueous Reagent Pouring)
  • Physical Beer-Lambert Volumetric Absorption Material
"""

import bpy


def build_fluid_simulation():
    print(">>> Constructing Mantaflow Fluid Physics & Simulation Domain...")

    col_name = "06_Fluid_Simulation"
    col = bpy.data.collections.get(col_name)
    if not col:
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)

    def link_obj(obj):
        if obj.name not in col.objects:
            col.objects.link(obj)
        for c in list(obj.users_collection):
            if c != col:
                c.objects.unlink(obj)

    # 1. Physics Material: Photorealistic Volumetric Liquid (Copper(II) Sulfate Pentahydrate)
    mat_fluid = bpy.data.materials.get("Mat_Simulated_Liquid") or bpy.data.materials.new(
        name="Mat_Simulated_Liquid"
    )
    mat_fluid.use_nodes = True
    tree = mat_fluid.node_tree
    tree.nodes.clear()

    node_out = tree.nodes.new("ShaderNodeOutputMaterial")
    node_bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
    node_absorb = tree.nodes.new("ShaderNodeVolumeAbsorption")

    # Surface Properties: Ultra-smooth water-like interface
    node_bsdf.inputs["Base Color"].default_value = (0.85, 0.95, 1.0, 1.0)
    node_bsdf.inputs["Roughness"].default_value = 0.005
    node_bsdf.inputs["IOR"].default_value = 1.333  # Refractive index of water at 20°C
    if "Transmission Weight" in node_bsdf.inputs:
        node_bsdf.inputs["Transmission Weight"].default_value = 1.0
    elif "Transmission" in node_bsdf.inputs:
        node_bsdf.inputs["Transmission"].default_value = 1.0

    # Volume Absorption (Cyan/Deep Blue Cu2+ complex ion)
    node_absorb.inputs["Color"].default_value = (0.05, 0.65, 0.95, 1.0)
    node_absorb.inputs["Density"].default_value = 4.5

    tree.links.new(node_bsdf.outputs["BSDF"], node_out.inputs["Surface"])
    tree.links.new(node_absorb.outputs["Volume"], node_out.inputs["Volume"])

    # 2. Reaction Beaker (Effector Obstacle)
    # Location placed upon the main central workbench (Z = 0.90m)
    beaker_loc = (0.0, 0.8, 1.02)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32,
        radius=0.08,
        depth=0.22,
        location=beaker_loc,
    )
    beaker = bpy.context.active_object
    beaker.name = "Sim_Reaction_Beaker"
    link_obj(beaker)

    # Apply glass material
    mat_glass = bpy.data.materials.get("Mat_Borosilicate_Glass")
    if mat_glass:
        beaker.data.materials.append(mat_glass)

    # Add Solidify modifier for wall thickness
    mod_solid = beaker.modifiers.new("Solidify", "SOLIDIFY")
    mod_solid.thickness = 0.006

    # Add Effector Physics to Beaker
    bpy.context.view_layer.objects.active = beaker
    bpy.ops.object.modifier_add(type="FLUID")
    fluid_effector = beaker.modifiers[-1]
    beaker.modifiers["Fluid"].fluid_type = "EFFECTOR"
    beaker.modifiers["Fluid"].effector_settings.effector_type = "COLLISION"
    beaker.modifiers["Fluid"].effector_settings.surface_thickness = 0.004

    # 3. Liquid Inflow Stream (Pouring Source)
    # Positioned 25cm above the beaker
    inflow_loc = (0.0, 0.8, 1.25)
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=16,
        ring_count=12,
        radius=0.022,
        location=inflow_loc,
    )
    inflow = bpy.context.active_object
    inflow.name = "Sim_Liquid_Inflow"
    link_obj(inflow)

    # Add Flow Physics to Inflow
    bpy.context.view_layer.objects.active = inflow
    bpy.ops.object.modifier_add(type="FLUID")
    inflow.modifiers["Fluid"].fluid_type = "FLOW"
    inflow.modifiers["Fluid"].flow_settings.flow_type = "LIQUID"
    inflow.modifiers["Fluid"].flow_settings.flow_behavior = "INFLOW"
    inflow.modifiers["Fluid"].flow_settings.use_initial_velocity = True
    inflow.modifiers["Fluid"].flow_settings.velocity_coord = (0.0, 0.0, -0.6)  # Downward stream

    # 4. Mantaflow Simulation Domain Box
    domain_loc = (0.0, 0.8, 1.15)
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=domain_loc,
    )
    domain = bpy.context.active_object
    domain.name = "Sim_Fluid_Domain"
    domain.scale = (0.35, 0.35, 0.55)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    link_obj(domain)

    # Assign fluid material to domain
    domain.data.materials.append(mat_fluid)

    # Add Domain Physics
    bpy.context.view_layer.objects.active = domain
    bpy.ops.object.modifier_add(type="FLUID")
    domain.modifiers["Fluid"].fluid_type = "DOMAIN"
    domain_settings = domain.modifiers["Fluid"].domain_settings
    domain_settings.domain_type = "LIQUID"
    domain_settings.resolution_max = 64  # Fast, interactive 64-division grid
    domain_settings.use_mesh = True  # Generate surface polygonal geometry
    domain_settings.mesh_scale = 1.0
    domain_settings.particle_scale = 1.0
    domain_settings.use_speed_vectors = True

    # Viscosity: Water at standard temperature
    domain_settings.viscosity_base = 1.0
    domain_settings.viscosity_exponent = 6

    # Animation Frame Range
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 120
    bpy.context.scene.frame_set(1)

    print(">>> Mantaflow Fluid Physics successfully configured on 'Sim_Fluid_Domain'.")
    return domain


if __name__ == "__main__":
    build_fluid_simulation()
