"""
ChemLab Native Desktop Application (PySide6 / Qt6).
Cross-platform native GUI for Windows & Linux:
  • Standalone operation without web dependencies or browser runtimes
  • Direct integration with Cantera Thermodynamics & RDKit Cheminformatics
  • Real-time Socket IPC Bridge to Blender 3D Engine (Port 9876)
  • Worldwide Laboratory Archetypes & Hazard Level Explorer
  • Interactive Reaction Kinetics & Titration Curve Visualizer
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from chemlab.simulation.cantera_engine import THERMO_ENGINE
from chemlab.simulation.rdkit_engine import RDKIT_ENGINE
from chemlab.world.lab_taxonomy import LAB_REGISTRY

logger = logging.getLogger("chemlab.desktop")


# Dark High-Tech Cleanroom QSS Stylesheet
CLEANROOM_STYLESHEET = """
QMainWindow {
    background-color: #0f141c;
    color: #e2e8f0;
}
QTabWidget::pane {
    border: 1px solid #1e293b;
    background-color: #0f141c;
}
QTabBar::tab {
    background: #182232;
    color: #94a3b8;
    padding: 10px 20px;
    font-weight: 600;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #0284c7;
    color: #ffffff;
}
QGroupBox {
    border: 1px solid #243447;
    border-radius: 6px;
    margin-top: 1.2em;
    padding: 15px;
    font-weight: bold;
    color: #38bdf8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
}
QPushButton {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: 600;
    padding: 8px 16px;
    border-radius: 5px;
    border: none;
}
QPushButton:hover {
    background-color: #0369a1;
}
QPushButton:pressed {
    background-color: #075985;
}
QPushButton#SecondaryBtn {
    background-color: #1e293b;
    color: #cbd5e1;
    border: 1px solid #334155;
}
QPushButton#SecondaryBtn:hover {
    background-color: #334155;
}
QLineEdit, QComboBox, QTextEdit {
    background-color: #182232;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 6px;
    color: #f8fafc;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border: 1px solid #0284c7;
}
QTableWidget {
    background-color: #131b26;
    border: 1px solid #1e293b;
    gridline-color: #243447;
    color: #e2e8f0;
}
QHeaderView::section {
    background-color: #1e293b;
    color: #38bdf8;
    padding: 6px;
    font-weight: bold;
    border: 1px solid #0f172a;
}
"""


class TitrationCanvasWidget(QWidget):
    """Custom paint widget rendering real mathematical titration curves."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.curve_points: list[tuple[float, float]] = []
        self.setMinimumHeight(220)

    def set_data(self, points: list[tuple[float, float]]) -> None:
        self.curve_points = points
        self.update()

    def paintEvent(self, event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        margin = 35

        # Background
        painter.fillRect(0, 0, w, h, QColor("#131b26"))

        # Grid lines
        painter.setPen(QPen(QColor("#243447"), 1, Qt.DashLine))
        for ph in [0, 4, 7, 10, 14]:
            y = h - margin - (ph / 14.0) * (h - 2 * margin)
            painter.drawLine(margin, int(y), w - margin, int(y))
            painter.setPen(QColor("#64748b"))
            painter.drawText(5, int(y + 4), f"{ph:2d}")
            painter.setPen(QPen(QColor("#243447"), 1, Qt.DashLine))

        if not self.curve_points:
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(self.rect(), Qt.AlignCenter, "Keine Titrationsdaten geladen.")
            return

        max_v = max(p[0] for p in self.curve_points) or 50.0

        # Draw curve line
        painter.setPen(QPen(QColor("#38bdf8"), 2))
        qpoints = []
        for v, ph in self.curve_points:
            x = margin + (v / max_v) * (w - 2 * margin)
            y = h - margin - (ph / 14.0) * (h - 2 * margin)
            qpoints.append(QPointF(x, y))

        for i in range(len(qpoints) - 1):
            painter.drawLine(qpoints[i], qpoints[i + 1])

        # Axis label
        painter.setPen(QColor("#e2e8f0"))
        painter.drawText(w - 75, h - 8, "V(mL) Titrant")
        painter.drawText(10, 20, "pH-Wert")


class ChemLabMainWindow(QMainWindow):
    """Main desktop application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ChemLab — Native Virtual Chemistry Platform [Windows / Linux]")
        self.resize(1280, 800)
        self.setStyleSheet(CLEANROOM_STYLESHEET)

        self._init_ui()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Header Title Bar
        header = QFrame(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 8)

        app_title = QLabel("🔬 CHEMLAB STUDIO — NATIVE LABORATORY ENGINE", self)
        app_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        app_title.setStyleSheet("color: #38bdf8;")
        header_layout.addWidget(app_title)

        header_layout.addStretch()

        self.lbl_engine_status = QLabel("● Blender IPC Bridge: 127.0.0.1:9876 [Offline]", self)
        self.lbl_engine_status.setStyleSheet("color: #f43f5e; font-weight: bold;")
        header_layout.addWidget(self.lbl_engine_status)

        main_layout.addWidget(header)

        # Tabbed Workspaces
        tabs = QTabWidget(self)
        tabs.addTab(self._create_world_lab_tab(), "🌐 Weltweite Laboratorien")
        tabs.addTab(self._create_thermo_calculator_tab(), "⚡ Kinetik & Thermodynamik (Cantera)")
        tabs.addTab(self._create_rdkit_tab(), "🧬 Molekül-Struktur & 3D (RDKit)")
        tabs.addTab(self._create_blender_bridge_tab(), "🖥️ Blender 3D Live-Bridge")

        main_layout.addWidget(tabs)

    # -------------------------------------------------------------------------
    # TAB 1: World Laboratories
    # -------------------------------------------------------------------------
    def _create_world_lab_tab(self) -> QWidget:
        widget = QWidget(self)
        layout = QHBoxLayout(widget)

        splitter = QSplitter(Qt.Horizontal, self)

        # Left list of archetypes
        left_panel = QFrame(self)
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("<b>Verfügbare Labor-Archetypen:</b>"))

        self.lab_combo = QComboBox(self)
        for lab in LAB_REGISTRY.list_all_archetypes():
            self.lab_combo.addItem(f"{lab.title}", lab.archetype_id)
        self.lab_combo.currentIndexChanged.connect(self._on_lab_selected)
        left_layout.addWidget(self.lab_combo)

        self.txt_lab_details = QTextEdit(self)
        self.txt_lab_details.setReadOnly(True)
        left_layout.addWidget(self.txt_lab_details)

        splitter.addWidget(left_panel)

        # Right equipment & safety table
        right_panel = QFrame(self)
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("<b>Vorhandene Geräte & Reagenzien-Inventar:</b>"))

        self.table_equipment = QTableWidget(self)
        self.table_equipment.setColumnCount(3)
        self.table_equipment.setHorizontalHeaderLabels(["Gerätename", "Kategorie", "Leistung (W)"])
        self.table_equipment.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_layout.addWidget(self.table_equipment)

        splitter.addWidget(right_panel)
        splitter.setSizes([450, 750])

        layout.addWidget(splitter)
        self._on_lab_selected(0)
        return widget

    def _on_lab_selected(self, index: int) -> None:
        lab_id = self.lab_combo.currentData()
        if not lab_id:
            return
        lab = LAB_REGISTRY.get_archetype(lab_id)
        if not lab:
            return

        detail_text = (
            f"<h2>{lab.title}</h2>"
            f"<p><b>Beschreibung:</b> {lab.short_description}</p>"
            f"<p><b>Sicherheitsstufe:</b> <span style='color:#f59e0b;'>{lab.containment_level}</span></p>"
            f"<p><b>Lüftung:</b> {lab.ventilation_type}</p>"
            f"<p><b>Abmessungen:</b> {lab.dimensions_meters[0]}m × {lab.dimensions_meters[1]}m × {lab.dimensions_meters[2]}m</p>"
            f"<p><b>Kontext:</b> {lab.narrative_context}</p>"
            f"<p><b>Gefahrenprofil:</b><br>• " + "<br>• ".join(lab.hazard_profile) + "</p>"
            "<p><b>Verfügbare Reagenzien:</b><br>" + ", ".join(lab.reagent_palette) + "</p>"
        )
        self.txt_lab_details.setHtml(detail_text)

        # Populate equipment table
        self.table_equipment.setRowCount(len(lab.key_equipment))
        for row, eq in enumerate(lab.key_equipment):
            self.table_equipment.setItem(row, 0, QTableWidgetItem(eq.name))
            self.table_equipment.setItem(row, 1, QTableWidgetItem(eq.category.value))
            self.table_equipment.setItem(row, 2, QTableWidgetItem(f"{eq.power_watts:.0f} W"))

    # -------------------------------------------------------------------------
    # TAB 2: Cantera Thermodynamics & Titration
    # -------------------------------------------------------------------------
    def _create_thermo_calculator_tab(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)

        # Reaction input controls
        input_box = QGroupBox("Reaktions-Thermodynamik & Kinetik", self)
        input_layout = QGridLayout(input_box)

        input_layout.addWidget(QLabel("Auswahl Reaktion:"), 0, 0)
        self.combo_reactions = QComboBox(self)
        self.combo_reactions.addItems(
            [
                "Aspirin-Synthese (Salicylsäure + Acetanhydrid)",
                "Neutralisation (Salzsäure + Natronlauge)",
                "Paracetamol-Synthese (4-Aminophenol + Acetanhydrid)",
                "Indigo-Farbstoffsynthese (Baeyer-Drewsen)",
            ]
        )
        input_layout.addWidget(self.combo_reactions, 0, 1)

        input_layout.addWidget(QLabel("Temperatur (°C):"), 0, 2)
        self.edit_temp = QLineEdit("25.0", self)
        input_layout.addWidget(self.edit_temp, 0, 3)

        btn_calc = QPushButton("Berechnen (Cantera Engine)", self)
        btn_calc.clicked.connect(self._calculate_thermo)
        input_layout.addWidget(btn_calc, 0, 4)

        layout.addWidget(input_box)

        # Result Displays
        self.lbl_thermo_result = QLabel("Ergebnisse werden hier angezeigt.", self)
        self.lbl_thermo_result.setStyleSheet(
            "padding: 10px; background-color: #182232; border-radius: 4px;"
        )
        layout.addWidget(self.lbl_thermo_result)

        # Titration Graph Section
        titration_box = QGroupBox("Säure-Base Titrationskurve (pH-Verlauf)", self)
        titration_layout = QVBoxLayout(titration_box)

        btn_run_titration = QPushButton(
            "Titrationskurve berechnen (0.1M Essigsäure vs 0.1M NaOH)", self
        )
        btn_run_titration.setProperty("id", "SecondaryBtn")
        btn_run_titration.clicked.connect(self._calculate_titration)
        titration_layout.addWidget(btn_run_titration)

        self.titration_canvas = TitrationCanvasWidget(self)
        titration_layout.addWidget(self.titration_canvas)

        layout.addWidget(titration_box)
        return widget

    def _calculate_thermo(self) -> None:
        idx = self.combo_reactions.currentIndex()
        try:
            temp_c = float(self.edit_temp.text())
        except ValueError:
            temp_c = 25.0

        if idx == 0:
            reactants = {"salicylic_acid": 1.0, "acetic_anhydride": 1.0}
            products = {"aspirin": 1.0, "acetic_acid": 1.0}
            ea = 65.0
        elif idx == 1:
            reactants = {"HCl_aq": 1.0, "NaOH_aq": 1.0}
            products = {"NaCl_aq": 1.0, "H2O": 1.0}
            ea = 15.0
        elif idx == 2:
            reactants = {"4_aminophenol": 1.0, "acetic_anhydride": 1.0}
            products = {"paracetamol": 1.0, "acetic_acid": 1.0}
            ea = 50.0
        else:
            reactants = {"2_nitrobenzaldehyde": 2.0, "acetone": 1.0}
            products = {"indigo": 1.0, "acetic_acid": 2.0, "H2O": 2.0}
            ea = 40.0

        res = THERMO_ENGINE.calculate_reaction_thermodynamics(
            reactants=reactants,
            products=products,
            temperature_c=temp_c,
            activation_energy_kj_mol=ea,
        )

        exotherm_color = "#f43f5e" if res.is_exothermic else "#38bdf8"
        spont_color = "#10b981" if res.is_spontaneous else "#f59e0b"

        text = (
            f"<b>Reaktionsgleichung:</b> <code>{res.equation}</code><br>"
            f"<b>Reaktionsenthalpie (ΔH°):</b> <span style='color:{exotherm_color};'>{res.delta_h_kj_mol:+.2f} kJ/mol</span> ({'Exotherm' if res.is_exothermic else 'Endotherm'}) | "
            f"<b>Entropie (ΔS°):</b> {res.delta_s_j_mol_k:+.2f} J/(mol·K)<br>"
            f"<b>Gibbs-Freie-Energie (ΔG°):</b> <span style='color:{spont_color};'>{res.delta_g_kj_mol:+.2f} kJ/mol</span> ({'Spontan' if res.is_spontaneous else 'Erzwungen'}) | "
            f"<b>Gleichgewichtskonstante K_eq:</b> {res.equilibrium_constant_k_eq:.4e}<br>"
            f"<b>Geschwindigkeitskonstante k(T):</b> {res.rate_constant_k:.4e} s⁻¹ | "
            f"<b>Adiabat. T-Sprung:</b> +{res.adiabatic_temperature_rise_c:.1f} °C"
        )
        if res.warnings:
            text += "<br><span style='color:#f43f5e;'>⚠️ " + "<br>⚠️ ".join(res.warnings) + "</span>"

        self.lbl_thermo_result.setText(text)

    def _calculate_titration(self) -> None:
        points = THERMO_ENGINE.calculate_titration_curve(
            analyte_conc_m=0.1,
            analyte_vol_ml=25.0,
            titrant_conc_m=0.1,
            pka=4.76,
            points=40,
        )
        self.titration_canvas.set_data(points)

    # -------------------------------------------------------------------------
    # TAB 3: RDKit Cheminformatics & 3D
    # -------------------------------------------------------------------------
    def _create_rdkit_tab(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)

        mol_box = QGroupBox("SMILES zu 3D-Konformer & Deskriptoren", self)
        mol_layout = QGridLayout(mol_box)

        mol_layout.addWidget(QLabel("SMILES-Code:"), 0, 0)
        self.edit_smiles = QLineEdit("CC(=O)Oc1ccccc1C(=O)O", self)  # Aspirin default
        mol_layout.addWidget(self.edit_smiles, 0, 1)

        mol_layout.addWidget(QLabel("Name:"), 0, 2)
        self.edit_mol_name = QLineEdit("Aspirin", self)
        mol_layout.addWidget(self.edit_mol_name, 0, 3)

        btn_embed = QPushButton("3D-Konformation berechnen", self)
        btn_embed.clicked.connect(self._calculate_rdkit)
        mol_layout.addWidget(btn_embed, 0, 4)

        layout.addWidget(mol_box)

        self.txt_mol_descriptors = QTextEdit(self)
        self.txt_mol_descriptors.setReadOnly(True)
        layout.addWidget(self.txt_mol_descriptors)

        return widget

    def _calculate_rdkit(self) -> None:
        smiles = self.edit_smiles.text().strip()
        name = self.edit_mol_name.text().strip() or "Molekül"

        props = RDKIT_ENGINE.smiles_to_3d_molecule(smiles, name=name)
        if not props:
            QMessageBox.warning(self, "Fehler", "Ungültiger SMILES-Code!")
            return

        report = (
            f"<h2>3D-Molekülanalyse: {props.iupac_name}</h2>"
            f"<p><b>Summenformel:</b> {props.formula} | <b>Gesamtatome (inkl. H):</b> {props.atom_count}</p>"
            f"<p><b>Molmasse:</b> {props.molecular_weight:.2f} g/mol | <b>Exakte Masse:</b> {props.exact_mass:.4f}</p>"
            f"<p><b>LogP (Lipophilie):</b> {props.log_p:.2f} | <b>TPSA:</b> {props.tpsa:.2f} Å²</p>"
            f"<p><b>H-Brücken-Donoren:</b> {props.num_h_donors} | <b>H-Brücken-Akzeptoren:</b> {props.num_h_acceptors}</p>"
            f"<p><b>Drehbare Bindungen:</b> {props.num_rotatable_bonds} | <b>Aromatische Ringe:</b> {props.num_aromatic_rings}</p>"
            f"<p><b>Lipinski Rule of 5:</b> <span style='color:#10b981;'>{'BESTANDEN' if props.lipinski_rule_of_five_pass else 'NICHT BESTANDEN'}</span></p>"
            f"<p><b>PDB-Struktur (Vorschau):</b><pre>{props.pdb_block[:400]}...</pre></p>"
        )
        self.txt_mol_descriptors.setHtml(report)

    # -------------------------------------------------------------------------
    # TAB 4: Blender 3D Live-Bridge
    # -------------------------------------------------------------------------
    def _create_blender_bridge_tab(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)

        bridge_box = QGroupBox("Blender 5.2 Live Desktop Fernsteuerung", self)
        b_layout = QGridLayout(bridge_box)

        btn_ping = QPushButton("Bridge Status prüfen", self)
        btn_ping.clicked.connect(self._ping_blender)
        b_layout.addWidget(btn_ping, 0, 0)

        btn_cam_overview = QPushButton("Kamera: Übersicht", self)
        btn_cam_overview.clicked.connect(lambda: self._set_blender_cam("Cam_Lab_Overview"))
        b_layout.addWidget(btn_cam_overview, 0, 1)

        btn_cam_detail = QPushButton("Kamera: Werkbank Detail", self)
        btn_cam_detail.clicked.connect(lambda: self._set_blender_cam("Cam_Workbench_Detail"))
        b_layout.addWidget(btn_cam_detail, 0, 2)

        btn_cam_hood = QPushButton("Kamera: Abzug & Sicherheit", self)
        btn_cam_hood.clicked.connect(lambda: self._set_blender_cam("Cam_FumeHood_View"))
        b_layout.addWidget(btn_cam_hood, 0, 3)

        layout.addWidget(bridge_box)

        self.txt_bridge_log = QTextEdit(self)
        self.txt_bridge_log.setReadOnly(True)
        self.txt_bridge_log.append("Blender Bridge Client bereit. Port 9876.")
        layout.addWidget(self.txt_bridge_log)

        return widget

    def _ping_blender(self) -> None:
        import socket

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.5)
            s.connect(("127.0.0.1", 9876))
            s.close()
            self.lbl_engine_status.setText("● Blender IPC Bridge: 127.0.0.1:9876 [ONLINE]")
            self.lbl_engine_status.setStyleSheet("color: #10b981; font-weight: bold;")
            self.txt_bridge_log.append(
                ">>> Ping erfolgreich: Blender MCP Addon ist online und lauscht auf Port 9876."
            )
        except Exception as e:
            self.lbl_engine_status.setText("● Blender IPC Bridge: 127.0.0.1:9876 [OFFLINE]")
            self.lbl_engine_status.setStyleSheet("color: #f43f5e; font-weight: bold;")
            self.txt_bridge_log.append(
                f">>> Verbindung fehlgeschlagen: {e}. Bitte Blender starten."
            )

    def _set_blender_cam(self, cam_name: str) -> None:
        from blender_client import execute_code_snippet

        code = f'import bpy\ncam = bpy.data.objects.get("{cam_name}")\nif cam:\n    bpy.context.scene.camera = cam\n    print("Camera set to {cam_name}")'
        res = execute_code_snippet(code)
        self.txt_bridge_log.append(f">>> Aktive Kamera gesetzt auf: {cam_name} (Code: {res})")


def launch_desktop_app() -> None:
    """Entry point for native desktop application."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = ChemLabMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_desktop_app()
