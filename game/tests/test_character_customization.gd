# Athanor Ascension — Character Customization & Unbound Progression Test
# Usage: tools/bin/godot --headless --path game --script res://tests/test_character_customization.gd
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
	var cc = root.get_node_or_null("CharacterCreator")
	if cc == null:
		var CharacterCreatorScript := load("res://scripts/character/character_creator.gd")
		cc = CharacterCreatorScript.new()
		root.add_child(cc)

	var qm = root.get_node_or_null("QuestManager")
	var sm = root.get_node_or_null("SkillManager")

	# -------------------------------------------------------------------------
	# 1. Default Fallback Names for Backgrounds
	# -------------------------------------------------------------------------
	_check("Academic fallback name is Dr. Aris Thorne",
		cc.get_default_name_for_background("academic") == "Dr. Aris Thorne")
	_check("Hobbyist fallback name is Vesper Finch",
		cc.get_default_name_for_background("hobbyist") == "Vesper Finch")
	_check("Ex-Pharma fallback name is Kaelen Voss",
		cc.get_default_name_for_background("ex_pharma") == "Kaelen Voss")

	# Finalize with empty name should fallback to default for chosen background
	cc.select_background("academic")
	cc.character_name = ""
	var res_academic: Dictionary = cc.finalize_character()
	_check("Empty academic name resolves to Dr. Aris Thorne",
		res_academic.get("character", {}).get("name", "") == "Dr. Aris Thorne")

	cc.select_background("hobbyist")
	cc.character_name = "   "
	var res_hobbyist: Dictionary = cc.finalize_character()
	_check("Whitespace hobbyist name resolves to Vesper Finch",
		res_hobbyist.get("character", {}).get("name", "") == "Vesper Finch")

	cc.select_background("ex_pharma")
	cc.character_name = ""
	var res_pharma: Dictionary = cc.finalize_character()
	_check("Empty ex_pharma name resolves to Kaelen Voss",
		res_pharma.get("character", {}).get("name", "") == "Kaelen Voss")

	# -------------------------------------------------------------------------
	# 2. Custom Player Naming & Appearance
	# -------------------------------------------------------------------------
	var custom_name := "Dr. Corvus Nightingale"
	cc.character_name = custom_name
	cc.pronouns = "they/them"
	cc.set_appearance("attire", "coat_style", "hazmat_heavy")
	var res_custom: Dictionary = cc.finalize_character()
	var char_data: Dictionary = res_custom.get("character", {})

	_check("Custom character name preserved", char_data.get("name", "") == custom_name)
	_check("Custom coat style applied",
		char_data.get("appearance", {}).get("attire", {}).get("coat_style", "") == "hazmat_heavy")

	# Apply character to game
	cc.apply_character_to_game(char_data)
	if qm != null:
		_check("QuestManager receives custom player name", qm.get_player_name() == custom_name)
		_check("QuestManager background matches selected background", qm.get_background() == "ex_pharma")

	# -------------------------------------------------------------------------
	# 3. Unbound 20-Skill Progression to Level 99
	# -------------------------------------------------------------------------
	_check("Character data flags open progression as true",
		bool(char_data.get("open_progression", false)))

	if sm != null:
		_check("SkillManager has all 20 mastery skills initialized",
			sm.get_all_skills().size() == 20)
		_check("Chemistry skill cap is Level 99",
			sm.MAX_SKILL_LEVEL == 99)
		_check("Level 92 requires ~50% of Level 99 XP",
			sm.get_xp_for_level(92) >= 6500000 and sm.get_xp_for_level(99) == 13034431)

	print("\n>>> [CharacterCustomization] %d passed, %d failed" % [_passed, _failed])
	quit(0 if _failed == 0 else 1)


func _init() -> void:
	_run.call_deferred()
