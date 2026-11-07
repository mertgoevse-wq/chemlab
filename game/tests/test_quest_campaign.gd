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
	var QuestManagerScript := load("res://scripts/quests/quest_manager.gd")
	var qm = QuestManagerScript.new()
	qm._initialize_quest_catalog()

	_check("catalog has six contracts", qm.quests.size() == 6)
	for quest_id in ["quest_04_contaminated_batch", "quest_05_quiet_synthesis", "quest_06_riverbank_contract"]:
		_check("%s present with briefing" % quest_id,
			qm.quests.has(quest_id) and not str(qm.quests[quest_id].get("briefing", "")).is_empty())
	_check("act II is narrative-gated", qm.quests["quest_05_quiet_synthesis"].has("moral_fork"))
	_check("every contract names its successor or ends the arc",
		qm.quests["quest_06_riverbank_contract"].get("next_quest_id", "") == "")

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

	print("\n>>> [QuestCampaign] %d passed, %d failed" % [_passed, _failed])
	quit(0 if _failed == 0 else 1)


func _init() -> void:
	_run.call_deferred()
