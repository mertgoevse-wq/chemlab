# Athanor Ascension — Genome Simulation Core
# Offline, deterministic-ish model behind the interactive chromosome browser.
#
# Honesty contract:
#   * Chromosome lengths and gene spans are real GRCh38 values.
#   * Curated hotspots carry real HGVS/protein annotations.
#   * Anything outside a curated hotspot is reported as a variant of uncertain
#     significance (VUS), never dressed up as a predicted clinical effect.
#   * Gene-dosage output is an educational 1.5x / 0.5x expression model.

class_name GenomeSimulation
extends RefCounted

const ASSEMBLY_PATH: String = "res://data/genomics/human_grch38_curated.json"

const TRANSITIONS: Dictionary = {"A": "G", "G": "A", "C": "T", "T": "C"}
const BASES: Array[String] = ["A", "C", "G", "T"]

# Severity ordering used for sorting/aggregation.
const SEVERITY_ORDER: Dictionary = {
	"benign": 0, "none": 0, "protective": 0, "uncertain": 1, "mild": 2, "moderate": 3, "severe": 4
}


static func load_assembly(path: String = ASSEMBLY_PATH) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("GenomeSimulation: assembly missing at %s" % path)
		return {}
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("GenomeSimulation: cannot open %s" % path)
		return {}
	var parsed = JSON.parse_string(file.get_as_text())
	file.close()
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("GenomeSimulation: invalid JSON in %s" % path)
		return {}
	return parsed


static func chromosomes(assembly: Dictionary) -> Array:
	return assembly.get("chromosomes", [])


static func chromosome(assembly: Dictionary, name: String) -> Dictionary:
	for chr in chromosomes(assembly):
		if str(chr.get("name", "")) == name:
			return chr
	return {}


static func genes(assembly: Dictionary) -> Array:
	return assembly.get("genes", [])


static func genes_on(assembly: Dictionary, chromosome_name: String) -> Array:
	var out: Array = []
	for gene in genes(assembly):
		if str(gene.get("chromosome", "")) == chromosome_name:
			out.append(gene)
	out.sort_custom(func(a, b): return int(a.get("start", 0)) < int(b.get("start", 0)))
	return out


static func gene(assembly: Dictionary, symbol: String) -> Dictionary:
	for g in genes(assembly):
		if str(g.get("symbol", "")) == symbol:
			return g
	return {}


static func genes_overlapping(assembly: Dictionary, chromosome_name: String, start_bp: int, end_bp: int) -> Array:
	var out: Array = []
	for g in genes_on(assembly, chromosome_name):
		if int(g.get("start", 0)) <= end_bp and int(g.get("end", 0)) >= start_bp:
			out.append(g)
	return out


static func gene_at(assembly: Dictionary, chromosome_name: String, position_bp: int) -> Dictionary:
	for g in genes_on(assembly, chromosome_name):
		if position_bp >= int(g.get("start", 0)) and position_bp <= int(g.get("end", 0)):
			return g
	return {}


static func hotpot_genomic_bp(g: Dictionary, hotspot: Dictionary) -> int:
	var start := int(g.get("start", 0))
	var end := int(g.get("end", 0))
	return start + int(round(float(hotspot.get("fraction", 0.5)) * float(end - start)))


static func nearest_hotspot(g: Dictionary, position_bp: int, tolerance_bp: int = 1200) -> Dictionary:
	var best: Dictionary = {}
	var best_distance := tolerance_bp + 1
	for hs in g.get("hotspots", []):
		var distance: int = abs(hotpot_genomic_bp(g, hs) - position_bp)
		if distance <= tolerance_bp and distance < best_distance:
			best = hs
			best_distance = distance
	return best


static func classify_substitution(ref: String, alt: String) -> String:
	var r := ref.to_upper()
	var a := alt.to_upper()
	if r.length() != 1 or a.length() != 1:
		return "indel_or_complex"
	if r == a:
		return "no_change"
	if TRANSITIONS.get(r, "") == a:
		return "transition"
	return "transversion"


static func is_transition(ref: String, alt: String) -> bool:
	return classify_substitution(ref, alt) == "transition"


static func random_alt_for(ref: String, spectrum: Dictionary, rng: RandomNumberGenerator) -> String:
	var roll := rng.randf()
	var cls := "transversion"
	if roll < float(spectrum.get("transition", 0.0)):
		cls = "transition"
	elif roll < float(spectrum.get("transition", 0.0)) + float(spectrum.get("frameshift", 0.0)):
		cls = "frameshift"
	var r := ref.to_upper()
	if cls == "transition":
		return str(TRANSITIONS.get(r, "A"))
	if cls == "frameshift":
		return r
	var choices: Array = []
	for base in BASES:
		if base != r and TRANSITIONS.get(r, "") != base:
			choices.append(base)
	return str(choices[rng.randi_range(0, choices.size() - 1)]) if not choices.is_empty() else "A"


static func _zygosity_note(g: Dictionary, zygosity: String) -> Dictionary:
	for entry in g.get("phenotypes", []):
		if str(entry.get("zygosity", "")) == zygosity:
			return entry
	return {}


static func apply_point_mutation(assembly: Dictionary, symbol: String, position_bp: int, alt: String,
		zygosity: String = "heterozygous", mutagen_id: String = "spontaneous") -> Dictionary:
	var g := gene(assembly, symbol)
	if g.is_empty():
		return {"ok": false, "error": "unknown_gene", "symbol": symbol}

	var start := int(g.get("start", 0))
	var end := int(g.get("end", 0))
	var clamped := clampi(position_bp, start, end)
	var chromosome_name := str(g.get("chromosome", ""))

	var hotspot := nearest_hotspot(g, clamped)
	var mut_class := classify_substitution(_ref_base_for(g, hotspot, clamped), alt)

	var result := {
		"ok": true,
		"symbol": symbol,
		"gene_name": g.get("name", symbol),
		"chromosome": chromosome_name,
		"position": clamped,
		"gene_start": start,
		"gene_end": end,
		"ref": _ref_base_for(g, hotspot, clamped),
		"alt": alt.to_upper(),
		"zygosity": zygosity,
		"substitution_class": mut_class,
		"mutagen_id": mutagen_id,
		"hotspot": str(hotspot.get("c", "")),
		"confidence": "curated" if not hotspot.is_empty() else "unmodelled",
		"inheritance": g.get("inheritance", "")
	}

	if not hotspot.is_empty():
		var effect_key := zygosity
		if effect_key == "hemizygous" and hotspot.has("phenotype_hemi"):
			effect_key = "hemizygous"
		result["consequence"] = hotspot.get("consequence", "coding_sequence_variant")
		result["protein"] = hotspot.get("protein", "")
		result["severity"] = hotspot.get("severity", "uncertain")
		result["phenotype"] = _effect_text(g, hotspot, zygosity)
		result["hgvs"] = hotspot.get("c", "")
		result["note"] = "Curated hotspot. Phenotype text is a teaching model, not a diagnosis."
	else:
		var inherited := _zygosity_note(g, zygosity)
		result["consequence"] = "coding_sequence_variant" if str(g.get("biotype", "")) == "protein_coding" else "non_coding_variant"
		result["protein"] = "not modelled at this locus"
		result["severity"] = "uncertain"
		result["phenotype"] = "Variant of uncertain significance (VUS). Outside the curated hotspots the codon context is not modelled, so no protein effect is claimed."
		result["hgvs"] = "%s:%d%s>%s" % [chromosome_name, clamped, result["ref"], result["alt"]]
		if not inherited.is_empty():
			result["carrier_context"] = str(inherited.get("label", ""))
		result["note"] = "No curated hotspot within 1.2 kb. Reaching a real classification would need transcript models, population frequency and ACMG review."
	return result


static func _ref_base_for(g: Dictionary, hotspot: Dictionary, position_bp: int) -> String:
	if not hotspot.is_empty():
		var ref := str(hotspot.get("ref", "N")).to_upper()
		if ref.length() >= 1:
			return ref.substr(0, 1)
	var seed_value := absi(int(g.get("start", 0)) * 31 + position_bp * 17)
	return BASES[seed_value % BASES.size()]


static func _effect_text(g: Dictionary, hotspot: Dictionary, zygosity: String) -> String:
	if zygosity == "homozygous" and hotspot.has("phenotype_hom"):
		return str(hotspot.get("phenotype_hom"))
	if zygosity == "hemizygous" and hotspot.has("phenotype_hemi"):
		return str(hotspot.get("phenotype_hemi"))
	var inherited := _zygosity_note(g, zygosity)
	var base := str(hotspot.get("phenotype", ""))
	if not inherited.is_empty():
		return "%s %s" % [base, str(inherited.get("label", ""))]
	return base


static func karyotype_label(karyotype: Dictionary) -> String:
	if karyotype.is_empty():
		return "46,XX (reference diploid)"
	var parts: Array[String] = []
	var keys := karyotype.keys()
	keys.sort()
	for key in keys:
		var copies := int(karyotype[key])
		if copies == 2:
			continue
		if copies == 3:
			parts.append("+%s" % key)
		elif copies == 1:
			parts.append("-%s" % key)
		elif copies == 0:
			parts.append("-%s-%s" % [key, key])
		elif copies > 3:
			parts.append("+%s x%d" % [key, copies - 2])
	if parts.is_empty():
		return "46,XX (reference diploid)"
	return " ".join(parts)


static func dosage_effects(assembly: Dictionary, karyotype: Dictionary, sex: String = "XX") -> Array:
	var out: Array = []
	for key in karyotype.keys():
		var copies := int(karyotype[key])
		if copies == 2:
			continue
		var multiplier := float(copies) / 2.0
		var chr_name := str(key)
		var chr_variants := {
			"21": {"3": "Trisomy 21 (Down syndrome) expression model", "1": "Monosomy 21 (not viable in humans)"},
			"18": {"3": "Trisomy 18 (Edwards syndrome) expression model", "1": "Monosomy 18 (not viable)"},
			"13": {"3": "Trisomy 13 (Patau syndrome) expression model", "1": "Monosomy 13 (not viable)"},
			"X": {"1": "Monosomy X (Turner syndrome) expression model", "3": "XXX expression model"},
			"Y": {"0": "Loss of Y (46,X0-like) expression model", "2": "XYY expression model"}
		}
		var label := "%s: %d copies (%.2fx expression)" % [chr_name, copies, multiplier]
		if chr_variants.has(chr_name) and chr_variants[chr_name].has(str(copies)):
			label = str(chr_variants[chr_name][str(copies)])
		var gene_notes: Array = []
		for g in genes_on(assembly, chr_name):
			if bool(g.get("dosage_sensitive", false)):
				gene_notes.append({
					"symbol": g.get("symbol", ""),
					"expression_multiplier": multiplier,
					"summary": g.get("summary", "")
				})
		out.append({
			"chromosome": chr_name,
			"copies": copies,
			"multiplier": multiplier,
			"label": label,
			"genes": gene_notes,
			"severity": "severe" if copies == 3 and chr_name in ["13", "18", "21"] else "moderate",
			"note": "Gene dosage is modelled as a uniform copy-number multiplier. Real trisomy phenotypes are mosaic, tissue-specific and polygenic."
		})
	return out


static func mutagens(assembly: Dictionary) -> Array:
	return assembly.get("mutagens", [])


static func mutagen(assembly: Dictionary, mutagen_id: String) -> Dictionary:
	for m in mutagens(assembly):
		if str(m.get("id", "")) == mutagen_id:
			return m
	return {}


static func _weighted_chromosome(assembly: Dictionary, rng: RandomNumberGenerator) -> Dictionary:
	var list := chromosomes(assembly)
	var total := 0
	for chr in list:
		total += int(chr.get("length_bp", 0))
	var pick := rng.randi_range(1, max(total, 1))
	var running := 0
	for chr in list:
		running += int(chr.get("length_bp", 0))
		if pick <= running:
			return chr
	return list[list.size() - 1] if not list.is_empty() else {}


static func expose_to_mutagen(assembly: Dictionary, mutagen_id: String, dose: float,
		seed_value: int = 7, coding_bias: float = 0.3) -> Dictionary:
	var m := mutagen(assembly, mutagen_id)
	if m.is_empty():
		return {"ok": false, "error": "unknown_mutagen", "mutations": [], "summary": {}}

	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value

	var spectrum: Dictionary = m.get("spectrum", {})
	var frameshift_weight := float(spectrum.get("frameshift", 0.0))

	# Aneuploid mutagens (colchicine) never produce point mutations; they act on
	# the spindle, so we return a nondisjunction event instead.
	if float(spectrum.get("transition", 0.0)) == 0.0 and frameshift_weight == 0.0:
		var chr_event := _weighted_chromosome(assembly, rng)
		return {
			"ok": true,
			"mutagen": m.get("name", mutagen_id),
			"mechanism": m.get("mechanism", ""),
			"point_mutations": 0,
			"mutations": [],
			"nondisjunction": true,
			"affected_chromosome": chr_event.get("name", "?"),
			"dose": dose,
			"summary": {"nondisjunction": 1, "total": 0},
			"note": "Spindle poison: the model produces a nondisjunction event, not DNA substitutions."
		}

	var events := maxi(1, int(round(float(m.get("rate_per_unit", 1.0)) * dose)))
	events = mini(events, 64)

	var mutations: Array = []
	var summary: Dictionary = {}
	for i in range(events):
		var chr := _weighted_chromosome(assembly, rng)
		var chr_name := str(chr.get("name", ""))
		var chr_genes := genes_on(assembly, chr_name)
		if chr_genes.is_empty() or rng.randf() > coding_bias:
			var pos := rng.randi_range(1, max(int(chr.get("length_bp", 1)), 2))
			var entry := {
				"region": "intergenic",
				"chromosome": chr_name,
				"position": pos,
				"effect": "intergenic_variant",
				"severity": "benign",
				"note": "Non-coding spacer; the model records the hit without inventing a phenotype."
			}
			mutations.append(entry)
			summary["intergenic_variant"] = int(summary.get("intergenic_variant", 0)) + 1
			continue

		var g: Dictionary = chr_genes[rng.randi_range(0, chr_genes.size() - 1)]
		var start := int(g.get("start", 0))
		var end := int(g.get("end", 0))
		var position := rng.randi_range(start, max(end, start + 1))
		var ref := _ref_base_for(g, {}, position)
		var alt := random_alt_for(ref, spectrum, rng)

		# Try to land on a curated hotspot: a real mutational process is biased by
		# sequence context, so we deliberately allow a modest hotspot hit rate.
		var hotspot := nearest_hotspot(g, position, 4000)
		if not hotspot.is_empty() and rng.randf() < 0.55:
			position = hotpot_genomic_bp(g, hotspot)
			ref = _ref_base_for(g, hotspot, position)
			alt = str(hotspot.get("alt", alt))
			if alt.length() > 1:
				alt = alt.substr(0, 1)

		var consequence := apply_point_mutation(assembly, str(g.get("symbol", "")), position, alt, "heterozygous", mutagen_id)
		consequence["region"] = "coding" if not str(hotspot.get("c", "")).is_empty() else "intragenic"
		consequence["effect"] = consequence.get("consequence", "")
		mutations.append(consequence)
		var key := str(consequence.get("consequence", "variant"))
		summary[key] = int(summary.get(key, 0)) + 1

	summary["total"] = mutations.size()
	return {
		"ok": true,
		"mutagen": m.get("name", mutagen_id),
		"mechanism": m.get("mechanism", ""),
		"dose": dose,
		"point_mutations": mutations.size(),
		"nondisjunction": false,
		"mutations": mutations,
		"summary": summary,
		"note": "Mutation positions across non-curated sequence are illustrative; only curated hotspot hits carry annotated protein effects."
	}


static func aggregate_phenotypes(state: Dictionary) -> Array:
	var out: Array = []
	var seen: Dictionary = {}
	for entry in state.get("mutations", []):
		if not bool(entry.get("ok", false)):
			continue
		if str(entry.get("confidence", "")) != "curated":
			continue
		var label := str(entry.get("phenotype", ""))
		if label.is_empty() or seen.has(label):
			continue
		seen[label] = true
		out.append({
			"label": label,
			"severity": entry.get("severity", "uncertain"),
			"source": "%s %s" % [entry.get("symbol", "?"), entry.get("hgvs", "")]
		})
	for entry in state.get("dosage", []):
		var label := str(entry.get("label", ""))
		if seen.has(label):
			continue
		seen[label] = true
		out.append({
			"label": label,
			"severity": entry.get("severity", "moderate"),
			"source": "chromosome dosage"
		})
	out.sort_custom(func(a, b):
		return int(SEVERITY_ORDER.get(str(a.get("severity", "uncertain")), 1)) > int(SEVERITY_ORDER.get(str(b.get("severity", "uncertain")), 1)))
	return out


static func severity_color(severity: String) -> Color:
	match severity:
		"severe": return Color(1.0, 0.34, 0.32)
		"moderate": return Color(1.0, 0.66, 0.24)
		"mild": return Color(0.95, 0.86, 0.35)
		"uncertain": return Color(0.62, 0.68, 0.8)
		"protective": return Color(0.35, 0.85, 0.62)
		"benign", "none": return Color(0.55, 0.62, 0.58)
	return Color(0.7, 0.75, 0.85)


static func format_bp(bp_value: int) -> String:
	if bp_value >= 1000000:
		return "%.2f Mb" % (float(bp_value) / 1000000.0)
	if bp_value >= 1000:
		return "%.1f kb" % (float(bp_value) / 1000.0)
	return "%d bp" % bp_value
