# Campaign chain regression: the contract graph must be walkable end to end.
# Usage: tools/bin/godot --headless --path game --script res://tests/test_quest_campaign.gd
extends SceneTree

var _passed := 0
var _failed := 0


func _check(label: String, condition: bool) -> void:
	if condition:
		_passed += 1
		print("PASS  ", label)
	else:
		_failed += 1
		print("FAIL  ", label)


func _run() -> void:
	var qm = root.get_node_or_null("QuestManager")
	if qm == null:
		var QuestManagerScript := load("res://scripts/quests/quest_manager.gd")
		qm = QuestManagerScript.new()
		root.add_child(qm)
		qm._initialize_quest_catalog()

	var side_quests: Array[Dictionary] = qm.get_all_side_quests()
	var main_quests: Array[Dictionary] = []
	for q_id in qm.quests:
		if not qm.is_side_quest(q_id):
			main_quests.append(qm.quests[q_id])

	_check("catalog has ten main campaign contracts across 10 Acts", main_quests.size() == 10)
	_check("catalog includes open world side quests (at least 8)", side_quests.size() >= 8)

	for quest_id in ["quest_04_contaminated_batch", "quest_05_quiet_synthesis", "quest_06_riverbank_contract", "quest_07_pilot_plant_scaleup", "quest_08_aether_resonance", "quest_09_destiny_inversion", "quest_10_athanor_ascension"]:
		_check("%s present with briefing" % quest_id,
			qm.quests.has(quest_id) and not str(qm.quests[quest_id].get("briefing", "")).is_empty())
	_check("act II is narrative-gated", qm.quests["quest_05_quiet_synthesis"].has("moral_fork"))
	_check("quest 6 links to Act 7 scale-up",
		qm.quests["quest_06_riverbank_contract"].get("next_quest_id", "") == "quest_07_pilot_plant_scaleup")
	_check("Act X names its successor or ends the arc",
		qm.quests["quest_10_athanor_ascension"].get("next_quest_id", "") == "")

	# Walk contract 1 to completion through its public objective surface and
	# confirm the campaign opens the next contract instead of dead-ending.
	qm.start_quest("quest_01_orientation")
	for obj in qm.quests["quest_01_orientation"]["objectives"]:
		qm.complete_objective_by_id(obj["id"])

	_check("quest 1 completes", int(qm.quests["quest_01_orientation"]["status"]) == qm.QuestStatus.COMPLETED)
	_check("quest 2 unlocks on completion",
		int(qm.quests["quest_02_iodine_clock"]["status"]) == qm.QuestStatus.AVAILABLE)

	# A later contract's objectives have their own ids; the shared physical
	# interactions must still advance the active objective.
	qm.start_quest("quest_04_contaminated_batch")
	qm.advance_objective("flame_test_identify", 1.0)
	_check("quest-agnostic progress reaches later contracts",
		qm.quests["quest_04_contaminated_batch"]["objectives"][1]["is_completed"])

	# -------------------------------------------------------------------------
	# Side Quest, Multi-Skill Progression, and Unique Item/Garment Rewards
	# -------------------------------------------------------------------------
	var side_id: String = "side_quest_tropane_belladonna"
	_check("Tropane alkaloid side quest recognized as side quest", qm.is_side_quest(side_id))

	var sm = root.get_node_or_null("SkillManager")
	var inv = root.get_node_or_null("InventoryManager")

	var chem_before: int = sm.get_xp("chemistry") if sm else 0
	var bio_before: int = sm.get_xp("biology") if sm else 0
	var tox_before: int = sm.get_xp("toxicology") if sm else 0

	qm.start_quest(side_id)
	_check("side quest starts successfully", qm.active_quest_id == side_id)

	# Complete all objectives for belladonna extraction side quest
	for obj in qm.quests[side_id]["objectives"]:
		qm.complete_objective_by_id(obj["id"])

	_check("side quest completes", int(qm.quests[side_id]["status"]) == qm.QuestStatus.COMPLETED)

	if sm != null:
		var chem_after: int = sm.get_xp("chemistry")
		var bio_after: int = sm.get_xp("biology")
		var tox_after: int = sm.get_xp("toxicology")
		_check("Multi-skill reward granted: chemistry XP (+800)", chem_after >= chem_before + 800)
		_check("Multi-skill reward granted: biology XP (+500)", bio_after >= bio_before + 500)
		_check("Multi-skill reward granted: toxicology XP (+500)", tox_after >= tox_before + 500)

	if inv != null:
		_check("Reward item added: belladonna_botanical_cloak in inventory", inv.has_item("belladonna_botanical_cloak"))

	print("\n>>> [QuestCampaign] %d passed, %d failed" % [_passed, _failed])
	quit(0 if _failed == 0 else 1)


func _init() -> void:
	_run.call_deferred()
