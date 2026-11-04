# Athanor Ascension — Genome simulation headless test
# Run: tools/bin/godot --headless --path game --script res://tests/test_genome_simulation.gd

extends SceneTree

const GS = preload("res://scripts/genomics/genome_simulation.gd")

var _failures: int = 0


func _init() -> void:
	print("--- GENOME SIMULATION VALIDATION ---")
	var assembly: Dictionary = GS.load_assembly()
	_check(not assembly.is_empty(), "assembly loads")
	_check(GS.chromosomes(assembly).size() == 25, "25 chromosomes incl. MT")
	_check(int(GS.chromosome(assembly, "1").get("length_bp", 0)) == 248956422, "chr1 GRCh38 length")
	_check(GS.gene(assembly, "HBB").get("symbol", "") == "HBB", "HBB present")

	_check(GS.classify_substitution("A", "G") == "transition", "A>G is a transition")
	_check(GS.classify_substitution("A", "C") == "transversion", "A>C is a transversion")

	var hbb: Dictionary = GS.gene(assembly, "HBB")
	var hs: Dictionary = hbb.get("hotspots", [])[0]
	var hbb_pos := GS.hotpot_genomic_bp(hbb, hs)
	var sickle := GS.apply_point_mutation(assembly, "HBB", hbb_pos, "T", "homozygous")
	_check(bool(sickle.get("ok", false)), "HBB mutation applies")
	_check(str(sickle.get("consequence", "")) == "missense_variant", "HBB is missense")
	_check(str(sickle.get("protein", "")).contains("Glu7Val"), "HBB protein change is HbS")
	_check(str(sickle.get("phenotype", "")).to_lower().contains("sickle"), "HBB phenotype mentions sickle")
	_check(str(sickle.get("confidence", "")) == "curated", "HBB is curated")

	var cftr: Dictionary = GS.gene(assembly, "CFTR")
	var cftr_hs: Dictionary = cftr.get("hotspots", [])[0]
	var cftr_res := GS.apply_point_mutation(assembly, "CFTR", GS.hotpot_genomic_bp(cftr, cftr_hs), "del", "homozygous")
	_check(str(cftr_res.get("protein", "")).contains("Phe508del"), "CFTR F508del protein")
	_check(str(cftr_res.get("consequence", "")).contains("frameshift") or str(cftr_res.get("consequence", "")).contains("deletion"), "CFTR is a deletion consequence")

	var arbitrary := GS.apply_point_mutation(assembly, "TP53", int(GS.gene(assembly, "TP53").get("start", 0)) + 900, "A", "heterozygous")
	_check(str(arbitrary.get("confidence", "")) == "unmodelled", "uncurated locus is unmodelled")
	_check(str(arbitrary.get("phenotype", "")).contains("uncertain"), "uncurated locus is VUS")

	var dosage: Array = GS.dosage_effects(assembly, {"21": 3, "X": 1})
	_check(dosage.size() == 2, "two dosage events")
	var chr21: Dictionary = dosage[0]
	_check(absf(float(chr21.get("multiplier", 0.0)) - 1.5) < 0.001, "trisomy 21 is 1.5x")
	var symbols: Array = []
	for entry in chr21.get("genes", []):
		symbols.append(str(entry.get("symbol", "")))
	_check(symbols.has("APP"), "trisomy 21 includes APP")
	_check(symbols.has("DYRK1A"), "trisomy 21 includes DYRK1A")

	var exposure: Dictionary = GS.expose_to_mutagen(assembly, "ems", 3.0, 42, 0.4)
	_check(bool(exposure.get("ok", false)), "EMS exposure runs")
	_check(int(exposure.get("point_mutations", 0)) > 0, "EMS produces point events")
	var summary: Dictionary = exposure.get("summary", {})
	_check(int(summary.get("transition", 0)) >= 0, "summary bucket present")

	var repeat_a: Dictionary = GS.expose_to_mutagen(assembly, "ems", 3.0, 42, 0.4)
	var repeat_b: Dictionary = GS.expose_to_mutagen(assembly, "ems", 3.0, 42, 0.4)
	_check(int(repeat_a.get("point_mutations", 0)) == int(repeat_b.get("point_mutations", 0)), "same seed -> same event count")

	var aneugen: Dictionary = GS.expose_to_mutagen(assembly, "colchicine", 3.0, 11, 0.3)
	_check(bool(aneugen.get("nondisjunction", false)), "colchicine gives nondisjunction")
	_check(int(aneugen.get("point_mutations", -1)) == 0, "colchicine gives no point mutations")

	var phenotypes: Array = GS.aggregate_phenotypes({"mutations": [sickle], "dosage": dosage})
	_check(not phenotypes.is_empty(), "phenotype report aggregates")

	print("--- RESULT: %s (%d failures) ---" % ["PASS" if _failures == 0 else "FAIL", _failures])
	quit(0 if _failures == 0 else 1)


func _check(condition: bool, label: String) -> void:
	if condition:
		print("  ok  ", label)
	else:
		_failures += 1
		printerr("  FAIL ", label)
