"""
Physical constants for electrochemistry.

Faraday constant F = 96485.33212 C/mol (exact, SI since 2019)
Gas constant R = 8.314462618 J/(mol·K)
Standard temperature T0 = 298.15 K
Standard molar masses (g/mol)
"""

import math

# Faraday constant in C/mol
F: float = 96485.33212

# Universal gas constant in J/(mol·K)
R: float = 8.314462618

# Standard temperature in K
T0: float = 298.15

# Nernst slope at 25 °C in V per decade per electron: (RT/F) * ln(10)
NERNST_SLOPE_V_DECADE: float = (R * T0 / F) * math.log(10)

# Standard molar masses (g/mol)
M_COPPER: float = 63.546
M_ZINC: float = 65.38
M_SILVER: float = 107.8682
M_IRON: float = 55.845
M_ALUMINIUM: float = 26.9815385
M_SODIUM: float = 22.98976928
M_CHLORINE: float = 35.45
M_HYDROGEN: float = 1.008

# Electron charge in coulombs
ELECTRON_CHARGE_C: float = 1.602176634e-19

# Avogadro constant mol^-1
AVOGADRO: float = 6.02214076e23
