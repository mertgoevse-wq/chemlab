# Athanor Ascension - Reaction Evaluator (Embedded Chemistry Engine)
# Core analytical chemistry calculations for Godot 4.7
# Used by SimulationBridge in EMBEDDED_FALLBACK mode

extends Resource

class_name ReactionEvaluator

# Species database with thermodynamic properties
# Based on NIST/CRC Handbook values
var species_db: Dictionary = {}

func _init() -> void:
	_initialize_species_database()

func _initialize_species_database() -> void:
	species_db = {
		# Water
		"H2O": {
			"formula": "H2O",
			"name": "Water",
			"molecular_weight_g_mol": 18.015,
			"density_g_cm3": 1.0,
			"delta_h_f_kj_mol": -285.83,
			"s_standard_j_mol_k": 69.91,
			"cp_j_mol_k": 75.38,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 15.7,
			"boiling_point_c": 100.0,
			"flash_point_c": -1.0,
			"is_volatile": true,
			"ghs_pictograms": [],
			"h_statements": [],
			"p_statements": [],
			"cas_number": "7732-18-5"
		},

		# Strong acids
		"HCl_aq": {
			"formula": "HCl",
			"name": "Hydrochloric Acid (aq)",
			"molecular_weight_g_mol": 36.461,
			"density_g_cm3": 1.18,
			"delta_h_f_kj_mol": -167.16,
			"s_standard_j_mol_k": 56.5,
			"cp_j_mol_k": 75.0,
			"is_acid": true,
			"is_base": false,
			"acid_pka": -7.0,
			"boiling_point_c": 110.0,
			"flash_point_c": -1.0,
			"is_volatile": true,
			"ghs_pictograms": ["GHS05", "GHS07"],
			"h_statements": ["H314", "H335"],
			"p_statements": ["P260", "P280", "P305+P351+P338"],
			"cas_number": "7647-01-0"
		},

		"H2SO4_aq": {
			"formula": "H2SO4",
			"name": "Sulfuric Acid",
			"molecular_weight_g_mol": 98.079,
			"density_g_cm3": 1.84,
			"delta_h_f_kj_mol": -909.27,
			"s_standard_j_mol_k": 20.1,
			"cp_j_mol_k": 138.0,
			"is_acid": true,
			"is_base": false,
			"acid_pka": -3.0,
			"boiling_point_c": 337.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": ["GHS05"],
			"h_statements": ["H314"],
			"p_statements": ["P280", "P305+P351+P338"],
			"cas_number": "7664-93-9"
		},

		"HNO3_aq": {
			"formula": "HNO3",
			"name": "Nitric Acid",
			"molecular_weight_g_mol": 63.013,
			"density_g_cm3": 1.51,
			"delta_h_f_kj_mol": -207.36,
			"s_standard_j_mol_k": 146.4,
			"cp_j_mol_k": 109.9,
			"is_acid": true,
			"is_base": false,
			"acid_pka": -1.4,
			"boiling_point_c": 121.0,
			"flash_point_c": -1.0,
			"is_volatile": true,
			"ghs_pictograms": ["GHS03", "GHS05", "GHS07"],
			"h_statements": ["H272", "H314", "H331"],
			"p_statements": ["P210", "P280", "P305+P351+P338"],
			"cas_number": "7697-37-2"
		},

		# Strong bases
		"NaOH_aq": {
			"formula": "NaOH",
			"name": "Sodium Hydroxide (aq)",
			"molecular_weight_g_mol": 39.997,
			"density_g_cm3": 2.13,
			"delta_h_f_kj_mol": -470.11,
			"s_standard_j_mol_k": 48.1,
			"cp_j_mol_k": 87.0,
			"is_acid": false,
			"is_base": true,
			"acid_pka": 15.7,
			"boiling_point_c": 1390.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": ["GHS05"],
			"h_statements": ["H314"],
			"p_statements": ["P280", "P305+P351+P338"],
			"cas_number": "1310-73-2"
		},

		"KOH_aq": {
			"formula": "KOH",
			"name": "Potassium Hydroxide (aq)",
			"molecular_weight_g_mol": 56.106,
			"density_g_cm3": 2.04,
			"delta_h_f_kj_mol": -482.4,
			"s_standard_j_mol_k": 78.9,
			"cp_j_mol_k": 95.0,
			"is_acid": false,
			"is_base": true,
			"acid_pka": 15.7,
			"boiling_point_c": 1327.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": ["GHS05"],
			"h_statements": ["H314"],
			"p_statements": ["P280", "P305+P351+P338"],
			"cas_number": "1310-58-3"
		},

		# Weak acids
		"CH3COOH_aq": {
			"formula": "CH3COOH",
			"name": "Acetic Acid",
			"molecular_weight_g_mol": 60.052,
			"density_g_cm3": 1.05,
			"delta_h_f_kj_mol": -484.5,
			"s_standard_j_mol_k": 159.8,
			"cp_j_mol_k": 124.3,
			"is_acid": true,
			"is_base": false,
			"acid_pka": 4.76,
			"boiling_point_c": 118.0,
			"flash_point_c": 39.0,
			"is_volatile": true,
			"ghs_pictograms": ["GHS02", "GHS05", "GHS07"],
			"h_statements": ["H226", "H314", "H332"],
			"p_statements": ["P210", "P280", "P305+P351+P338"],
			"cas_number": "64-19-7"
		},

		"C7H6O3": {
			"formula": "C7H6O3",
			"name": "Salicylic Acid",
			"molecular_weight_g_mol": 138.121,
			"density_g_cm3": 1.44,
			"delta_h_f_kj_mol": -589.9,
			"s_standard_j_mol_k": 180.2,
			"cp_j_mol_k": 159.0,
			"is_acid": true,
			"is_base": false,
			"acid_pka": 2.97,
			"boiling_point_c": 211.0,
			"flash_point_c": 157.0,
			"is_volatile": false,
			"ghs_pictograms": ["GHS07"],
			"h_statements": ["H315", "H319", "H335"],
			"p_statements": ["P261", "P280", "P305+P351+P338"],
			"cas_number": "69-72-7"
		},

		"C4H6O3": {
			"formula": "C4H6O3",
			"name": "Acetic Anhydride",
			"molecular_weight_g_mol": 102.089,
			"density_g_cm3": 1.08,
			"delta_h_f_kj_mol": -624.4,
			"s_standard_j_mol_k": 269.0,
			"cp_j_mol_k": 182.0,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 15.0,
			"boiling_point_c": 140.0,
			"flash_point_c": 49.0,
			"is_volatile": true,
			"ghs_pictograms": ["GHS02", "GHS05", "GHS07"],
			"h_statements": ["H226", "H314", "H332"],
			"p_statements": ["P210", "P280", "P305+P351+P338"],
			"cas_number": "108-24-7"
		},

		"C9H8O4": {
			"formula": "C9H8O4",
			"name": "Acetylsalicylic Acid (Aspirin)",
			"molecular_weight_g_mol": 180.158,
			"density_g_cm3": 1.40,
			"delta_h_f_kj_mol": -756.2,
			"s_standard_j_mol_k": 208.5,
			"cp_j_mol_k": 210.0,
			"is_acid": true,
			"is_base": false,
			"acid_pka": 3.49,
			"boiling_point_c": 140.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": ["GHS07"],
			"h_statements": ["H315", "H319"],
			"p_statements": ["P280", "P305+P351+P338"],
			"cas_number": "50-78-2"
		},

		"C6H7NO": {
			"formula": "C6H7NO",
			"name": "4-Aminophenol",
			"molecular_weight_g_mol": 109.126,
			"density_g_cm3": 1.29,
			"delta_h_f_kj_mol": -184.2,
			"s_standard_j_mol_k": 155.0,
			"cp_j_mol_k": 145.0,
			"is_acid": false,
			"is_base": true,
			"acid_pka": 10.3,
			"boiling_point_c": 284.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": ["GHS07", "GHS09"],
			"h_statements": ["H301", "H315", "H319", "H410"],
			"p_statements": ["P273", "P280", "P305+P351+P338"],
			"cas_number": "123-30-8"
		},

		"C8H9NO2": {
			"formula": "C8H9NO2",
			"name": "Paracetamol",
			"molecular_weight_g_mol": 151.163,
			"density_g_cm3": 1.26,
			"delta_h_f_kj_mol": -445.8,
			"s_standard_j_mol_k": 195.0,
			"cp_j_mol_k": 192.0,
			"is_acid": true,
			"is_base": false,
			"acid_pka": 9.5,
			"boiling_point_c": 420.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": ["GHS07"],
			"h_statements": ["H301", "H315", "H319"],
			"p_statements": ["P280", "P305+P351+P338"],
			"cas_number": "103-90-2"
		},

		# Salts
		"NaCl_aq": {
			"formula": "NaCl",
			"name": "Sodium Chloride (aq)",
			"molecular_weight_g_mol": 58.443,
			"density_g_cm3": 2.16,
			"delta_h_f_kj_mol": -407.27,
			"s_standard_j_mol_k": 115.5,
			"cp_j_mol_k": 85.0,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 7.0,
			"boiling_point_c": 1465.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": [],
			"h_statements": [],
			"p_statements": [],
			"cas_number": "7647-14-5"
		},

		"NaHCO3_aq": {
			"formula": "NaHCO3",
			"name": "Sodium Bicarbonate",
			"molecular_weight_g_mol": 84.007,
			"density_g_cm3": 2.20,
			"delta_h_f_kj_mol": -950.8,
			"s_standard_j_mol_k": 101.7,
			"cp_j_mol_k": 87.6,
			"is_acid": false,
			"is_base": true,
			"acid_pka": 10.3,
			"boiling_point_c": 851.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": [],
			"h_statements": [],
			"p_statements": [],
			"cas_number": "144-55-8"
		},

		# Peroxides
		"H2O2_aq": {
			"formula": "H2O2",
			"name": "Hydrogen Peroxide",
			"molecular_weight_g_mol": 34.015,
			"density_g_cm3": 1.45,
			"delta_h_f_kj_mol": -191.17,
			"s_standard_j_mol_k": 143.9,
			"cp_j_mol_k": 89.1,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 11.7,
			"boiling_point_c": 150.0,
			"flash_point_c": -1.0,
			"is_volatile": true,
			"ghs_pictograms": ["GHS03", "GHS05", "GHS07"],
			"h_statements": ["H272", "H314", "H332"],
			"p_statements": ["P210", "P280", "P305+P351+P338"],
			"cas_number": "7722-84-1"
		},

		# Iodides
		"KI_aq": {
			"formula": "KI",
			"name": "Potassium Iodide",
			"molecular_weight_g_mol": 166.002,
			"density_g_cm3": 3.12,
			"delta_h_f_kj_mol": -327.9,
			"s_standard_j_mol_k": 106.3,
			"cp_j_mol_k": 51.3,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 7.0,
			"boiling_point_c": 1330.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": [],
			"h_statements": [],
			"p_statements": [],
			"cas_number": "7681-11-0"
		},

		# Gases
		"O2_gas": {
			"formula": "O2",
			"name": "Oxygen Gas",
			"molecular_weight_g_mol": 31.999,
			"density_g_cm3": 0.0014,
			"delta_h_f_kj_mol": 0.0,
			"s_standard_j_mol_k": 205.15,
			"cp_j_mol_k": 29.38,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 7.0,
			"boiling_point_c": -183.0,
			"flash_point_c": -1.0,
			"is_volatile": true,
			"ghs_pictograms": ["GHS03", "GHS04"],
			"h_statements": ["H270", "H280"],
			"p_statements": ["P220", "P244"],
			"cas_number": "7782-44-7"
		},

		"CO2_gas": {
			"formula": "CO2",
			"name": "Carbon Dioxide",
			"molecular_weight_g_mol": 44.01,
			"density_g_cm3": 0.0019,
			"delta_h_f_kj_mol": -393.51,
			"s_standard_j_mol_k": 213.74,
			"cp_j_mol_k": 37.11,
			"is_acid": true,
			"is_base": false,
			"acid_pka": 6.35,
			"boiling_point_c": -78.5,
			"flash_point_c": -1.0,
			"is_volatile": true,
			"ghs_pictograms": ["GHS04"],
			"h_statements": ["H280"],
			"p_statements": ["P403"],
			"cas_number": "124-38-9"
		},

		# Organic solvents
		"C2H5OH": {
			"formula": "C2H5OH",
			"name": "Ethanol",
			"molecular_weight_g_mol": 46.068,
			"density_g_cm3": 0.789,
			"delta_h_f_kj_mol": -277.69,
			"s_standard_j_mol_k": 160.7,
			"cp_j_mol_k": 112.3,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 15.9,
			"boiling_point_c": 78.37,
			"flash_point_c": 13.0,
			"is_volatile": true,
			"ghs_pictograms": ["GHS02", "GHS07"],
			"h_statements": ["H225", "H319"],
			"p_statements": ["P210", "P280", "P305+P351+P338"],
			"cas_number": "64-17-5"
		},

		"CH3OH": {
			"formula": "CH3OH",
			"name": "Methanol",
			"molecular_weight_g_mol": 32.042,
			"density_g_cm3": 0.792,
			"delta_h_f_kj_mol": -238.6,
			"s_standard_j_mol_k": 126.8,
			"cp_j_mol_k": 81.6,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 15.5,
			"boiling_point_c": 64.7,
			"flash_point_c": 11.0,
			"is_volatile": true,
			"ghs_pictograms": ["GHS02", "GHS06", "GHS08"],
			"h_statements": ["H225", "H301", "H311", "H331", "H370"],
			"p_statements": ["P210", "P280", "P305+P351+P338", "P310"],
			"cas_number": "67-56-1"
		},

		"C4H10O": {
			"formula": "C4H10O",
			"name": "Diethyl Ether",
			"molecular_weight_g_mol": 74.122,
			"density_g_cm3": 0.713,
			"delta_h_f_kj_mol": -279.3,
			"s_standard_j_mol_k": 218.4,
			"cp_j_mol_k": 172.5,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 15.0,
			"boiling_point_c": 34.6,
			"flash_point_c": -45.0,
			"is_volatile": true,
			"ghs_pictograms": ["GHS02", "GHS07"],
			"h_statements": ["H224", "H319", "H336"],
			"p_statements": ["P210", "P280", "P305+P351+P338"],
			"cas_number": "60-29-7"
		},

		"C4H8O2": {
			"formula": "C4H8O2",
			"name": "Ethyl Acetate",
			"molecular_weight_g_mol": 88.11,
			"density_g_cm3": 0.902,
			"delta_h_f_kj_mol": -480.0,
			"s_standard_j_mol_k": 259.4,
			"cp_j_mol_k": 170.1,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 15.0,
			"boiling_point_c": 77.1,
			"flash_point_c": -4.0,
			"is_volatile": true,
			"ghs_pictograms": ["GHS02", "GHS07"],
			"h_statements": ["H225", "H319", "H336"],
			"p_statements": ["P210", "P280", "P305+P351+P338"],
			"cas_number": "141-78-6"
		},

		# Indicators
		"phenolphthalein": {
			"formula": "C20H14O4",
			"name": "Phenolphthalein",
			"molecular_weight_g_mol": 318.32,
			"density_g_cm3": 1.27,
			"delta_h_f_kj_mol": -500.0,
			"s_standard_j_mol_k": 200.0,
			"cp_j_mol_k": 200.0,
			"is_acid": true,
			"is_base": false,
			"acid_pka": 9.4,
			"boiling_point_c": 300.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": [],
			"h_statements": [],
			"p_statements": [],
			"cas_number": "77-09-8"
		},

		# Manganese compounds (for Briggs-Rauscher)
		"MnSO4_aq": {
			"formula": "MnSO4",
			"name": "Manganese(II) Sulfate",
			"molecular_weight_g_mol": 151.001,
			"density_g_cm3": 3.25,
			"delta_h_f_kj_mol": -1065.0,
			"s_standard_j_mol_k": 120.0,
			"cp_j_mol_k": 100.0,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 7.0,
			"boiling_point_c": 700.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": ["GHS07", "GHS09"],
			"h_statements": ["H302", "H315", "H319", "H410"],
			"p_statements": ["P273", "P280", "P305+P351+P338"],
			"cas_number": "7785-87-7"
		},

		"KIO3_aq": {
			"formula": "KIO3",
			"name": "Potassium Iodate",
			"molecular_weight_g_mol": 214.001,
			"density_g_cm3": 3.89,
			"delta_h_f_kj_mol": -490.0,
			"s_standard_j_mol_k": 150.0,
			"cp_j_mol_k": 110.0,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 7.0,
			"boiling_point_c": 560.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": ["GHS03", "GHS07"],
			"h_statements": ["H272", "H302", "H315", "H319"],
			"p_statements": ["P210", "P280", "P305+P351+P338"],
			"cas_number": "7758-05-6"
		},

		"malonic_acid": {
			"formula": "C3H4O4",
			"name": "Malonic Acid",
			"molecular_weight_g_mol": 104.06,
			"density_g_cm3": 1.62,
			"delta_h_f_kj_mol": -850.0,
			"s_standard_j_mol_k": 160.0,
			"cp_j_mol_k": 130.0,
			"is_acid": true,
			"is_base": false,
			"acid_pka": 2.83,
			"boiling_point_c": 200.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": ["GHS07"],
			"h_statements": ["H315", "H319"],
			"p_statements": ["P280", "P305+P351+P338"],
			"cas_number": "141-82-2"
		},

		# Silver nitrate
		"AgNO3_aq": {
			"formula": "AgNO3",
			"name": "Silver Nitrate",
			"molecular_weight_g_mol": 169.87,
			"density_g_cm3": 4.35,
			"delta_h_f_kj_mol": -124.4,
			"s_standard_j_mol_k": 140.9,
			"cp_j_mol_k": 93.0,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 7.0,
			"boiling_point_c": 440.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": ["GHS03", "GHS05", "GHS09"],
			"h_statements": ["H272", "H314", "H410"],
			"p_statements": ["P210", "P280", "P305+P351+P338", "P273"],
			"cas_number": "7761-88-8"
		},

		# Barium chloride
		"BaCl2_aq": {
			"formula": "BaCl2",
			"name": "Barium Chloride",
			"molecular_weight_g_mol": 208.23,
			"density_g_cm3": 3.51,
			"delta_h_f_kj_mol": -858.0,
			"s_standard_j_mol_k": 130.0,
			"cp_j_mol_k": 100.0,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 7.0,
			"boiling_point_c": 1560.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": ["GHS06", "GHS09"],
			"h_statements": ["H301", "H332", "H410"],
			"p_statements": ["P280", "P305+P351+P338", "P273"],
			"cas_number": "10361-37-2"
		},

		# Lead nitrate
		"PbNO3_aq": {
			"formula": "Pb(NO3)2",
			"name": "Lead(II) Nitrate",
			"molecular_weight_g_mol": 331.2,
			"density_g_cm3": 4.53,
			"delta_h_f_kj_mol": -416.0,
			"s_standard_j_mol_k": 180.0,
			"cp_j_mol_k": 120.0,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 7.0,
			"boiling_point_c": 470.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": ["GHS03", "GHS06", "GHS08", "GHS09"],
			"h_statements": ["H272", "H301", "H332", "H360Df", "H373", "H410"],
			"p_statements": ["P201", "P280", "P305+P351+P338", "P273"],
			"cas_number": "10099-74-8"
		},

		# Calcium carbonate
		"CaCO3_s": {
			"formula": "CaCO3",
			"name": "Calcium Carbonate",
			"molecular_weight_g_mol": 100.09,
			"density_g_cm3": 2.71,
			"delta_h_f_kj_mol": -1207.0,
			"s_standard_j_mol_k": 92.9,
			"cp_j_mol_k": 81.9,
			"is_acid": false,
			"is_base": true,
			"acid_pka": 9.0,
			"boiling_point_c": 825.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": [],
			"h_statements": [],
			"p_statements": [],
			"cas_number": "471-34-1"
		},

		# Iron(III) chloride
		"FeCl3_aq": {
			"formula": "FeCl3",
			"name": "Iron(III) Chloride",
			"molecular_weight_g_mol": 162.2,
			"density_g_cm3": 2.90,
			"delta_h_f_kj_mol": -399.5,
			"s_standard_j_mol_k": 142.3,
			"cp_j_mol_k": 96.6,
			"is_acid": true,
			"is_base": false,
			"acid_pka": 2.0,
			"boiling_point_c": 315.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": ["GHS05", "GHS07"],
			"h_statements": ["H314", "H332"],
			"p_statements": ["P280", "P305+P351+P338"],
			"cas_number": "7705-08-0"
		},

		# Copper(II) sulfate
		"CuSO4_aq": {
			"formula": "CuSO4",
			"name": "Copper(II) Sulfate",
			"molecular_weight_g_mol": 159.609,
			"density_g_cm3": 2.28,
			"delta_h_f_kj_mol": -771.4,
			"s_standard_j_mol_k": -99.0,
			"cp_j_mol_k": 100.0,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 7.0,
			"boiling_point_c": 650.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": ["GHS07", "GHS09"],
			"h_statements": ["H302", "H315", "H319", "H410"],
			"p_statements": ["P273", "P280", "P305+P351+P338"],
			"cas_number": "7758-99-8"
		},

		# Sodium thiosulfate
		"Na2S2O3_aq": {
			"formula": "Na2S2O3",
			"name": "Sodium Thiosulfate",
			"molecular_weight_g_mol": 158.11,
			"density_g_cm3": 1.667,
			"delta_h_f_kj_mol": -1123.0,
			"s_standard_j_mol_k": 155.0,
			"cp_j_mol_k": 130.0,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 7.0,
			"boiling_point_c": 300.0,
			"flash_point_c": -1.0,
			"is_volatile": false,
			"ghs_pictograms": [],
			"h_statements": [],
			"p_statements": [],
			"cas_number": "7772-98-7"
		},

		# Ions (for precipitation calculations)
		"Ag+": {
			"formula": "Ag+",
			"name": "Silver Ion",
			"molecular_weight_g_mol": 107.87,
			"density_g_cm3": 1.0,
			"delta_h_f_kj_mol": 105.0,
			"s_standard_j_mol_k": 72.0,
			"cp_j_mol_k": 50.0,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 7.0,
			"is_ion": true
		},

		"Cl-": {
			"formula": "Cl-",
			"name": "Chloride Ion",
			"molecular_weight_g_mol": 35.45,
			"density_g_cm3": 1.0,
			"delta_h_f_kj_mol": -167.2,
			"s_standard_j_mol_k": 56.5,
			"cp_j_mol_k": 50.0,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 7.0,
			"is_ion": true
		},

		"Ba2+": {
			"formula": "Ba2+",
			"name": "Barium Ion",
			"molecular_weight_g_mol": 137.33,
			"density_g_cm3": 1.0,
			"delta_h_f_kj_mol": -537.6,
			"s_standard_j_mol_k": 8.0,
			"cp_j_mol_k": 50.0,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 7.0,
			"is_ion": true
		},

		"SO4^2-": {
			"formula": "SO4^2-",
			"name": "Sulfate Ion",
			"molecular_weight_g_mol": 96.06,
			"density_g_cm3": 1.0,
			"delta_h_f_kj_mol": -909.3,
			"s_standard_j_mol_k": 20.1,
			"cp_j_mol_k": 50.0,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 7.0,
			"is_ion": true
		},

		"Pb2+": {
			"formula": "Pb2+",
			"name": "Lead(II) Ion",
			"molecular_weight_g_mol": 207.2,
			"density_g_cm3": 1.0,
			"delta_h_f_kj_mol": 0.0,
			"s_standard_j_mol_k": 18.5,
			"cp_j_mol_k": 50.0,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 7.0,
			"is_ion": true
		},

		"Ca2+": {
			"formula": "Ca2+",
			"name": "Calcium Ion",
			"molecular_weight_g_mol": 40.08,
			"density_g_cm3": 1.0,
			"delta_h_f_kj_mol": -542.8,
			"s_standard_j_mol_k": -53.1,
			"cp_j_mol_k": 50.0,
			"is_acid": false,
			"is_base": false,
			"acid_pka": 7.0,
			"is_ion": true
		},

		"CO3^2-": {
			"formula": "CO3^2-",
			"name": "Carbonate Ion",
			"molecular_weight_g_mol": 60.01,
			"density_g_cm3": 1.0,
			"delta_h_f_kj_mol": -677.1,
			"s_standard_j_mol_k": -56.9,
			"cp_j_mol_k": 50.0,
			"is_acid": false,
			"is_base": true,
			"acid_pka": 10.3,
			"is_ion": true
		},

		"Fe3+": {
			"formula": "Fe3+",
			"name": "Iron(III) Ion",
			"molecular_weight_g_mol": 55.85,
			"density_g_cm3": 1.0,
			"delta_h_f_kj_mol": -48.5,
			"s_standard_j_mol_k": -137.7,
			"cp_j_mol_k": 50.0,
			"is_acid": true,
			"is_base": false,
			"acid_pka": 2.2,
			"is_ion": true
		},

		"OH-": {
			"formula": "OH-",
			"name": "Hydroxide Ion",
			"molecular_weight_g_mol": 17.01,
			"density_g_cm3": 1.0,
			"delta_h_f_kj_mol": -230.0,
			"s_standard_j_mol_k": -10.9,
			"cp_j_mol_k": 50.0,
			"is_acid": false,
			"is_base": true,
			"acid_pka": 15.7,
			"is_ion": true
		},

		"Cu2+": {
			"formula": "Cu2+",
			"name": "Copper(II) Ion",
			"molecular_weight_g_mol": 63.55,
			"density_g_cm3": 1.0,
			"delta_h_f_kj_mol": 64.8,
			"s_standard_j_mol_k": -99.6,
			"cp_j_mol_k": 50.0,
			"is_acid": true,
			"is_base": false,
			"acid_pka": 7.0,
			"is_ion": true
		}
	}

# =============================================================================
# SPECIES LOOKUP
# =============================================================================

func has_species(species_id: String) -> bool:
	return species_db.has(species_id)

func get_species(species_id: String) -> Dictionary:
	if species_db.has(species_id):
		return species_db[species_id].duplicate(true)
	return {}

func get_all_species() -> Array[String]:
	return species_db.keys()

# =============================================================================
# THERMODYNAMIC CALCULATIONS
# =============================================================================

const R_GAS: float = 8.314462618

func calculate_delta_h(reactants: Dictionary, products: Dictionary) -> float:
	# ΔH°_rxn = Σ (ν_prod * ΔH°_f,prod) - Σ (ν_react * ΔH°_f,react)
	var h_reactants = 0.0
	var h_products = 0.0

	for species_id in reactants:
		if species_db.has(species_id):
			h_reactants += reactants[species_id] * species_db[species_id].delta_h_f_kj_mol

	for species_id in products:
		if species_db.has(species_id):
			h_products += products[species_id] * species_db[species_id].delta_h_f_kj_mol

	return h_products - h_reactants

func calculate_delta_s(reactants: Dictionary, products: Dictionary) -> float:
	# ΔS°_rxn = Σ (ν_prod * S°_prod) - Σ (ν_react * S°_react)
	var s_reactants = 0.0
	var s_products = 0.0

	for species_id in reactants:
		if species_db.has(species_id):
			s_reactants += reactants[species_id] * species_db[species_id].s_standard_j_mol_k

	for species_id in products:
		if species_db.has(species_id):
			s_products += products[species_id] * species_db[species_id].s_standard_j_mol_k

	return s_products - s_reactants

func calculate_delta_g(delta_h_kj_mol: float, delta_s_j_mol_k: float, temperature_c: float) -> float:
	# ΔG°(T) = ΔH° - T * ΔS°
	var temp_k = temperature_c + 273.15
	return delta_h_kj_mol - (temp_k * (delta_s_j_mol_k / 1000.0))

func calculate_k_eq(delta_g_kj_mol: float, temperature_c: float) -> float:
	# K_eq(T) = exp(-ΔG° / (R * T))
	var temp_k = temperature_c + 273.15
	var exponent = -(delta_g_kj_mol * 1000.0) / (R_GAS * temp_k)
	# Clamp to prevent overflow
	exponent = clamp(exponent, -700.0, 700.0)
	return exp(exponent)

func calculate_arrhenius_k(temperature_c: float, activation_energy_kj_mol: float = 55.0, pre_exponential_factor_a: float = 1.0e11) -> float:
	# k(T) = A * exp(-E_a / (R * T))
	var temp_k = temperature_c + 273.15
	var ea_j = activation_energy_kj_mol * 1000.0
	var arrhenius_exp = -ea_j / (R_GAS * temp_k)
	arrhenius_exp = clamp(arrhenius_exp, -700.0, 700.0)
	return pre_exponential_factor_a * exp(arrhenius_exp)

func calculate_adiabatic_temp_rise(delta_h_kj_mol: float, moles_reacted: float, total_mass_g: float, cp_j_g_k: float) -> float:
	# ΔT_ad = -ΔH° * moles / (mass * Cp)
	if total_mass_g <= 0.0 or cp_j_g_k <= 0.0:
		return 0.0
	return max(0.0, (-delta_h_kj_mol * 1000.0 * moles_reacted) / (total_mass_g * cp_j_g_k))

# =============================================================================
# ACID-BASE CALCULATIONS
# =============================================================================

func henderson_hasselbalch_ph(pka: float, conc_base: float, conc_acid: float) -> float:
	# pH = pKa + log10([base]/[acid])
	if conc_acid <= 0.0:
		return 14.0
	var ratio = conc_base / max(conc_acid, 1e-10)
	return pka + log10(ratio)

func log10(val: float) -> float:
	if val <= 0.0:
		return -20.0
	return log(val) / log(10.0)

# =============================================================================
# TITRATION CURVES
# =============================================================================

func calculate_titration_curve(analyte_conc_m: float, analyte_vol_ml: float, titrant_conc_m: float, pka: float = 4.76, points: int = 50) -> Array:
	# Returns array of {volume_ml, pH}
	var v_equiv_ml = (analyte_conc_m * analyte_vol_ml) / titrant_conc_m
	var curve: Array = []

	var max_v = v_equiv_ml * 2.0
	var step = max_v / float(points)

	for i in range(points + 1):
		var v_add = i * step
		var ph: float

		if v_add == 0:
			# Pure weak acid
			ph = 0.5 * (pka - log10(max(1e-5, analyte_conc_m)))
		elif v_add < v_equiv_ml:
			# Buffer region
			var fraction = v_add / v_equiv_ml
			var ratio = fraction / max(1e-6, 1.0 - fraction)
			ph = pka + log10(max(1e-4, ratio))
		elif abs(v_add - v_equiv_ml) < (step * 0.25):
			# Equivalence point
			var salt_conc = (analyte_conc_m * analyte_vol_ml) / (analyte_vol_ml + v_add)
			var poh = 0.5 * ((14.0 - pka) - log10(max(1e-5, salt_conc)))
			ph = 14.0 - poh
		else:
			# Excess strong base
			var excess_moles = (v_add - v_equiv_ml) * 0.001 * titrant_conc_m
			var total_vol_l = (analyte_vol_ml + v_add) * 0.001
			var oh_conc = excess_moles / total_vol_l
			var poh = -log10(max(1e-14, oh_conc))
			ph = min(14.0, 14.0 - poh)

		curve.append({ "volume_ml": round(v_add, 2), "pH": round(max(0.0, min(14.0, ph)), 2) })

	return curve

# =============================================================================
# SOLUBILITY PRODUCT / PRECIPITATION
# =============================================================================

func solubility_product_check(conc_a: float, conc_b: float, ksp: float, stoichiometry: String = "1:1") -> bool:
	# Check if ionic product exceeds Ksp
	var ip: float

	match stoichiometry:
		"1:1":
			ip = conc_a * conc_b
		"1:2":
			ip = conc_a * conc_b * conc_b
		"2:1":
			ip = conc_a * conc_a * conc_b
		"1:3":
			ip = conc_a * conc_b * conc_b * conc_b
		"3:1":
			ip = conc_a * conc_a * conc_a * conc_b
		_:
			ip = conc_a * conc_b

	return ip > ksp

func calculate_precipitation_amount(conc_a: float, conc_b: float, ksp: float, volume_l: float, stoichiometry: String = "1:1") -> float:
	# Calculate moles of precipitate formed
	# Simplified: assume complete precipitation until IP = Ksp
	var ip: float
	match stoichiometry:
		"1:1":
			ip = conc_a * conc_b
		"1:2":
			ip = conc_a * conc_b * conc_b
		"2:1":
			ip = conc_a * conc_a * conc_b
		_:
			ip = conc_a * conc_b

	if ip <= ksp:
		return 0.0

	# Approximate: precipitate until one ion is limiting or IP = Ksp
	var limiting = min(conc_a, conc_b)
	return limiting * volume_l * 0.5  # Simplified

# =============================================================================
# INDICATOR COLORS
# =============================================================================

func phenolphthalein_color(pH: float) -> Color:
	# Phenolphthalein: colorless < 8.2, pink 8.2-10, magenta > 10
	if pH < 8.2:
		return Color(1.0, 1.0, 1.0, 0.0)  # Colorless
	elif pH < 9.0:
		var alpha = (pH - 8.2) / 0.8 * 0.6
		return Color(1.0, 1.0 - alpha * 0.3, 1.0 - alpha * 0.2, alpha)
	elif pH < 10.0:
		var alpha = 0.6 + (pH - 9.0) / 1.0 * 0.4
		return Color(1.0, 0.72 - (alpha - 0.6) * 0.5, 0.82 - (alpha - 0.6) * 0.3, alpha)
	else:
		return Color(0.92, 0.08, 0.55, 1.0)  # Vibrant magenta

func bromothymol_blue_color(pH: float) -> Color:
	# Yellow < 6.0, green 6.0-7.6, blue > 7.6
	if pH < 6.0:
		return Color(1.0, 1.0, 0.0, 1.0)
	elif pH < 7.6:
		var t = (pH - 6.0) / 1.6
		return Color(1.0 - t, 1.0, t, 1.0)
	else:
		return Color(0.0, 0.2, 1.0, 1.0)

func methyl_orange_color(pH: float) -> Color:
	# Red < 3.1, orange 3.1-4.4, yellow > 4.4
	if pH < 3.1:
		return Color(1.0, 0.0, 0.0, 1.0)
	elif pH < 4.4:
		var t = (pH - 3.1) / 1.3
		return Color(1.0, t * 0.5, 0.0, 1.0)
	else:
		return Color(1.0, 1.0, 0.0, 1.0)

# =============================================================================
# REACTION KINETICS (Embedded)
# =============================================================================

func calculate_reaction_rate(conc_a: float, conc_b: float, temperature_c: float, ea_kj_mol: float = 56.0, a_factor: float = 1.0e7) -> float:
	# Rate = k * [A] * [B] for bimolecular
	var k = calculate_arrhenius_k(temperature_c, ea_kj_mol, a_factor)
	return k * conc_a * conc_b

func calculate_h2o2_decomposition_rate(h2o2_conc: float, ki_conc: float, temperature_c: float) -> float:
	# H2O2 + I- -> H2O + O2 (catalyzed)
	# Rate = k [H2O2][I-]
	var ea = 56.0  # kJ/mol
	var A = 1e7
	var temp_k = temperature_c + 273.15
	var k = A * exp(-ea * 1000.0 / (R_GAS * temp_k))
	return k * h2o2_conc * ki_conc

# =============================================================================
# OSCILLATING REACTIONS (Briggs-Rauscher)
# =============================================================================

func check_br_conditions(species_concentrations: Dictionary) -> bool:
	# Briggs-Rauscher: H2O2 + IO3- + Malonic Acid + Mn2+
	return (species_concentrations.get("H2O2_aq", 0) > 0 and
		species_concentrations.get("KIO3_aq", 0) > 0 and
		species_concentrations.get("malonic_acid", 0) > 0 and
		species_concentrations.get("MnSO4_aq", 0) > 0)

func step_br_oscillator(species_concentrations: Dictionary, dt: float, reaction_progress: float) -> Dictionary:
	var result = { "phase_changed": false }

	var ma_conc = species_concentrations.get("malonic_acid", 0)
	if ma_conc <= 0:
		return result

	var base_period = 8.0  # seconds
	var period = base_period / max(ma_conc, 0.01)

	var phase_duration = period / 3.0
	reaction_progress += dt

	var cycle_pos = fmod(reaction_progress, period)

	var new_phase = 0
	var new_color = Color(1.0, 1.0, 1.0, 1.0)

	if cycle_pos < phase_duration:
		new_phase = 1
		new_color = Color(0.95, 0.98, 1.0, 1.0)  # Clear
	elif cycle_pos < 2 * phase_duration:
		new_phase = 2
		new_color = Color(0.96, 0.72, 0.24, 1.0)  # Amber
	else:
		new_phase = 3
		new_color = Color(0.14, 0.22, 0.64, 1.0)  # Deep Blue

	return {
		"phase_changed": true,
		"phase": new_phase,
		"color": new_color,
		"reaction_progress": reaction_progress
	}

# =============================================================================
# SAFETY CHECKS
# =============================================================================

func check_thermal_hazard(temperature_c: float) -> Array[String]:
	var warnings = []
	if temperature_c > 100.0:
		warnings.append("BOILING: Temperature %0.1f°C exceeds 100°C" % temperature_c)
	elif temperature_c > 80.0:
		warnings.append("High temperature: %0.1f°C" % temperature_c)
	return warnings

func check_pressure_hazard(gas_moles: float, headspace_volume_ml: float, temperature_c: float) -> Array[String]:
	var warnings = []
	if gas_moles > 0 and headspace_volume_ml > 0:
		var temp_k = temperature_c + 273.15
		var vol_l = headspace_volume_ml / 1000.0
		var pressure_pa = gas_moles * R_GAS * temp_k / vol_l
		var pressure_kpa = pressure_pa / 1000.0
		if pressure_kpa > 200.0:
			warnings.append("OVERPRESSURE: %0.1f kPa" % pressure_kpa)
	return warnings

# =============================================================================
# VERIFICATION TESTS
# =============================================================================

func verify_neutralization_constants() -> Dictionary:
	# HCl + NaOH -> NaCl + H2O
	var reactants = { "HCl_aq": 1.0, "NaOH_aq": 1.0 }
	var products = { "NaCl_aq": 1.0, "H2O": 1.0 }

	var delta_h = calculate_delta_h(reactants, products)
	var expected = -57.1  # kJ/mol
	var within_tolerance = abs(delta_h - expected) < 2.855  # 5%

	return {
		"calculated_delta_h_kj_mol": delta_h,
		"expected_delta_h_kj_mol": expected,
		"within_tolerance_5_percent": within_tolerance
	}

func verify_henderson_hasselbalch() -> bool:
	var ph = henderson_hasselbalch_ph(4.76, 0.1, 0.1)
	return abs(ph - 4.76) < 0.01

func verify_arrhenius() -> bool:
	var k1 = calculate_arrhenius_k(25.0, 50.0, 1e10)
	var k2 = calculate_arrhenius_k(50.0, 50.0, 1e10)
	return k2 > k1 * 2.0

func verify_precipitation() -> bool:
	return solubility_product_check(1e-4, 1e-4, 1e-10) == true

func verify_adiabatic_temp_rise() -> bool:
	var dt = calculate_adiabatic_temp_rise(-57.1, 0.1, 100.0, 4.184)
	return dt > 13.0 and dt < 14.5

func run_all_verifications() -> Dictionary:
	var results = {
		"neutralization": verify_neutralization_constants(),
		"henderson_hasselbalch": verify_henderson_hasselbalch(),
		"arrhenius": verify_arrhenius(),
		"precipitation": verify_precipitation(),
		"adiabatic_temp_rise": verify_adiabatic_temp_rise()
	}

	var all_passed = true
	for key in results:
		if typeof(results[key]) == TYPE_DICTIONARY:
			if not results[key].within_tolerance_5_percent:
				all_passed = false
		elif not results[key]:
			all_passed = false

	results["all_passed"] = all_passed
	return results