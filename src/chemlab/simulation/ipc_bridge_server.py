"""
ChemLab IPC Bridge Server — Connects Godot SimulationBridge to Python Scientific Engines.

This server runs as a persistent TCP socket listener (default port 8765) that accepts
JSON-RPC style commands from the Godot SimulationBridge and delegates to the
authoritative scientific simulation engines:

- AnalyticalEngine: NMR, GC-MS, HPLC, Melting Point, Balance, pH/Titration
- GeneticsEngine: PCR, Primer Design, Gel Electrophoresis, Restriction Digest, Sanger, CRISPR, qPCR
- NuclearEngine: 60+ Isotopes, Decay Chains, Reactor Physics, Reprocessing, Dosimetry

Protocol (per ARCHITECTURE.md §4.1):
- Each message is a newline-delimited JSON object
- Request:  {"request_id": "...", "command": "MIX_REAGENTS", "payload": {...}}
- Response: {"request_id": "...", "status": "SUCCESS", "data": {...}, "duration_ms": 1.2}
"""

import json
import logging
import socket
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class IPCRequest:
    request_id: str
    command: str
    payload: dict

    @classmethod
    def from_dict(cls, data: dict) -> "IPCRequest":
        return cls(
            request_id=data.get("request_id", ""),
            command=data.get("command", ""),
            payload=data.get("payload", {}),
        )


@dataclass
class IPCResponse:
    request_id: str
    status: str  # "SUCCESS", "EXECUTED", "ERROR"
    data: dict | None = None
    error: str | None = None
    duration_ms: float = 0.0

    def to_json(self) -> str:
        result = {
            "request_id": self.request_id,
            "status": self.status,
        }
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            result["error"] = self.error
        if self.duration_ms > 0:
            result["duration_ms"] = self.duration_ms
        return json.dumps(result) + "\n"


class CommandRegistry:
    """Registry of supported IPC commands with their handlers."""

    def __init__(self):
        self._handlers: dict[str, Callable[[dict], dict]] = {}

    def register(self, command: str, handler: Callable[[dict], dict]) -> None:
        self._handlers[command.upper()] = handler
        logger.info("Registered IPC command: %s", command)

    def has_command(self, command: str) -> bool:
        return command.upper() in self._handlers

    def execute(self, command: str, payload: dict) -> dict:
        handler = self._handlers.get(command.upper())
        if not handler:
            raise ValueError(f"Unknown command: {command}")
        return handler(payload)


class ScientificEngineBridge:
    """
    Bridge that routes commands to the appropriate scientific engine.

    This class encapsulates all three engines and provides a unified interface
    for the IPC server to interact with chemical simulation capabilities.
    """

    def __init__(self):
        self._analytical_engine = None
        self._genetics_engine = None
        self._nuclear_engine = None
        self._ai_computer = None
        self._initialized = False

    def _lazy_init(self):
        """Initialize engines on first use to avoid import overhead."""
        if self._initialized:
            return

        from chemlab.simulation.analytical_engine import AnalyticalEngine
        from chemlab.simulation.genetics_engine import GeneticsEngine
        from chemlab.simulation.nuclear_engine import NuclearEngine
        from chemlab.ai.reagent_computer import get_reagent_computer

        self._analytical_engine = AnalyticalEngine()
        self._genetics_engine = GeneticsEngine()
        self._nuclear_engine = NuclearEngine()
        self._ai_computer = get_reagent_computer()
        self._initialized = True
        logger.info("Scientific engines initialized")

    def _dataclass_to_dict(self, obj) -> dict:
        """Recursively convert dataclasses to dictionaries."""
        if obj is None:
            return None
        if hasattr(obj, "__dataclass_fields__"):
            result = {}
            for field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name)
                result[field_name] = self._dataclass_to_dict(value)
            return result
        elif isinstance(obj, list):
            return [self._dataclass_to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._dataclass_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        else:
            return str(obj)

    def _element_to_z(self, element: str) -> int:
        """Convert element symbol to atomic number."""
        element_map = {
            "H": 1,
            "HE": 2,
            "LI": 3,
            "BE": 4,
            "B": 5,
            "C": 6,
            "N": 7,
            "O": 8,
            "F": 9,
            "NE": 10,
            "NA": 11,
            "MG": 12,
            "AL": 13,
            "SI": 14,
            "P": 15,
            "S": 16,
            "CL": 17,
            "AR": 18,
            "K": 19,
            "CA": 20,
            "SC": 21,
            "TI": 22,
            "V": 23,
            "CR": 24,
            "MN": 25,
            "FE": 26,
            "CO": 27,
            "NI": 28,
            "CU": 29,
            "ZN": 30,
            "GA": 31,
            "GE": 32,
            "AS": 33,
            "SE": 34,
            "BR": 35,
            "KR": 36,
            "RB": 37,
            "SR": 38,
            "Y": 39,
            "ZR": 40,
            "NB": 41,
            "MO": 42,
            "TC": 43,
            "RU": 44,
            "RH": 45,
            "PD": 46,
            "AG": 47,
            "CD": 48,
            "IN": 49,
            "SN": 50,
            "SB": 51,
            "TE": 52,
            "I": 53,
            "XE": 54,
            "CS": 55,
            "BA": 56,
            "LA": 57,
            "CE": 58,
            "PR": 59,
            "ND": 60,
            "PM": 61,
            "SM": 62,
            "EU": 63,
            "GD": 64,
            "TB": 65,
            "DY": 66,
            "HO": 67,
            "ER": 68,
            "TM": 69,
            "YB": 70,
            "LU": 71,
            "HF": 72,
            "TA": 73,
            "W": 74,
            "RE": 75,
            "OS": 76,
            "IR": 77,
            "PT": 78,
            "AU": 79,
            "HG": 80,
            "TL": 81,
            "PB": 82,
            "BI": 83,
            "PO": 84,
            "AT": 85,
            "RN": 86,
            "FR": 87,
            "RA": 88,
            "AC": 89,
            "TH": 90,
            "PA": 91,
            "U": 92,
            "NP": 93,
            "PU": 94,
            "AM": 95,
            "CM": 96,
            "BK": 97,
            "CF": 98,
            "ES": 99,
            "FM": 100,
            "MD": 101,
            "NO": 102,
            "LR": 103,
            "RF": 104,
            "DB": 105,
            "SG": 106,
            "BH": 107,
            "HS": 108,
            "MT": 109,
            "DS": 110,
            "RG": 111,
            "CN": 112,
            "NH": 113,
            "FL": 114,
            "MC": 115,
            "LV": 116,
            "TS": 117,
            "OG": 118,
        }
        return element_map.get(element.upper(), 0)

    # -------------------------------------------------------------------------
    # Analytical Chemistry Commands
    # -------------------------------------------------------------------------

    def handle_nmr(self, payload: dict) -> dict:
        self._lazy_init()
        smiles = payload.get("smiles", "")
        nucleus = payload.get("nucleus", "1H")
        solvent = payload.get("solvent", "CDCl3")
        field_mhz = payload.get("field_mhz", 400.0)
        scans = payload.get("scans", 16)

        if not smiles:
            return {"error": "smiles parameter required"}

        try:
            if nucleus.upper() == "1H" or nucleus == "1":
                result = self._analytical_engine.run_nmr_1h(
                    smiles=smiles,
                    solvent=solvent,
                    scans=scans,
                )
            elif nucleus.upper() == "13C" or nucleus == "13":
                result = self._analytical_engine.run_nmr_13c(
                    smiles=smiles,
                    solvent=solvent,
                    scans=scans,
                )
            else:
                return {"error": f"Unsupported nucleus: {nucleus}. Use '1H' or '13C'"}

            # Convert dataclass to dict
            return {"spectrum": self._dataclass_to_dict(result)}
        except Exception as e:
            logger.exception("NMR simulation failed")
            return {"error": str(e)}

    def handle_gcms(self, payload: dict) -> dict:
        self._lazy_init()
        smiles = payload.get("smiles", "")
        column = payload.get("column", "DB-5MS")

        if not smiles:
            return {"error": "smiles parameter required"}

        try:
            result = self._analytical_engine.run_gc_ms(
                smiles=smiles,
                column=column,
            )
            return {"spectrum": self._dataclass_to_dict(result)}
        except Exception as e:
            logger.exception("GC-MS simulation failed")
            return {"error": str(e)}

    def handle_hplc(self, payload: dict) -> dict:
        self._lazy_init()
        smiles = payload.get("smiles", "")
        column = payload.get("column", "C18")
        wavelength = payload.get("wavelength", 254.0)

        if not smiles:
            return {"error": "smiles parameter required"}

        try:
            result = self._analytical_engine.run_hplc(
                smiles=smiles,
                column=column,
                wavelength=wavelength,
            )
            return {"chromatogram": self._dataclass_to_dict(result)}
        except Exception as e:
            logger.exception("HPLC simulation failed")
            return {"error": str(e)}

    def handle_melting_point(self, payload: dict) -> dict:
        self._lazy_init()
        smiles = payload.get("smiles", "")
        heating_rate = payload.get("heating_rate", 1.0)

        if not smiles:
            return {"error": "smiles parameter required"}

        try:
            result = self._analytical_engine.run_melting_point(
                smiles=smiles,
                heating_rate=heating_rate,
            )
            return {"melting_point": self._dataclass_to_dict(result)}
        except Exception as e:
            logger.exception("Melting point simulation failed")
            return {"error": str(e)}

    def handle_balance(self, payload: dict) -> dict:
        self._lazy_init()
        target_mass_g = payload.get("mass_g", 0.0)
        num_measurements = payload.get("num_measurements", 5)

        try:
            result = self._analytical_engine.run_balance(
                target_mass_g=target_mass_g,
                num_measurements=num_measurements,
            )
            return {"measurement": self._dataclass_to_dict(result)}
        except Exception as e:
            logger.exception("Balance simulation failed")
            return {"error": str(e)}

    def handle_ph_titration(self, payload: dict) -> dict:
        self._lazy_init()
        # Use the existing run_titration method
        acid_smiles = payload.get("acid_smiles", "")
        base_smiles = payload.get("base_smiles", "")
        acid_conc_m = payload.get("acid_conc_m", 0.1)
        base_conc_m = payload.get("base_conc_m", 0.1)
        acid_volume_ml = payload.get("acid_volume_ml", 25.0)
        indicator = payload.get("indicator", "phenolphthalein")

        if not acid_smiles or not base_smiles:
            return {"error": "acid_smiles and base_smiles required"}

        try:
            result = self._analytical_engine.run_titration(
                acid_smiles=acid_smiles,
                base_smiles=base_smiles,
                acid_conc_m=acid_conc_m,
                base_conc_m=base_conc_m,
                acid_volume_ml=acid_volume_ml,
                indicator=indicator,
            )
            return {"titration_curve": self._dataclass_to_dict(result)}
        except Exception as e:
            logger.exception("Titration simulation failed")
            return {"error": str(e)}

    # -------------------------------------------------------------------------
    # Genetics Commands
    # -------------------------------------------------------------------------

    def handle_pcr(self, payload: dict) -> dict:
        self._lazy_init()
        template = payload.get("template", "")
        forward_primer = payload.get("forward_primer", "")
        reverse_primer = payload.get("reverse_primer", "")
        cycles = payload.get("cycles", 30)
        annealing_temp_c = payload.get("annealing_temp_c", 60.0)

        if not template or not forward_primer or not reverse_primer:
            return {"error": "template, forward_primer, reverse_primer required"}

        try:
            # Create PCRProtocol object with PCRStep objects
            from chemlab.simulation.genetics_engine import PCRCycle, PCRProtocol, PCRStep

            cycle = PCRCycle(
                denaturation=PCRStep(
                    name="denaturation",
                    temperature_c=95.0,
                    hold_time_s=30,
                ),
                annealing=PCRStep(
                    name="annealing",
                    temperature_c=annealing_temp_c,
                    hold_time_s=30,
                ),
                extension=PCRStep(
                    name="extension",
                    temperature_c=72.0,
                    hold_time_s=60,
                ),
            )
            protocol = PCRProtocol(
                initial_denaturation=PCRStep(
                    name="initial_denaturation",
                    temperature_c=98.0,
                    hold_time_s=120,
                ),
                cycles=[cycle] * cycles,
                final_extension=PCRStep(
                    name="final_extension",
                    temperature_c=72.0,
                    hold_time_s=300,
                ),
                final_hold=PCRStep(
                    name="final_hold",
                    temperature_c=4.0,
                    hold_time_s=0,
                ),
            )
            result = self._genetics_engine.simulate_pcr(protocol)
            return {"amplicon": self._dataclass_to_dict(result)}
        except Exception as e:
            logger.exception("PCR simulation failed")
            return {"error": str(e)}

    def handle_primer_design(self, payload: dict) -> dict:
        self._lazy_init()
        target_sequence = payload.get("target_sequence", "")
        amplicon_size_bp = payload.get("amplicon_size_bp", 200)
        tm_min = payload.get("tm_min", 55.0)
        tm_max = payload.get("tm_max", 65.0)

        if not target_sequence:
            return {"error": "target_sequence required"}

        try:
            result = self._genetics_engine.design_primers(
                template=target_sequence,
                target_start=0,
                target_end=min(len(target_sequence), amplicon_size_bp),
            )
            return {"primers": self._dataclass_to_dict(result)}
        except Exception as e:
            logger.exception("Primer design failed")
            return {"error": str(e)}

    def handle_gel_electrophoresis(self, payload: dict) -> dict:
        self._lazy_init()
        samples = payload.get("samples", [])
        agarose_percent = payload.get("agarose_percent", 1.0)
        voltage_v = payload.get("voltage_v", 100.0)
        run_time_min = payload.get("run_time_min", 30.0)

        try:
            # Convert samples to fragment format
            fragments = []
            for s in samples:
                fragments.append(
                    {
                        "size_bp": s.get("size_bp", 1000),
                        "concentration_ng_ul": s.get("concentration", 10.0),
                        "label": s.get("label", "sample"),
                    }
                )
            result = self._genetics_engine.simulate_gel_electrophoresis(
                fragments=fragments,
                voltage_v=voltage_v,
                run_time_min=run_time_min,
            )
            return {"gel_image": self._dataclass_to_dict(result)}
        except Exception as e:
            logger.exception("Gel electrophoresis failed")
            return {"error": str(e)}

    def handle_restriction_digest(self, payload: dict) -> dict:
        self._lazy_init()
        dna_sequence = payload.get("dna_sequence", "")
        enzymes = payload.get("enzymes", [])

        if not dna_sequence:
            return {"error": "dna_sequence required"}

        try:
            result = self._genetics_engine.digest_dna(
                sequence=dna_sequence,
                enzymes=enzymes,
            )
            return {"fragments": self._dataclass_to_dict(result)}
        except Exception as e:
            logger.exception("Restriction digest failed")
            return {"error": str(e)}

    def handle_sanger_sequencing(self, payload: dict) -> dict:
        self._lazy_init()
        template = payload.get("template", "")
        primer = payload.get("primer", "")

        if not template or not primer:
            return {"error": "template and primer required"}

        try:
            result = self._genetics_engine.simulate_sanger_sequencing(
                template=template,
                primer=primer,
            )
            return {"sequence": self._dataclass_to_dict(result)}
        except Exception as e:
            logger.exception("Sanger sequencing failed")
            return {"error": str(e)}

    def handle_crispr(self, payload: dict) -> dict:
        self._lazy_init()
        target_sequence = payload.get("target_sequence", "")
        guide_rna = payload.get("guide_rna", "")
        cas_variant = payload.get("cas_variant", "SpCas9")

        if not target_sequence or not guide_rna:
            return {"error": "target_sequence and guide_rna required"}

        try:
            from chemlab.simulation.genetics_engine import SgRNA

            sg = SgRNA(
                target_sequence=target_sequence,
                pam_sequence="NGG",
                spacer=guide_rna,
                target_gene="",
                strand="+",
                efficiency_score=0.8,
                off_target_score=0.9,
            )
            result = self._genetics_engine.simulate_indels(sg, cell_type="HEK293")
            return {"edit_result": self._dataclass_to_dict(result)}
        except Exception as e:
            logger.exception("CRISPR simulation failed")
            return {"error": str(e)}

    def handle_qpcr(self, payload: dict) -> dict:
        self._lazy_init()
        template = payload.get("template", "")
        forward_primer = payload.get("forward_primer", "")
        reverse_primer = payload.get("reverse_primer", "")
        probe = payload.get("probe", "")

        if not template or not forward_primer or not reverse_primer:
            return {"error": "template, forward_primer, reverse_primer required"}

        try:
            result = self._genetics_engine.simulate_qpcr(
                initial_copies=1000,
                efficiency=0.9,
            )
            return {"amplification_curve": self._dataclass_to_dict(result)}
        except Exception as e:
            logger.exception("qPCR simulation failed")
            return {"error": str(e)}

    # -------------------------------------------------------------------------
    # Nuclear Physics Commands
    # -------------------------------------------------------------------------

    def handle_decay_chain(self, payload: dict) -> dict:
        self._lazy_init()
        isotope = payload.get("isotope", "")
        initial_atoms = payload.get("initial_atoms", 1e12)
        time_seconds = payload.get("time_seconds", 3600.0)

        if not isotope:
            return {"error": "isotope parameter required"}

        try:
            # Parse isotope symbol (e.g., "U-238")
            if "-" not in isotope:
                return {"error": "isotope must be in format 'U-238'"}
            element, mass_str = isotope.split("-")
            z = self._element_to_z(element)
            a = int(mass_str)

            parent = self._nuclear_engine.get_isotope(z, a)
            if not parent:
                return {"error": f"Unknown isotope: {isotope}"}

            result = self._nuclear_engine.decay_chain_activity(
                parent=parent,
                initial_atoms=initial_atoms,
                time_seconds=time_seconds,
            )
            return {"decay_chain": result}
        except Exception as e:
            logger.exception("Decay chain simulation failed")
            return {"error": str(e)}

    def handle_reactor_physics(self, payload: dict) -> dict:
        self._lazy_init()
        fuel_enrichment = payload.get("fuel_enrichment", 0.04)
        burnup_gwd_mtu = payload.get("burnup_gwd_mtu", 0.0)
        power_mw = payload.get("power_mw", 3000.0)
        coolant_temp_c = payload.get("coolant_temp_c", 300.0)

        try:
            from chemlab.simulation.nuclear_engine import FuelAssembly

            fuel = FuelAssembly(
                enrichment=fuel_enrichment,
                mass_kg=10000.0,
                burnup_gwd_mtu=burnup_gwd_mtu,
            )
            k_eff = self._nuclear_engine.reactor_criticality(fuel)

            # Get equilibrium values
            xe135 = self._nuclear_engine.xenon_135_equilibrium(
                flux_n_cm2_s=1e14,
                power_mw=power_mw,
            )
            sm149 = self._nuclear_engine.samarium_149_equilibrium(
                flux_n_cm2_s=1e14,
            )

            return {
                "reactor_state": {
                    "k_eff": k_eff,
                    "xenon_135_ppm": xe135,
                    "samarium_149_ppm": sm149,
                    "power_mw": power_mw,
                    "coolant_temp_c": coolant_temp_c,
                }
            }
        except Exception as e:
            logger.exception("Reactor physics simulation failed")
            return {"error": str(e)}

    def handle_gamma_spectrum(self, payload: dict) -> dict:
        self._lazy_init()
        isotopes = payload.get("isotopes", [])
        measurement_time_s = payload.get("measurement_time_s", 3600.0)
        detector_type = payload.get("detector_type", "HPGe")

        try:
            # Use the existing dose rate calculation as a proxy
            spectrum = {}
            for iso_str in isotopes:
                if "-" in iso_str:
                    element, mass_str = iso_str.split("-")
                    z = self._element_to_z(element)
                    a = int(mass_str)
                    iso = self._nuclear_engine.get_isotope(z, a)
                    if iso:
                        # Get decay energies for gamma spectrum
                        for mode, energy in iso.decay_energies.items():
                            if mode in ["gamma", "beta+"]:
                                spectrum[energy] = iso.half_life_s
            return {"spectrum": spectrum}
        except Exception as e:
            logger.exception("Gamma spectrum simulation failed")
            return {"error": str(e)}

    def handle_dosimetry(self, payload: dict) -> dict:
        self._lazy_init()
        source_isotope = payload.get("source_isotope", "")
        activity_bq = payload.get("activity_bq", 1e6)
        distance_m = payload.get("distance_m", 1.0)
        shielding = payload.get("shielding", "none")
        exposure_time_h = payload.get("exposure_time_h", 1.0)

        if not source_isotope:
            return {"error": "source_isotope required"}

        try:
            if "-" not in source_isotope:
                return {"error": "isotope must be in format 'Cs-137'"}
            element, mass_str = source_isotope.split("-")
            z = self._element_to_z(element)
            a = int(mass_str)
            iso = self._nuclear_engine.get_isotope(z, a)
            if not iso:
                return {"error": f"Unknown isotope: {source_isotope}"}

            # Use geiger_muller_count_rate as proxy for dose calculation
            count_rate = self._nuclear_engine.geiger_muller_count_rate(
                activity_bq=activity_bq,
                distance_cm=distance_m * 100,
                efficiency=0.1,
                window_thickness_mg_cm2=20.0,
            )

            # Convert to approximate dose rate (very rough)
            dose_rate_usv_h = count_rate * 0.01  # rough conversion

            return {
                "dose": {
                    "source": source_isotope,
                    "activity_bq": activity_bq,
                    "distance_m": distance_m,
                    "dose_rate_usv_h": dose_rate_usv_h,
                    "total_dose_usv": dose_rate_usv_h * exposure_time_h,
                    "shielding": shielding,
                }
            }
        except Exception as e:
            logger.exception("Dosimetry calculation failed")
            return {"error": str(e)}

    def handle_reprocessing(self, payload: dict) -> dict:
        self._lazy_init()
        spent_fuel = payload.get("spent_fuel", {})
        process_type = payload.get("process_type", "PUREX")

        try:
            from chemlab.simulation.nuclear_engine import FuelAssembly

            # Create a default spent fuel assembly
            fuel = FuelAssembly(
                enrichment=spent_fuel.get("enrichment", 0.04),
                mass_kg=spent_fuel.get("mass_kg", 1000.0),
                burnup_gwd_mtu=spent_fuel.get("burnup_gwd_mtu", 45.0),
            )
            result = self._nuclear_engine.reprocess_fuel(fuel)
            return {"products": result}
        except Exception as e:
            logger.exception("Reprocessing simulation failed")
            return {"error": str(e)}

    # -------------------------------------------------------------------------
    # AI Reagent Computer Commands
    # -------------------------------------------------------------------------

    def handle_ai_compute_reaction(self, payload: dict) -> dict:
        """
        Handle AI_COMPUTE_REACTION command.
        Uses AIReagentComputer with multi-provider fallback (Ollama, LM Studio, Groq, Gemini, NIM, Local).
        """
        self._lazy_init()
        from chemlab.ai.reagent_computer import ReagentComputationRequest

        req = ReagentComputationRequest(
            reagents=payload.get("reagents", []),
            temperature_c=float(payload.get("temperature_c", 22.0)),
            pressure_atm=float(payload.get("pressure_atm", 1.0)),
            volume_ml=float(payload.get("volume_ml", 100.0)),
            catalysts=payload.get("catalysts", []),
            target_compound=payload.get("target_compound"),
            reaction_type=payload.get("reaction_type"),
            time_dilation=float(payload.get("time_dilation", 1.0)),
        )

        result = self._ai_computer.compute_reaction(req)
        resp = {
            "success": result.success,
            "provider_used": result.provider_used,
            "latency_ms": result.latency_ms,
            "fallback_used": result.fallback_used,
            "error_message": result.error_message,
        }
        if result.prediction:
            pred = result.prediction
            resp["prediction"] = {
                "reaction_name": pred.reaction_name,
                "balanced_equation": pred.balanced_equation,
                "products": pred.products,
                "enthalpy_kj_mol": pred.enthalpy_kj_mol,
                "activation_energy_kj_mol": pred.activation_energy_kj_mol,
                "rate_constant_k": pred.rate_constant_k,
                "target_color_rgb": list(pred.target_color_rgb),
                "produces_gas": pred.produces_gas,
                "precipitate_formed": pred.precipitate_formed,
                "emission_glow": pred.emission_glow,
                "safety_warnings": pred.safety_warnings,
            }
        return resp

    def handle_ai_register_provider(self, payload: dict) -> dict:
        """
        Handle AI_REGISTER_PROVIDER command to configure local AI or free cloud providers.
        """
        self._lazy_init()
        name = payload.get("name", "local_ai")
        endpoint = payload.get("endpoint", "http://127.0.0.1:11434/v1")
        model = payload.get("model", "llama3.2")
        priority = int(payload.get("priority", 1))
        api_key = payload.get("api_key")

        self._ai_computer.add_provider(name, priority, endpoint, api_key, model)
        return {
            "status": "registered",
            "provider": name,
            "endpoint": endpoint,
            "model": model,
            "priority": priority,
        }

    def handle_ai_get_providers(self, payload: dict) -> dict:
        """
        Handle AI_GET_PROVIDERS command.
        """
        self._lazy_init()
        return {
            "providers": self._ai_computer.get_provider_status(),
            "provider_order": self._ai_computer.provider_order,
        }

    # -------------------------------------------------------------------------
    # Unified Commands (matching Godot SimulationBridge contract)
    # -------------------------------------------------------------------------

    def handle_mix_reagents(self, payload: dict) -> dict:
        """
        Handle MIX_REAGENTS command per ARCHITECTURE.md §4.1 contract.

        Payload:
            vessel_id: str
            reagents: list of {id: str, moles: float}
            catalyst: str
            temperature_c: float
            addition_order_correct: bool
            in_fume_hood: bool

        Response:
            vessel_id, reaction_name, conversion_ratio, temperature_c,
            is_exothermic, delta_h_kj_mol, color_rgba, turbidity,
            precipitate_formed, precipitate_name, bubbles_per_second,
            side_products, safety_warnings
        """
        self._lazy_init()

        vessel_id = payload.get("vessel_id", "default")
        reagents = payload.get("reagents", [])
        catalyst = payload.get("catalyst", "")
        temperature_c = payload.get("temperature_c", 22.0)
        addition_order_correct = payload.get("addition_order_correct", True)
        in_fume_hood = payload.get("in_fume_hood", True)

        # Validate reagents
        for r in reagents:
            if "id" not in r or "moles" not in r:
                return {"error": "Each reagent must have 'id' and 'moles'"}

        try:
            # Determine primary reaction type from reagents
            result = self._analyze_mixture(reagents, catalyst, temperature_c)

            return {
                "vessel_id": vessel_id,
                "reaction_name": result.get("reaction_name", "Mixing"),
                "conversion_ratio": result.get("conversion_ratio", 0.0),
                "temperature_c": result.get("temperature_c", temperature_c),
                "is_exothermic": result.get("is_exothermic", False),
                "delta_h_kj_mol": result.get("delta_h_kj_mol", 0.0),
                "color_rgba": result.get("color_rgba", [1.0, 1.0, 1.0, 1.0]),
                "turbidity": result.get("turbidity", 0.0),
                "precipitate_formed": result.get("precipitate_formed", False),
                "precipitate_name": result.get("precipitate_name", ""),
                "bubbles_per_second": result.get("bubbles_per_second", 0.0),
                "side_products": result.get("side_products", []),
                "safety_warnings": result.get("safety_warnings", []),
            }
        except Exception as e:
            logger.exception("Mix reagents failed")
            return {"error": str(e)}

    def _analyze_mixture(self, reagents: list, catalyst: str, temp_c: float) -> dict:
        """Analyze a mixture and determine reaction outcomes."""
        # Extract species IDs
        species_ids = [r["id"] for r in reagents]
        species_moles = {r["id"]: r["moles"] for r in reagents}

        result = {
            "reaction_name": "Mixing",
            "conversion_ratio": 0.0,
            "temperature_c": temp_c,
            "is_exothermic": False,
            "delta_h_kj_mol": 0.0,
            "color_rgba": [1.0, 1.0, 1.0, 1.0],
            "turbidity": 0.0,
            "precipitate_formed": False,
            "precipitate_name": "",
            "bubbles_per_second": 0.0,
            "side_products": [],
            "safety_warnings": [],
        }

        # Check for known reaction patterns
        has_hcl = "HCl_aq" in species_ids or "hcl" in species_ids
        has_naoh = "NaOH_aq" in species_ids or "naoh" in species_ids
        has_h2o2 = "H2O2_aq" in species_ids or "h2o2" in species_ids
        has_ki = "KI_aq" in species_ids or "ki" in species_ids
        has_fe3 = "Fe3+" in species_ids or "fecl3" in species_ids

        # Acid-base neutralization
        if has_hcl and has_naoh:
            hcl_moles = species_moles.get("HCl_aq", species_moles.get("hcl", 0))
            naoh_moles = species_moles.get("NaOH_aq", species_moles.get("naoh", 0))
            reacted = min(hcl_moles, naoh_moles)

            if reacted > 0:
                result["reaction_name"] = "HCl + NaOH Neutralization"
                result["conversion_ratio"] = reacted / max(hcl_moles, naoh_moles)
                result["is_exothermic"] = True
                result["delta_h_kj_mol"] = -57.1
                result["color_rgba"] = [1.0, 1.0, 1.0, 0.0]  # Colorless

                # Calculate temperature rise
                # Assume total volume ~ 100 mL = 100 g for dilute aqueous solutions
                total_volume_ml = 100.0
                total_mass_g = total_volume_ml * 1.0  # water density ~ 1 g/mL
                heat_j = reacted * 57100  # J
                delta_t = heat_j / (total_mass_g * 4.184)
                result["temperature_c"] = temp_c + delta_t

                if result["temperature_c"] > 80:
                    result["safety_warnings"].append(
                        f"Temperature {result['temperature_c']:.1f}°C exceeds safe handling limit"
                    )

        # Elephant toothpaste (H2O2 + KI)
        if has_h2o2 and has_ki:
            h2o2_moles = species_moles.get("H2O2_aq", species_moles.get("h2o2", 0))
            ki_moles = species_moles.get("KI_aq", species_moles.get("ki", 0))

            if h2o2_moles > 0 and ki_moles > 0:
                result["reaction_name"] = "Catalytic H2O2 Decomposition (Elephant Toothpaste)"
                result["conversion_ratio"] = 0.9  # Fast and near-complete
                result["is_exothermic"] = True
                result["delta_h_kj_mol"] = -98.0
                result["bubbles_per_second"] = 50.0
                result["color_rgba"] = [0.9, 0.9, 0.95, 1.0]
                result["side_products"].append("O2_gas")

                # Temperature rise - assume 100 mL total volume
                total_volume_ml = 100.0
                total_mass_g = total_volume_ml * 1.0
                heat_j = h2o2_moles * 98000
                delta_t = heat_j / (total_mass_g * 4.184)
                result["temperature_c"] = temp_c + delta_t

                if result["temperature_c"] > 60:
                    result["safety_warnings"].append(
                        f"Rapid gas evolution and temperature {result['temperature_c']:.1f}°C - splash hazard"
                    )

        # Briggs-Rauscher check
        has_ma = "malonic_acid" in species_ids
        has_kio3 = "KIO3" in species_ids or "kio3" in species_ids
        has_mn = "manganese_sulfate" in species_ids

        if has_h2o2 and has_kio3 and has_ma and has_mn:
            result["reaction_name"] = "Briggs-Rauscher Oscillating Reaction"
            result["is_exothermic"] = False
            result["color_rgba"] = [0.95, 0.98, 1.0, 1.0]  # Clear start
            result["side_products"] = ["oscillation_phase"]

        # Precipitation check
        if "Ag+" in species_ids and "Cl-" in species_ids:
            ag_moles = species_moles.get("Ag+", 0)
            cl_moles = species_moles.get("Cl-", 0)
            if ag_moles > 0 and cl_moles > 0:
                result["precipitate_formed"] = True
                result["precipitate_name"] = "Silver Chloride"
                result["turbidity"] = 0.5
                result["color_rgba"] = [0.9, 0.9, 0.9, 1.0]
                result["safety_warnings"].append("Precipitate formed: AgCl (environmental hazard)")

        return result

    def handle_step_simulation(self, payload: dict) -> dict:
        """
        Handle STEP_SIMULATION command.

        Payload:
            vessel_id: str
            dt: float (time step in seconds)

        Response:
            vessel state, reactions, temperature_change, ph_change
        """
        self._lazy_init()
        vessel_id = payload.get("vessel_id", "default")
        dt = payload.get("dt", 0.1)

        # This would normally maintain vessel state across steps
        # For now, return a minimal valid response
        return {
            "vessel": {
                "vessel_id": vessel_id,
                "volume_ml": 100.0,
                "temperature_c": 22.0,
                "ph": 7.0,
                "species_moles": {"H2O": 5.55},
                "color_rgba": [1.0, 1.0, 1.0, 1.0],
                "turbidity": 0.0,
                "bubble_rate": 0.0,
            },
            "reactions": [],
            "temperature_change": 0.0,
            "ph_change": 0.0,
        }

    def handle_calculate_thermodynamics(self, payload: dict) -> dict:
        """Handle CALCULATE_THERMODYNAMICS command via Cantera engine."""
        self._lazy_init()
        reactants = payload.get("reactants", {})
        products = payload.get("products", {})
        temperature_c = payload.get("temperature_c", 25.0)

        try:
            # Use the analytical engine's Cantera integration
            result = self._analytical_engine.query_cantera(
                reactants=reactants,
                products=products,
                temperature_c=temperature_c,
            )
            return result
        except Exception as e:
            logger.exception("Cantera query failed")
            return {"error": str(e)}

    def handle_rdkit_conformer(self, payload: dict) -> dict:
        """Handle RDKIT_CONFORMER command."""
        self._lazy_init()
        smiles = payload.get("smiles", "")
        compound_name = payload.get("compound_name", "")

        if not smiles:
            return {"error": "smiles parameter required"}

        try:
            result = self._analytical_engine.query_rdkit(
                smiles=smiles,
                compound_name=compound_name,
            )
            return result
        except Exception as e:
            logger.exception("RDKit query failed")
            return {"error": str(e)}

    def handle_handshake(self, payload: dict) -> dict:
        """Handle HANDSHAKE command."""
        client = payload.get("client", "unknown")
        version = payload.get("version", "1.0")
        logger.info("Handshake from %s v%s", client, version)

        return {
            "status": "connected",
            "server": "chemlab_ipc_bridge",
            "version": "1.0",
            "engines": {
                "analytical": True,
                "genetics": True,
                "nuclear": True,
            },
            "supported_commands": [
                "MIX_REAGENTS",
                "STEP_SIMULATION",
                "CALCULATE_THERMODYNAMICS",
                "RDKIT_CONFORMER",
                "NMR",
                "GCMS",
                "HPLC",
                "MELTING_POINT",
                "BALANCE",
                "PH_TITRATION",
                "PCR",
                "PRIMER_DESIGN",
                "GEL_ELECTROPHORESIS",
                "RESTRICTION_DIGEST",
                "SANGER_SEQUENCING",
                "CRISPR",
                "QPCR",
                "DECAY_CHAIN",
                "REACTOR_PHYSICS",
                "GAMMA_SPECTRUM",
                "DOSIMETRY",
                "REPROCESSING",
                "AI_COMPUTE_REACTION",
                "AI_REGISTER_PROVIDER",
                "AI_GET_PROVIDERS",
            ],
        }


class ThreadedIPCServer:
    """
    Threaded TCP IPC Server for Godot SimulationBridge communication.

    Features:
    - Clean shutdown via threading.Event
    - Per-client timeout handling
    - JSON-RPC style message format (newline-delimited)
    - Automatic reconnection handling
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8765,
        buffer_size: int = 8192,
        command_timeout_seconds: float = 10.0,
        max_connections: int = 5,
    ):
        self._host = host
        self._port = port
        self._buffer_size = buffer_size
        self._command_timeout = command_timeout_seconds
        self._max_connections = max_connections

        self._shutdown_event = threading.Event()
        self._server_socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        # Initialize command registry and engine bridge
        self._registry = CommandRegistry()
        self._bridge = ScientificEngineBridge()
        self._register_commands()

    def _register_commands(self):
        """Register all supported IPC commands."""
        # Handshake
        self._registry.register("HANDSHAKE", self._bridge.handle_handshake)

        # Unified simulation commands
        self._registry.register("MIX_REAGENTS", self._bridge.handle_mix_reagents)
        self._registry.register("STEP_SIMULATION", self._bridge.handle_step_simulation)
        self._registry.register(
            "CALCULATE_THERMODYNAMICS", self._bridge.handle_calculate_thermodynamics
        )
        self._registry.register("RDKIT_CONFORMER", self._bridge.handle_rdkit_conformer)

        # Analytical chemistry
        self._registry.register("NMR", self._bridge.handle_nmr)
        self._registry.register("NMR_ANALYSIS", self._bridge.handle_nmr)
        self._registry.register("GCMS", self._bridge.handle_gcms)
        self._registry.register("HPLC", self._bridge.handle_hplc)
        self._registry.register("MELTING_POINT", self._bridge.handle_melting_point)
        self._registry.register("BALANCE", self._bridge.handle_balance)
        self._registry.register("PH_TITRATION", self._bridge.handle_ph_titration)

        # Genetics
        self._registry.register("PCR", self._bridge.handle_pcr)
        self._registry.register("PRIMER_DESIGN", self._bridge.handle_primer_design)
        self._registry.register("GEL_ELECTROPHORESIS", self._bridge.handle_gel_electrophoresis)
        self._registry.register("RESTRICTION_DIGEST", self._bridge.handle_restriction_digest)
        self._registry.register("SANGER_SEQUENCING", self._bridge.handle_sanger_sequencing)
        self._registry.register("CRISPR", self._bridge.handle_crispr)
        self._registry.register("QPCR", self._bridge.handle_qpcr)

        # Nuclear physics
        self._registry.register("DECAY_CHAIN", self._bridge.handle_decay_chain)
        self._registry.register("REACTOR_PHYSICS", self._bridge.handle_reactor_physics)
        self._registry.register("GAMMA_SPECTRUM", self._bridge.handle_gamma_spectrum)
        self._registry.register("DOSIMETRY", self._bridge.handle_dosimetry)
        self._registry.register("REPROCESSING", self._bridge.handle_reprocessing)

        # AI reaction computing
        self._registry.register("AI_COMPUTE_REACTION", self._bridge.handle_ai_compute_reaction)
        self._registry.register("AI_REGISTER_PROVIDER", self._bridge.handle_ai_register_provider)
        self._registry.register("AI_GET_PROVIDERS", self._bridge.handle_ai_get_providers)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    @property
    def is_running(self) -> bool:
        return not self._shutdown_event.is_set() and self._server_socket is not None

    def start(self):
        """Bind socket and start background listening thread."""
        with self._lock:
            if self.is_running:
                logger.warning("IPC Server is already running")
                return

            self._shutdown_event.clear()

            try:
                self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self._server_socket.bind((self._host, self._port))
                self._server_socket.listen(self._max_connections)
                self._server_socket.settimeout(0.5)

                self._thread = threading.Thread(
                    target=self._accept_loop,
                    name="ChemLab-IPC-ServerThread",
                    daemon=True,
                )
                self._thread.start()
                logger.info("IPC Bridge Server listening on %s:%s", self._host, self._port)

            except OSError as exc:
                if self._server_socket:
                    self._server_socket.close()
                    self._server_socket = None
                raise RuntimeError(
                    f"Failed to bind socket on {self._host}:{self._port}: {exc}"
                ) from exc

    def _accept_loop(self):
        """Main listening loop polling for connections."""
        while not self._shutdown_event.is_set():
            if not self._server_socket:
                break
            try:
                client_sock, client_addr = self._server_socket.accept()
                logger.debug("Godot client connected from %s", client_addr)
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, client_addr),
                    name=f"ChemLab-IPC-Client-{client_addr}",
                    daemon=True,
                )
                client_thread.start()
            except TimeoutError:
                continue
            except OSError:
                break

    def _handle_client(self, client_sock: socket.socket, client_addr: tuple):
        """Process incoming client messages."""
        client_sock.settimeout(self._command_timeout)
        buffer = ""

        try:
            while not self._shutdown_event.is_set():
                chunk = client_sock.recv(self._buffer_size)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8")

                # Process complete newline-delimited messages
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        request_data = json.loads(line)
                        request = IPCRequest.from_dict(request_data)

                        start_time = time.perf_counter()

                        if self._registry.has_command(request.command):
                            response_data = self._registry.execute(request.command, request.payload)
                            duration_ms = (time.perf_counter() - start_time) * 1000.0
                            response = IPCResponse(
                                request_id=request.request_id,
                                status="SUCCESS",
                                data=response_data,
                                duration_ms=duration_ms,
                            )
                        else:
                            response = IPCResponse(
                                request_id=request.request_id,
                                status="ERROR",
                                error=f"Unknown command: {request.command}",
                                duration_ms=(time.perf_counter() - start_time) * 1000.0,
                            )

                    except json.JSONDecodeError as e:
                        response = IPCResponse(
                            request_id="",
                            status="ERROR",
                            error=f"Invalid JSON: {e}",
                        )
                    except Exception as e:
                        logger.exception("Error processing request")
                        response = IPCResponse(
                            request_id=request_data.get("request_id", "")
                            if isinstance(request_data, dict)
                            else "",
                            status="ERROR",
                            error=str(e),
                        )

                    try:
                        client_sock.sendall(response.to_json().encode("utf-8"))
                    except OSError:
                        break

        except TimeoutError:
            logger.debug("Client %s timeout", client_addr)
        except OSError:
            pass
        finally:
            client_sock.close()
            logger.debug("Client %s disconnected", client_addr)

    def stop(self):
        """Cleanly shutdown the server."""
        with self._lock:
            self._shutdown_event.set()
            if self._server_socket:
                try:
                    self._server_socket.close()
                except OSError:
                    pass
                self._server_socket = None

            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=2.0)
                self._thread = None
            logger.info("IPC Bridge Server stopped")


def run_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    command_timeout: float = 10.0,
):
    """Run the IPC bridge server until interrupted."""
    server = ThreadedIPCServer(
        host=host,
        port=port,
        command_timeout_seconds=command_timeout,
    )

    print(f"Starting ChemLab IPC Bridge Server on {host}:{port}")
    print("Press Ctrl+C to stop")

    try:
        server.start()
        # Keep main thread alive
        while server.is_running:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.stop()


if __name__ == "__main__":
    import sys

    host = "127.0.0.1"
    port = 8765

    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])

    run_server(host=host, port=port)
