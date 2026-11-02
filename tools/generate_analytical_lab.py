"""
Generator for Godot 4 3D Analytical Chemistry Laboratory scene.
Builds res://scenes/laboratories/analytical_lab.tscn with:
- 10m x 8m x 3.5m cleanroom architecture (epoxy floor, wall panels with warning stripes and kickplates, acoustic ceiling with 6 LED panels)
- Central Main Workbench (3.0m x 1.2m x 0.9m) with reagent shelf rack and under-bench cabinetry
- Analytical Balance Station with granite slab table against North wall
- Fume Hood Station (ANSI/AIHA Z9.5 certified) with movable sash glass, exhaust plenum, and interior light
- Wash & Waste Station with polypropylene sink, deionized water tap, drying rack, and 3 waste carboys
- Emergency Safety Station with deluge shower and eye-wash station
- Intel Iris Xe optimized lighting: 4000 K ambient, bench spotlight, fume hood interior light
- Transform spawn markers and pre-placed apparatus instances (Flask, Beaker, Bunsen Burner, Magnetic Stirrer, Analytical Balance, Reagents)
- Collision setup on all surfaces (floor, walls, ceiling, furniture)
"""

from pathlib import Path

OUTPUT_PATH = Path(
    r"C:\Users\Win11 Pro\Desktop\chemlab\game\scenes\laboratories\analytical_lab.tscn"
)

SCENE_CONTENT = """[gd_scene load_steps=38 format=3 uid="uid://chemlab_analytical_lab_01"]

[ext_resource type="Script" path="res://scenes/laboratories/analytical_lab.gd" id="1_lab_script"]
[ext_resource type="Environment" path="res://default_env.tres" id="2_lab_env"]
[ext_resource type="PackedScene" path="res://scenes/player/player_controller.tscn" id="3_player"]
[ext_resource type="PackedScene" path="res://scenes/apparatus/analytical_balance.tscn" id="4_balance"]
[ext_resource type="PackedScene" path="res://scenes/apparatus/magnetic_stirrer.tscn" id="5_stirrer"]
[ext_resource type="PackedScene" path="res://scenes/apparatus/titration_buret.tscn" id="6_buret"]
[ext_resource type="PackedScene" path="res://scenes/apparatus/bunsen_burner.tscn" id="7_burner"]
[ext_resource type="PackedScene" path="res://scenes/apparatus/erlenmeyer_flask.tscn" id="8_erlenmeyer"]
[ext_resource type="PackedScene" path="res://scenes/apparatus/beaker.tscn" id="9_beaker"]
[ext_resource type="PackedScene" path="res://scenes/quests/quest_overlay.tscn" id="10_quest_overlay"]

[sub_resource type="StandardMaterial3D" id="Mat_FloorEpoxy"]
albedo_color = Color(0.72, 0.77, 0.82, 1)
metallic = 0.05
roughness = 0.22

[sub_resource type="BoxMesh" id="Mesh_Floor"]
material = SubResource("Mat_FloorEpoxy")
size = Vector3(10, 0.1, 8)

[sub_resource type="BoxShape3D" id="Shape_Floor"]
size = Vector3(10, 0.1, 8)

[sub_resource type="StandardMaterial3D" id="Mat_CleanroomWall"]
albedo_color = Color(0.92, 0.94, 0.95, 1)
roughness = 0.45

[sub_resource type="BoxMesh" id="Mesh_Wall_NS"]
material = SubResource("Mat_CleanroomWall")
size = Vector3(10, 3.5, 0.2)

[sub_resource type="BoxShape3D" id="Shape_Wall_NS"]
size = Vector3(10, 3.5, 0.2)

[sub_resource type="BoxMesh" id="Mesh_Wall_EW"]
material = SubResource("Mat_CleanroomWall")
size = Vector3(0.2, 3.5, 8)

[sub_resource type="BoxShape3D" id="Shape_Wall_EW"]
size = Vector3(0.2, 3.5, 8)

[sub_resource type="StandardMaterial3D" id="Mat_Kickplate"]
albedo_color = Color(0.15, 0.16, 0.18, 1)
roughness = 0.35

[sub_resource type="BoxMesh" id="Mesh_Kickplate_NS"]
material = SubResource("Mat_Kickplate")
size = Vector3(10, 0.2, 0.04)

[sub_resource type="BoxMesh" id="Mesh_Kickplate_EW"]
material = SubResource("Mat_Kickplate")
size = Vector3(0.04, 0.2, 8)

[sub_resource type="StandardMaterial3D" id="Mat_WarningStripe"]
albedo_color = Color(0.02, 0.55, 0.75, 1)
roughness = 0.25

[sub_resource type="BoxMesh" id="Mesh_Stripe_NS"]
material = SubResource("Mat_WarningStripe")
size = Vector3(10, 0.15, 0.02)

[sub_resource type="BoxMesh" id="Mesh_Stripe_EW"]
material = SubResource("Mat_WarningStripe")
size = Vector3(0.02, 0.15, 8)

[sub_resource type="StandardMaterial3D" id="Mat_AcousticCeiling"]
albedo_color = Color(0.88, 0.89, 0.9, 1)
roughness = 0.85

[sub_resource type="BoxMesh" id="Mesh_Ceiling"]
material = SubResource("Mat_AcousticCeiling")
size = Vector3(10, 0.1, 8)

[sub_resource type="BoxShape3D" id="Shape_Ceiling"]
size = Vector3(10, 0.1, 8)

[sub_resource type="StandardMaterial3D" id="Mat_LEDPanel"]
albedo_color = Color(1, 0.98, 0.95, 1)
emission_enabled = true
emission = Color(1, 0.98, 0.95, 1)
emission_energy_multiplier = 3.5

[sub_resource type="BoxMesh" id="Mesh_LEDPanel"]
material = SubResource("Mat_LEDPanel")
size = Vector3(1.2, 0.04, 0.6)

[sub_resource type="StandardMaterial3D" id="Mat_PhenolicBenchTop"]
albedo_color = Color(0.12, 0.13, 0.15, 1)
metallic = 0.08
roughness = 0.22

[sub_resource type="BoxMesh" id="Mesh_MainBenchTop"]
material = SubResource("Mat_PhenolicBenchTop")
size = Vector3(3, 0.05, 1.2)

[sub_resource type="BoxShape3D" id="Shape_MainWorkbench"]
size = Vector3(3, 0.9, 1.2)

[sub_resource type="StandardMaterial3D" id="Mat_CabinetLaminate"]
albedo_color = Color(0.9, 0.92, 0.94, 1)
roughness = 0.4

[sub_resource type="BoxMesh" id="Mesh_Cabinet"]
material = SubResource("Mat_CabinetLaminate")
size = Vector3(1.1, 0.74, 1.0)

[sub_resource type="StandardMaterial3D" id="Mat_SteelFrame"]
albedo_color = Color(0.85, 0.88, 0.9, 1)
metallic = 0.4
roughness = 0.35

[sub_resource type="BoxMesh" id="Mesh_ShelfStanchion"]
material = SubResource("Mat_SteelFrame")
size = Vector3(0.04, 0.65, 0.04)

[sub_resource type="StandardMaterial3D" id="Mat_ReagentShelf"]
albedo_color = Color(0.88, 0.92, 0.95, 1)
roughness = 0.2

[sub_resource type="BoxMesh" id="Mesh_ReagentShelf"]
material = SubResource("Mat_ReagentShelf")
size = Vector3(2.2, 0.03, 0.35)

[sub_resource type="StandardMaterial3D" id="Mat_PolishedGranite"]
albedo_color = Color(0.08, 0.08, 0.09, 1)
metallic = 0.05
roughness = 0.12

[sub_resource type="BoxMesh" id="Mesh_GraniteTop"]
material = SubResource("Mat_PolishedGranite")
size = Vector3(1.6, 0.08, 0.8)

[sub_resource type="BoxShape3D" id="Shape_BalanceTable"]
size = Vector3(1.6, 0.9, 0.8)

[sub_resource type="BoxMesh" id="Mesh_BalanceBase"]
material = SubResource("Mat_SteelFrame")
size = Vector3(1.4, 0.82, 0.7)

[sub_resource type="StandardMaterial3D" id="Mat_FumeHoodCasing"]
albedo_color = Color(0.88, 0.9, 0.92, 1)
roughness = 0.3

[sub_resource type="BoxMesh" id="Mesh_FumeHoodBase"]
material = SubResource("Mat_FumeHoodCasing")
size = Vector3(1.9, 0.9, 1.0)

[sub_resource type="BoxShape3D" id="Shape_FumeHood"]
size = Vector3(1.9, 2.4, 1.0)

[sub_resource type="BoxMesh" id="Mesh_FumeHoodUpper"]
material = SubResource("Mat_FumeHoodCasing")
size = Vector3(1.9, 1.5, 1.0)

[sub_resource type="StandardMaterial3D" id="Mat_FumeHoodInterior"]
albedo_color = Color(0.95, 0.96, 0.98, 1)
roughness = 0.15

[sub_resource type="BoxMesh" id="Mesh_FumeHoodWorkDeck"]
material = SubResource("Mat_FumeHoodInterior")
size = Vector3(1.7, 0.04, 0.85)

[sub_resource type="CylinderMesh" id="Mesh_ExhaustPlenum"]
material = SubResource("Mat_SteelFrame")
top_radius = 0.18
bottom_radius = 0.18
height = 1.1

[sub_resource type="StandardMaterial3D" id="Mat_SashGlass"]
transparency = 1
albedo_color = Color(0.88, 0.95, 1, 0.28)
metallic = 0.1
roughness = 0.04

[sub_resource type="BoxMesh" id="Mesh_SashGlass"]
material = SubResource("Mat_SashGlass")
size = Vector3(1.65, 0.75, 0.02)

[sub_resource type="BoxShape3D" id="Shape_SashArea"]
size = Vector3(2.0, 2.0, 1.5)

[sub_resource type="StandardMaterial3D" id="Mat_PolypropyleneSink"]
albedo_color = Color(0.18, 0.2, 0.22, 1)
roughness = 0.35

[sub_resource type="BoxMesh" id="Mesh_SinkCounter"]
material = SubResource("Mat_PolypropyleneSink")
size = Vector3(0.85, 0.05, 2.0)

[sub_resource type="BoxShape3D" id="Shape_SinkStation"]
size = Vector3(0.85, 0.9, 2.0)

[sub_resource type="BoxMesh" id="Mesh_SinkBase"]
material = SubResource("Mat_CabinetLaminate")
size = Vector3(0.8, 0.85, 1.95)

[sub_resource type="StandardMaterial3D" id="Mat_Chrome"]
albedo_color = Color(0.95, 0.95, 0.96, 1)
metallic = 0.95
roughness = 0.15

[sub_resource type="CylinderMesh" id="Mesh_Faucet"]
material = SubResource("Mat_Chrome")
top_radius = 0.015
bottom_radius = 0.015
height = 0.35

[sub_resource type="BoxMesh" id="Mesh_Pegboard"]
material = SubResource("Mat_CabinetLaminate")
size = Vector3(0.04, 0.9, 1.4)

[sub_resource type="StandardMaterial3D" id="Mat_SafetyYellow"]
albedo_color = Color(0.95, 0.76, 0.05, 1)
roughness = 0.3

[sub_resource type="StandardMaterial3D" id="Mat_SafetyRed"]
albedo_color = Color(0.85, 0.08, 0.08, 1)
roughness = 0.25

[sub_resource type="StandardMaterial3D" id="Mat_SafetyGreen"]
albedo_color = Color(0.08, 0.85, 0.25, 1)
roughness = 0.3

[sub_resource type="CylinderMesh" id="Mesh_CarboyYellow"]
material = SubResource("Mat_SafetyYellow")
top_radius = 0.16
bottom_radius = 0.16
height = 0.45

[sub_resource type="CylinderMesh" id="Mesh_CarboyRed"]
material = SubResource("Mat_SafetyRed")
top_radius = 0.16
bottom_radius = 0.16
height = 0.45

[sub_resource type="CylinderMesh" id="Mesh_ShowerPipe"]
material = SubResource("Mat_Chrome")
top_radius = 0.025
bottom_radius = 0.025
height = 1.1

[sub_resource type="CylinderMesh" id="Mesh_ShowerHead"]
material = SubResource("Mat_SafetyYellow")
top_radius = 0.03
bottom_radius = 0.18
height = 0.12

[sub_resource type="CylinderMesh" id="Mesh_EyeWashPedestal"]
material = SubResource("Mat_Chrome")
top_radius = 0.03
bottom_radius = 0.03
height = 1.05

[sub_resource type="CylinderMesh" id="Mesh_EyeWashBowl"]
material = SubResource("Mat_Chrome")
top_radius = 0.18
bottom_radius = 0.18
height = 0.08

[sub_resource type="BoxShape3D" id="Shape_SafetyStation"]
size = Vector3(0.6, 2.4, 0.6)

[sub_resource type="StandardMaterial3D" id="Mat_AmberBottle"]
transparency = 1
albedo_color = Color(0.45, 0.22, 0.04, 0.85)
roughness = 0.1

[sub_resource type="CylinderMesh" id="Mesh_ReagentBottleAmber"]
material = SubResource("Mat_AmberBottle")
top_radius = 0.032
bottom_radius = 0.032
height = 0.12

[sub_resource type="StandardMaterial3D" id="Mat_WhiteBottle"]
albedo_color = Color(0.95, 0.95, 0.95, 1)
roughness = 0.3

[sub_resource type="CylinderMesh" id="Mesh_ReagentBottleWhite"]
material = SubResource("Mat_WhiteBottle")
top_radius = 0.032
bottom_radius = 0.032
height = 0.12

[node name="AnalyticalLab" type="Node3D" node_paths=PackedStringArray("player_spawn_point", "fume_hood_sash", "fume_hood_interaction_area", "fume_hood_interior_light", "bench_spotlight", "ambient_light", "spawn_erlenmeyer", "spawn_beaker", "spawn_bunsen_burner", "spawn_magnetic_stirrer", "spawn_analytical_balance", "spawn_reagent_hcl", "spawn_reagent_naoh", "spawn_reagent_phenolphthalein", "spawn_fume_hood_apparatus")]
script = ExtResource("1_lab_script")
player_spawn_point = NodePath("SpawnPoints/Spawn_Player")
fume_hood_sash = NodePath("Furniture/FumeHoodStation/FumeHood_SashAssembly")
fume_hood_interaction_area = NodePath("Furniture/FumeHoodStation/InteractionArea_Sash")
fume_hood_interior_light = NodePath("Lighting/Light_FumeHood_Interior")
bench_spotlight = NodePath("Lighting/Light_Bench_Spotlight")
ambient_light = NodePath("Lighting/Light_KeyAmbient")
spawn_erlenmeyer = NodePath("SpawnPoints/Spawn_ErlenmeyerFlask")
spawn_beaker = NodePath("SpawnPoints/Spawn_Beaker")
spawn_bunsen_burner = NodePath("SpawnPoints/Spawn_BunsenBurner")
spawn_magnetic_stirrer = NodePath("SpawnPoints/Spawn_MagneticStirrer")
spawn_analytical_balance = NodePath("SpawnPoints/Spawn_AnalyticalBalance")
spawn_reagent_hcl = NodePath("SpawnPoints/Spawn_Reagent_HCl")
spawn_reagent_naoh = NodePath("SpawnPoints/Spawn_Reagent_NaOH")
spawn_reagent_phenolphthalein = NodePath("SpawnPoints/Spawn_Reagent_Phenolphthalein")
spawn_fume_hood_apparatus = NodePath("SpawnPoints/Spawn_FumeHood_Apparatus")

[node name="WorldEnvironment" type="WorldEnvironment" parent="."]
environment = ExtResource("2_lab_env")

[node name="Lighting" type="Node3D" parent="."]

[node name="DirectionalLight3D" type="DirectionalLight3D" parent="Lighting"]
transform = Transform3D(0.866025, -0.353553, 0.353553, 0, 0.707107, 0.707107, -0.5, -0.612372, 0.612372, 0, 3.4, 0)
light_color = Color(0.96, 0.95, 0.92, 1)
light_energy = 0.4
shadow_enabled = false

[node name="Light_KeyAmbient" type="OmniLight3D" parent="Lighting"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 3.0, 0)
light_color = Color(0.96, 0.95, 0.92, 1)
light_energy = 0.8
omni_range = 8.0

[node name="Light_Bench_Spotlight" type="OmniLight3D" parent="Lighting"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 2.7, 0)
light_color = Color(1, 0.98, 0.94, 1)
light_energy = 1.8
omni_range = 4.8

[node name="Light_FumeHood_Interior" type="OmniLight3D" parent="Lighting"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -2.2, 2.1, -3.35)
light_color = Color(0.92, 0.97, 1, 1)
light_energy = 2.2
omni_range = 2.6

[node name="Light_Balance_Task" type="OmniLight3D" parent="Lighting"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.2, 2.4, -3.4)
light_color = Color(0.98, 0.98, 1, 1)
light_energy = 1.2
omni_range = 2.5

[node name="Light_Sink_Task" type="OmniLight3D" parent="Lighting"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -4.2, 2.5, 1.5)
light_color = Color(0.98, 0.98, 1, 1)
light_energy = 1.2
omni_range = 2.5

[node name="Architecture" type="Node3D" parent="."]

[node name="Floor" type="StaticBody3D" parent="Architecture"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.05, 0)

[node name="MeshInstance3D" type="MeshInstance3D" parent="Architecture/Floor"]
mesh = SubResource("Mesh_Floor")

[node name="CollisionShape3D" type="CollisionShape3D" parent="Architecture/Floor"]
shape = SubResource("Shape_Floor")

[node name="Wall_North" type="StaticBody3D" parent="Architecture"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.75, -4)

[node name="MeshInstance3D" type="MeshInstance3D" parent="Architecture/Wall_North"]
mesh = SubResource("Mesh_Wall_NS")

[node name="CollisionShape3D" type="CollisionShape3D" parent="Architecture/Wall_North"]
shape = SubResource("Shape_Wall_NS")

[node name="Kickplate_North" type="MeshInstance3D" parent="Architecture/Wall_North"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -1.65, 0.11)
mesh = SubResource("Mesh_Kickplate_NS")

[node name="Stripe_North" type="MeshInstance3D" parent="Architecture/Wall_North"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.55, 0.11)
mesh = SubResource("Mesh_Stripe_NS")

[node name="Wall_South" type="StaticBody3D" parent="Architecture"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.75, 4)

[node name="MeshInstance3D" type="MeshInstance3D" parent="Architecture/Wall_South"]
mesh = SubResource("Mesh_Wall_NS")

[node name="CollisionShape3D" type="CollisionShape3D" parent="Architecture/Wall_South"]
shape = SubResource("Shape_Wall_NS")

[node name="Kickplate_South" type="MeshInstance3D" parent="Architecture/Wall_South"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -1.65, -0.11)
mesh = SubResource("Mesh_Kickplate_NS")

[node name="Stripe_South" type="MeshInstance3D" parent="Architecture/Wall_South"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.55, -0.11)
mesh = SubResource("Mesh_Stripe_NS")

[node name="Wall_West" type="StaticBody3D" parent="Architecture"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -5, 1.75, 0)

[node name="MeshInstance3D" type="MeshInstance3D" parent="Architecture/Wall_West"]
mesh = SubResource("Mesh_Wall_EW")

[node name="CollisionShape3D" type="CollisionShape3D" parent="Architecture/Wall_West"]
shape = SubResource("Shape_Wall_EW")

[node name="Kickplate_West" type="MeshInstance3D" parent="Architecture/Wall_West"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.11, -1.65, 0)
mesh = SubResource("Mesh_Kickplate_EW")

[node name="Stripe_West" type="MeshInstance3D" parent="Architecture/Wall_West"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.11, -0.55, 0)
mesh = SubResource("Mesh_Stripe_EW")

[node name="Wall_East" type="StaticBody3D" parent="Architecture"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 5, 1.75, 0)

[node name="MeshInstance3D" type="MeshInstance3D" parent="Architecture/Wall_East"]
mesh = SubResource("Mesh_Wall_EW")

[node name="CollisionShape3D" type="CollisionShape3D" parent="Architecture/Wall_East"]
shape = SubResource("Shape_Wall_EW")

[node name="Kickplate_East" type="MeshInstance3D" parent="Architecture/Wall_East"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.11, -1.65, 0)
mesh = SubResource("Mesh_Kickplate_EW")

[node name="Stripe_East" type="MeshInstance3D" parent="Architecture/Wall_East"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.11, -0.55, 0)
mesh = SubResource("Mesh_Stripe_EW")

[node name="Ceiling" type="StaticBody3D" parent="Architecture"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 3.55, 0)

[node name="MeshInstance3D" type="MeshInstance3D" parent="Architecture/Ceiling"]
mesh = SubResource("Mesh_Ceiling")

[node name="CollisionShape3D" type="CollisionShape3D" parent="Architecture/Ceiling"]
shape = SubResource("Shape_Ceiling")

[node name="LED_Panel_0" type="MeshInstance3D" parent="Architecture/Ceiling"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -2.5, -0.06, -1.8)
mesh = SubResource("Mesh_LEDPanel")

[node name="LED_Panel_1" type="MeshInstance3D" parent="Architecture/Ceiling"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.06, -1.8)
mesh = SubResource("Mesh_LEDPanel")

[node name="LED_Panel_2" type="MeshInstance3D" parent="Architecture/Ceiling"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.5, -0.06, -1.8)
mesh = SubResource("Mesh_LEDPanel")

[node name="LED_Panel_3" type="MeshInstance3D" parent="Architecture/Ceiling"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -2.5, -0.06, 1.8)
mesh = SubResource("Mesh_LEDPanel")

[node name="LED_Panel_4" type="MeshInstance3D" parent="Architecture/Ceiling"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.06, 1.8)
mesh = SubResource("Mesh_LEDPanel")

[node name="LED_Panel_5" type="MeshInstance3D" parent="Architecture/Ceiling"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.5, -0.06, 1.8)
mesh = SubResource("Mesh_LEDPanel")

[node name="Furniture" type="Node3D" parent="."]

[node name="CentralMainWorkbench" type="StaticBody3D" parent="Furniture"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.45, 0)

[node name="BenchTopMesh" type="MeshInstance3D" parent="Furniture/CentralMainWorkbench"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.425, 0)
mesh = SubResource("Mesh_MainBenchTop")

[node name="CollisionShape3D" type="CollisionShape3D" parent="Furniture/CentralMainWorkbench"]
shape = SubResource("Shape_MainWorkbench")

[node name="Cabinet_Left" type="MeshInstance3D" parent="Furniture/CentralMainWorkbench"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.85, -0.03, 0)
mesh = SubResource("Mesh_Cabinet")

[node name="Cabinet_Right" type="MeshInstance3D" parent="Furniture/CentralMainWorkbench"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.85, -0.03, 0)
mesh = SubResource("Mesh_Cabinet")

[node name="ReagentRack" type="Node3D" parent="Furniture/CentralMainWorkbench"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.45, 0)

[node name="Stanchion_Left" type="MeshInstance3D" parent="Furniture/CentralMainWorkbench/ReagentRack"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -1.05, 0.325, 0)
mesh = SubResource("Mesh_ShelfStanchion")

[node name="Stanchion_Right" type="MeshInstance3D" parent="Furniture/CentralMainWorkbench/ReagentRack"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.05, 0.325, 0)
mesh = SubResource("Mesh_ShelfStanchion")

[node name="Shelf_Lower" type="MeshInstance3D" parent="Furniture/CentralMainWorkbench/ReagentRack"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.25, 0)
mesh = SubResource("Mesh_ReagentShelf")

[node name="Shelf_Upper" type="MeshInstance3D" parent="Furniture/CentralMainWorkbench/ReagentRack"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.55, 0)
mesh = SubResource("Mesh_ReagentShelf")

[node name="AnalyticalBalanceStation" type="StaticBody3D" parent="Furniture"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.2, 0.45, -3.4)

[node name="GraniteTopMesh" type="MeshInstance3D" parent="Furniture/AnalyticalBalanceStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.41, 0)
mesh = SubResource("Mesh_GraniteTop")

[node name="CollisionShape3D" type="CollisionShape3D" parent="Furniture/AnalyticalBalanceStation"]
shape = SubResource("Shape_BalanceTable")

[node name="SteelBaseMesh" type="MeshInstance3D" parent="Furniture/AnalyticalBalanceStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.04, 0)
mesh = SubResource("Mesh_BalanceBase")

[node name="FumeHoodStation" type="StaticBody3D" parent="Furniture"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -2.2, 0, -3.35)

[node name="BaseCabinetMesh" type="MeshInstance3D" parent="Furniture/FumeHoodStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.45, 0)
mesh = SubResource("Mesh_FumeHoodBase")

[node name="UpperChamberMesh" type="MeshInstance3D" parent="Furniture/FumeHoodStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.65, 0)
mesh = SubResource("Mesh_FumeHoodUpper")

[node name="WorkDeckMesh" type="MeshInstance3D" parent="Furniture/FumeHoodStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.92, 0)
mesh = SubResource("Mesh_FumeHoodWorkDeck")

[node name="ExhaustPlenumMesh" type="MeshInstance3D" parent="Furniture/FumeHoodStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 2.95, 0)
mesh = SubResource("Mesh_ExhaustPlenum")

[node name="CollisionShape3D" type="CollisionShape3D" parent="Furniture/FumeHoodStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.2, 0)
shape = SubResource("Shape_FumeHood")

[node name="FumeHood_SashAssembly" type="Node3D" parent="Furniture/FumeHoodStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.95, 0.48)

[node name="SashGlassMesh" type="MeshInstance3D" parent="Furniture/FumeHoodStation/FumeHood_SashAssembly"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.375, 0)
mesh = SubResource("Mesh_SashGlass")

[node name="InteractionArea_Sash" type="Area3D" parent="Furniture/FumeHoodStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.2, 1.0)
collision_layer = 3
collision_mask = 3

[node name="CollisionShape3D" type="CollisionShape3D" parent="Furniture/FumeHoodStation/InteractionArea_Sash"]
shape = SubResource("Shape_SashArea")

[node name="WashAndWasteStation" type="StaticBody3D" parent="Furniture"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -4.2, 0.45, 1.5)

[node name="CountertopMesh" type="MeshInstance3D" parent="Furniture/WashAndWasteStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.425, 0)
mesh = SubResource("Mesh_SinkCounter")

[node name="CollisionShape3D" type="CollisionShape3D" parent="Furniture/WashAndWasteStation"]
shape = SubResource("Shape_SinkStation")

[node name="BaseCabinetMesh" type="MeshInstance3D" parent="Furniture/WashAndWasteStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.025, 0)
mesh = SubResource("Mesh_SinkBase")

[node name="FaucetMesh" type="MeshInstance3D" parent="Furniture/WashAndWasteStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.25, 0.625, 0)
mesh = SubResource("Mesh_Faucet")

[node name="DryingPegboard" type="MeshInstance3D" parent="Furniture/WashAndWasteStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.68, 1.4, 0)
mesh = SubResource("Mesh_Pegboard")

[node name="Carboy_Yellow" type="MeshInstance3D" parent="Furniture/WashAndWasteStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.225, 1.2)
mesh = SubResource("Mesh_CarboyYellow")

[node name="Carboy_Red" type="MeshInstance3D" parent="Furniture/WashAndWasteStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.225, 1.6)
mesh = SubResource("Mesh_CarboyRed")

[node name="EmergencySafetyStation" type="StaticBody3D" parent="Furniture"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 4.3, 0, -1.5)

[node name="ShowerPipeMesh" type="MeshInstance3D" parent="Furniture/EmergencySafetyStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 2.95, 0)
mesh = SubResource("Mesh_ShowerPipe")

[node name="ShowerHeadMesh" type="MeshInstance3D" parent="Furniture/EmergencySafetyStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 2.35, 0)
mesh = SubResource("Mesh_ShowerHead")

[node name="EyeWashPedestalMesh" type="MeshInstance3D" parent="Furniture/EmergencySafetyStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.525, 0)
mesh = SubResource("Mesh_EyeWashPedestal")

[node name="EyeWashBowlMesh" type="MeshInstance3D" parent="Furniture/EmergencySafetyStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.08, 0)
mesh = SubResource("Mesh_EyeWashBowl")

[node name="CollisionShape3D" type="CollisionShape3D" parent="Furniture/EmergencySafetyStation"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.2, 0)
shape = SubResource("Shape_SafetyStation")

[node name="SpawnPoints" type="Node3D" parent="."]

[node name="Spawn_Player" type="Marker3D" parent="SpawnPoints"]
transform = Transform3D(-1, 0, 8.74228e-08, 0, 1, 0, -8.74228e-08, 0, -1, 0, 1.0, 2.5)

[node name="Spawn_ErlenmeyerFlask" type="Marker3D" parent="SpawnPoints"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.9, 0.2)

[node name="Spawn_Beaker" type="Marker3D" parent="SpawnPoints"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.7, 0.9, 0.2)

[node name="Spawn_BunsenBurner" type="Marker3D" parent="SpawnPoints"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.1, 0.9, 0)

[node name="Spawn_MagneticStirrer" type="Marker3D" parent="SpawnPoints"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.4, 0.9, 0)

[node name="Spawn_AnalyticalBalance" type="Marker3D" parent="SpawnPoints"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.2, 0.9, -3.4)

[node name="Spawn_Reagent_HCl" type="Marker3D" parent="SpawnPoints"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.5, 1.165, 0)

[node name="ReagentBottle_HCl" type="MeshInstance3D" parent="SpawnPoints/Spawn_Reagent_HCl"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.06, 0)
mesh = SubResource("Mesh_ReagentBottleAmber")

[node name="Spawn_Reagent_NaOH" type="Marker3D" parent="SpawnPoints"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.2, 1.165, 0)

[node name="ReagentBottle_NaOH" type="MeshInstance3D" parent="SpawnPoints/Spawn_Reagent_NaOH"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.06, 0)
mesh = SubResource("Mesh_ReagentBottleWhite")

[node name="Spawn_Reagent_Phenolphthalein" type="Marker3D" parent="SpawnPoints"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.1, 1.165, 0)

[node name="ReagentBottle_Phenol" type="MeshInstance3D" parent="SpawnPoints/Spawn_Reagent_Phenolphthalein"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.06, 0)
mesh = SubResource("Mesh_ReagentBottleAmber")

[node name="Spawn_FumeHood_Apparatus" type="Marker3D" parent="SpawnPoints"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -2.2, 0.92, -3.35)

[node name="ApparatusInstances" type="Node3D" parent="."]

[node name="AnalyticalBalance" parent="ApparatusInstances" instance=ExtResource("4_balance")]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.2, 0.9, -3.4)

[node name="MagneticStirrer" parent="ApparatusInstances" instance=ExtResource("5_stirrer")]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.4, 0.9, 0)

[node name="TitrationBuret" parent="ApparatusInstances" instance=ExtResource("6_buret")]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.4, 0.9, 0)

[node name="BunsenBurner" parent="ApparatusInstances" instance=ExtResource("7_burner")]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.1, 0.9, 0)

[node name="ErlenmeyerFlask" parent="ApparatusInstances" instance=ExtResource("8_erlenmeyer")]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.9, 0.2)

[node name="Beaker" parent="ApparatusInstances" instance=ExtResource("9_beaker")]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.7, 0.9, 0.2)

[node name="Player" parent="." instance=ExtResource("3_player")]
transform = Transform3D(-1, 0, 8.74228e-08, 0, 1, 0, -8.74228e-08, 0, -1, 0, 1.0, 2.5)

[node name="QuestOverlay" parent="." instance=ExtResource("10_quest_overlay")]
"""

OUTPUT_PATH.write_text(SCENE_CONTENT.strip() + "\n", encoding="utf-8")

print(f"Generated {OUTPUT_PATH} ({len(SCENE_CONTENT)} bytes)")
