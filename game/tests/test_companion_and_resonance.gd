# Athanor Ascension — Companion System & Fate Resonance Automated Test Suite
# Tests 3D Companion physical presence, chemical sniffing, hazard scavenging,
# symbiotic skill wiring, and tri-protagonist campaign destiny resonance.
#
# Usage:
#   tools/bin/godot --headless --path game --script res://tests/test_companion_and_resonance.gd

extends SceneTree

var _passed: int = 0
var _failed: int = 0


func _check(label: String, condition: bool) -> void:
	if condition:
		_passed += 1
		print("PASS  ", label)
	else:
		_failed += 1
		print("FAIL  ", label)


func _run() -> void:
	print("=====================================================================")
	print("🧪 Athanor Ascension — Companion & Fate Resonance Verification")
	print("=====================================================================\n")

	_test_companion_lifecycle_and_entity()
	_test_companion_commands_sniff_and_scavenge()
	_test_symbiotic_skill_wiring()
	_test_tri_protagonist_switching_and_resonance()
	_test_destiny_swapping_inversion()
	_test_serialization_round_trip()

	print("\n=====================================================================")
	print(">>> [Companion & Resonance Tests] %d passed, %d failed" % [_passed, _failed])
	print("=====================================================================")

	quit(0 if _failed == 0 else 1)


func _test_companion_lifecycle_and_entity() -> void:
	print("\n--- 1. Companion Lifecycle & 3D Entity Physical Presence ---")
	var CompanionManagerScript = load("res://scripts/companions/companion_manager.gd")
	var cm = CompanionManagerScript.new()
	cm._load_species_data()

	# Register/Add a Cinderling companion
	var comp_id = cm.add_companion("cinderling", "Ignis")
	_check("companion added successfully", comp_id != "")
	_check("companion is in catalog", cm.companions.has(comp_id))

	# Create a dummy 3D scene root to act as lab scene inside the scene tree
	var lab_root = Node3D.new()
	lab_root.name = "TestLab"
	root.add_child(lab_root)

	var dummy_player = Node3D.new()
	dummy_player.name = "Player"
	dummy_player.position = Vector3(0, 0, 0)
	lab_root.add_child(dummy_player)

	# Summon companion into 3D lab space
	var entity = cm.summon_companion(comp_id, lab_root, Vector3(1.5, 0.0, 1.5))
	_check("entity summoned and returned CharacterBody3D", entity is CharacterBody3D)
	_check("entity added as child of lab scene", entity.get_parent() == lab_root)
	_check("entity species matches cinderling", entity.species_id == "cinderling")
	_check("entity belongs to 'companions' and 'aetherkin' groups",
		entity.is_in_group("companions") and entity.is_in_group("aetherkin"))

	# Check visual nodes assembly (Iris Xe 60 FPS PBR compliance)
	var visual_root = entity.get_node_or_null("VisualRoot")
	var body_mesh = visual_root.get_node_or_null("BodyMesh") if visual_root else null
	var aura_light = entity.get_node_or_null("AuraLight")
	var col_shape = entity.get_node_or_null("CollisionShape")

	_check("procedural visual hierarchy constructed", visual_root != null and body_mesh != null)
	_check("elemental aura light and collision attached", aura_light is OmniLight3D and col_shape is CollisionShape3D)

	# Dismiss companion
	var dismissed = cm.dismiss_companion(comp_id)
	_check("companion dismissed successfully", dismissed)
	_check("spawned entity reference cleared", not cm.spawned_entities.has(comp_id))

	root.remove_child(lab_root)
	dummy_player.free()
	lab_root.free()
	cm.free()


func _test_companion_commands_sniff_and_scavenge() -> void:
	print("\n--- 2. Companion Active Commands: Chemical Sniffing & Scavenging ---")
	var test_container = Node3D.new()
	test_container.name = "CommandTestContainer"
	root.add_child(test_container)

	var CompanionEntityScript = load("res://scenes/companions/companion_entity.gd")
	var entity: CharacterBody3D = CompanionEntityScript.new()
	entity.species_id = "cinderling"
	entity.position = Vector3(0, 0, 0)
	test_container.add_child(entity)

	# Mock Apparatus
	var mock_apparatus = Node3D.new()
	mock_apparatus.name = "NMR_Tube_Aspirin"
	mock_apparatus.position = Vector3(0.3, 0, 0)
	mock_apparatus.set_meta("compound_name", "Acetylsalicylic Acid")
	test_container.add_child(mock_apparatus)

	var sniff_state = {"received": false, "data": {}}
	entity.sniff_completed.connect(func(apparatus: Node, diagnostic: Dictionary):
		sniff_state["received"] = true
		sniff_state["data"] = diagnostic
	)

	# Command Sniff
	entity.command_sniff(mock_apparatus)
	_check("command_sniff set task to 'sniff'", entity.current_task == "sniff")

	# Simulate physics process delta steps until sniff completion (1.2s threshold)
	for i in range(15):
		entity._process_sniff(0.1)

	_check("sniff_completed signal fired", sniff_state["received"])
	var sniff_data: Dictionary = sniff_state["data"]
	_check("sniff detected compound name", sniff_data.get("compound_name", "") == "Acetylsalicylic Acid")
	_check("sniff detected high purity", float(sniff_data.get("purity_pct", 0.0)) >= 95.0)
	_check("cinderling thermal stability diagnosis present", sniff_data.has("thermal_stability"))

	# Mock Hazardous Waste Zone
	var mock_zone = Node3D.new()
	mock_zone.name = "Fume_Hood_BSL3"
	mock_zone.position = Vector3(0.3, 0, 0)
	mock_zone.add_to_group("fume_hood")
	test_container.add_child(mock_zone)

	var scavenge_state = {"received": false, "loot": []}
	entity.scavenge_completed.connect(func(zone: Node, loot: Array):
		scavenge_state["received"] = true
		scavenge_state["loot"] = loot
	)

	# Command Scavenge
	entity.command_scavenge(mock_zone)
	_check("command_scavenge set task to 'scavenge'", entity.current_task == "scavenge")

	# Simulate physics process delta steps until scavenge completion (1.5s threshold)
	for i in range(20):
		entity._process_scavenge(0.1)

	_check("scavenge_completed signal fired", scavenge_state["received"])
	var recovered_items: Array = scavenge_state["loot"]
	_check("scavenged loot recovered from fume hood", recovered_items.size() > 0 and recovered_items[0].get("item_id", "") == "chiral_ligand_aliquot")

	root.remove_child(test_container)
	mock_apparatus.free()
	mock_zone.free()
	entity.free()
	test_container.free()


func _test_symbiotic_skill_wiring() -> void:
	print("\n--- 3. Symbiotic Skill Wiring & Multipliers ---")
	var sm = root.get_node_or_null("SkillManager")
	var cm = root.get_node_or_null("CompanionManager")
	var created_sm = false
	var created_cm = false

	if sm == null:
		var SkillManagerScript = load("res://scripts/progression/skill_manager.gd")
		sm = SkillManagerScript.new()
		sm.name = "SkillManager"
		root.add_child(sm)
		created_sm = true

	if cm == null:
		var CompanionManagerScript = load("res://scripts/companions/companion_manager.gd")
		cm = CompanionManagerScript.new()
		cm.name = "CompanionManager"
		root.add_child(cm)
		created_cm = true

	cm._load_species_data()
	cm.max_total_companions = 10

	var c_cinder = cm.add_companion("cinderling", "Cinder")
	var c_gecko = cm.add_companion("wall_gecko", "Sticky")
	var c_rat = cm.add_companion("instrumented_rat", "Algernon")
	var c_brine = cm.add_companion("brinejack", "Halite")

	# Test Cinderling synergy
	var syn_cinder = cm.wire_skill_synergy(c_cinder)
	_check("cinderling boosts chemistry multiplier to 1.25", is_equal_approx(sm.get_xp_multiplier("chemistry"), 1.25))
	_check("cinderling boosts thermodynamics to 1.30", is_equal_approx(sm.get_xp_multiplier("thermodynamics"), 1.30))

	# Test Wall Gecko synergy
	var syn_gecko = cm.wire_skill_synergy(c_gecko)
	_check("wall gecko boosts lab safety to 1.35", is_equal_approx(sm.get_xp_multiplier("lab_safety"), 1.35))
	_check("wall gecko boosts containment to 1.30", is_equal_approx(sm.get_xp_multiplier("containment"), 1.30))

	# Test Instrumented Rat synergy
	var syn_rat = cm.wire_skill_synergy(c_rat)
	_check("rat boosts toxicology to 1.30", is_equal_approx(sm.get_xp_multiplier("toxicology"), 1.30))
	_check("rat boosts forensics to 1.25", is_equal_approx(sm.get_xp_multiplier("forensics"), 1.25))

	# Test Brinejack synergy
	var syn_brine = cm.wire_skill_synergy(c_brine)
	_check("brinejack boosts materials science to 1.25", is_equal_approx(sm.get_xp_multiplier("materials_science"), 1.25))

	if created_cm:
		root.remove_child(cm)
		cm.free()
	if created_sm:
		root.remove_child(sm)
		sm.free()


func _test_tri_protagonist_switching_and_resonance() -> void:
	print("\n--- 4. Tri-Protagonist Switching & Fate Resonance Engine ---")
	var QuestManagerScript = load("res://scripts/quests/quest_manager.gd")
	var qm = QuestManagerScript.new()

	_check("default protagonist is Thorne", qm.get_current_protagonist() == "thorne")

	# Switch to Finch
	var switched_finch = qm.switch_protagonist("finch")
	_check("switched to Finch", switched_finch and qm.get_current_protagonist() == "finch")
	_check("background updated to hobbyist", qm.get_background() == "hobbyist")

	# Switch to Voss
	var switched_voss = qm.switch_protagonist("voss")
	_check("switched to Voss", switched_voss and qm.get_current_protagonist() == "voss")
	_check("background updated to ex_pharma", qm.get_background() == "ex_pharma")

	# Test cross-character resonance matrix
	qm.record_fate_resonance("thorne", "finch", 45.0, "Leaked chiral catalyst NMR spectra to underground")
	qm.record_fate_resonance("finch", "voss", 55.0, "Delivered stable anti-toxin synthesis batch to whistleblower")
	qm.record_fate_resonance("voss", "thorne", 55.0, "Handed corporate forensic audit reports to academic panel")

	var summary = qm.get_fate_summary()
	var matrix = summary.get("resonance_matrix", {})
	_check("thorne to finch resonance is 45.0", is_equal_approx(float(matrix.get("thorne_to_finch", 0.0)), 45.0))
	_check("finch to voss resonance is 55.0", is_equal_approx(float(matrix.get("finch_to_voss", 0.0)), 55.0))
	_check("voss to thorne resonance is 55.0", is_equal_approx(float(matrix.get("voss_to_thorne", 0.0)), 55.0))

	# Nexus convergence threshold check: sum (45+55+55 = 155) >= 150 triggers Nexus
	_check("Act 4 Nexus Convergence triggered by cumulative resonance >= 150", summary.get("nexus_achieved", false) == true)

	qm.free()


func _test_destiny_swapping_inversion() -> void:
	print("\n--- 5. Act 9 Destiny Swapping & Convergence Inversion ---")
	var FateResonanceScript = load("res://scripts/quests/fate_resonance_manager.gd")
	var frm = FateResonanceScript.new()

	_check("initial fate: Thorne is academic", frm.get_destiny("thorne") == "academic_chair")
	_check("initial fate: Finch is underground", frm.get_destiny("finch") == "alchemical_underground")
	_check("initial fate: Voss is whistleblower", frm.get_destiny("voss") == "regulatory_whistleblower")

	# Swap Thorne and Finch destinies
	var swap_ok = frm.swap_destinies("thorne", "finch", "Convergence Inversion: Academic tenure transferred to underground prodigy")
	_check("destiny swap executed", swap_ok)
	_check("destiny swap flag is active", frm.destiny_swap_active)
	_check("Thorne now holds alchemical underground fate", frm.get_destiny("thorne") == "alchemical_underground")
	_check("Finch now holds academic chair fate", frm.get_destiny("finch") == "academic_chair")
	_check("Voss maintains whistleblower fate", frm.get_destiny("voss") == "regulatory_whistleblower")
	_check("shared timeline logged swap reason", frm.shared_timeline_events.size() > 0)


func _test_serialization_round_trip() -> void:
	print("\n--- 6. Serialization & Save/Load Round-Trip Persistence ---")
	var CompanionManagerScript = load("res://scripts/companions/companion_manager.gd")
	var QuestManagerScript = load("res://scripts/quests/quest_manager.gd")

	# 1. Test CompanionManager persistence
	var cm1 = CompanionManagerScript.new()
	cm1._load_species_data()
	var c1 = cm1.add_companion("cinderling", "Flame")
	cm1.set_companion_active(c1, true)
	cm1.modify_bond(c1, 0.35)

	var saved_comp_data = cm1.to_dict()
	_check("companion to_dict contains 'companions' and 'active_companions'",
		saved_comp_data.has("companions") and saved_comp_data.has("active_companions"))

	var cm2 = CompanionManagerScript.new()
	cm2._load_species_data()
	cm2.from_dict(saved_comp_data)
	_check("deserialized companion exists", cm2.companions.has(c1))
	var restored_comp = cm2.companions.get(c1)
	_check("deserialized companion stats match (level 1, active)",
		restored_comp != null and restored_comp.level == 1 and restored_comp.active == true)
	_check("deserialized companion bond preserved",
		restored_comp != null and is_equal_approx(restored_comp.bond, 0.45))

	cm1.free()
	cm2.free()

	# 2. Test QuestManager Fate Resonance persistence
	var qm1 = QuestManagerScript.new()
	qm1.switch_protagonist("finch")
	qm1.record_fate_resonance("finch", "voss", 75.0, "Specialized solvent shipment delivered")
	qm1.swap_protagonist_destinies("finch", "voss", "Role reversal in Act 9")

	var saved_quest_data = qm1.to_dict()
	_check("quest to_dict contains 'fate_resonance'", saved_quest_data.has("fate_resonance"))

	var qm2 = QuestManagerScript.new()
	qm2.from_dict(saved_quest_data)
	_check("deserialized active protagonist preserved as Finch", qm2.get_current_protagonist() == "finch")
	var restored_summary = qm2.get_fate_summary()
	_check("deserialized resonance matrix preserved",
		is_equal_approx(float(restored_summary.get("resonance_matrix", {}).get("finch_to_voss", 0.0)), 75.0))
	_check("deserialized destiny swap flag preserved", restored_summary.get("swap_active", false) == true)
	_check("deserialized Finch destiny is regulatory_whistleblower",
		restored_summary.get("fates", {}).get("finch", "") == "regulatory_whistleblower")

	qm1.free()
	qm2.free()


func _init() -> void:
	_run.call_deferred()
