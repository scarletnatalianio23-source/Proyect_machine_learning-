"""
Synthetic dataset generator for the Forest Awareness project (v2).

IMPORTANT: the values produced here are FICTIONAL (simulated). The municipality
names and departments are real, and the surface areas are approximate, but the
population, cattle, planted area, poverty index and forest loss are simulated.
They are NOT official IDEAM, DANE or SMByC figures.

One row = one municipality in one year (2019-2023). Target: hectares of forest
lost that year (`forest_loss_ha`).

Usage:  python data/generate_dataset.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

# name | department | region | approximate area (km2)
MUNICIPALITIES = """
Cartagena del Chairá|Caquetá|Amazon|12900
San Vicente del Caguán|Caquetá|Amazon|17000
Solano|Caquetá|Amazon|42000
Florencia|Caquetá|Amazon|2300
Puerto Rico|Caquetá|Amazon|3300
La Montañita|Caquetá|Amazon|1800
Solita|Caquetá|Amazon|1700
Milán|Caquetá|Amazon|1200
Belén de los Andaquíes|Caquetá|Amazon|1200
El Doncello|Caquetá|Amazon|1200
Paujil|Caquetá|Amazon|1300
Albania|Caquetá|Amazon|400
Curillo|Caquetá|Amazon|600
Morelia|Caquetá|Amazon|300
La Macarena|Meta|Orinoquia|11200
Uribe|Meta|Orinoquia|7500
Mesetas|Meta|Orinoquia|2400
Puerto Rico|Meta|Orinoquia|3200
Mapiripán|Meta|Orinoquia|11800
Puerto Gaitán|Meta|Orinoquia|17500
Puerto Concordia|Meta|Orinoquia|1500
Puerto Lleras|Meta|Orinoquia|2300
Vista Hermosa|Meta|Orinoquia|4100
San Martín|Meta|Orinoquia|6500
Villavicencio|Meta|Orinoquia|1300
Granada|Meta|Orinoquia|370
Acacías|Meta|Orinoquia|1100
Puerto López|Meta|Orinoquia|6700
Cumaral|Meta|Orinoquia|600
Restrepo|Meta|Orinoquia|200
Lejanías|Meta|Orinoquia|560
El Castillo|Meta|Orinoquia|500
San José del Guaviare|Guaviare|Amazon|16800
Calamar|Guaviare|Amazon|11200
El Retorno|Guaviare|Amazon|12000
Miraflores|Guaviare|Amazon|13000
Puerto Asís|Putumayo|Amazon|2700
Puerto Guzmán|Putumayo|Amazon|4000
Puerto Leguízamo|Putumayo|Amazon|10900
Orito|Putumayo|Amazon|2300
Valle del Guamuez|Putumayo|Amazon|800
Mocoa|Putumayo|Amazon|1300
Villagarzón|Putumayo|Amazon|1400
San Miguel|Putumayo|Amazon|1100
Leticia|Amazonas|Amazon|5900
Puerto Nariño|Amazonas|Amazon|1700
Mitú|Vaupés|Amazon|16400
Carurú|Vaupés|Amazon|6200
Inírida|Guainía|Amazon|16400
Puerto Carreño|Vichada|Orinoquia|12400
Cumaribo|Vichada|Orinoquia|65600
La Primavera|Vichada|Orinoquia|19000
Santa Rosalía|Vichada|Orinoquia|2800
Tibú|Norte de Santander|Andean|2700
Sardinata|Norte de Santander|Andean|1400
El Tarra|Norte de Santander|Andean|700
Teorama|Norte de Santander|Andean|1000
Cúcuta|Norte de Santander|Andean|1100
Ocaña|Norte de Santander|Andean|460
Convención|Norte de Santander|Andean|1000
Pamplona|Norte de Santander|Andean|1100
Tierralta|Córdoba|Caribbean|5000
Puerto Libertador|Córdoba|Caribbean|1500
Montelíbano|Córdoba|Caribbean|1500
Valencia|Córdoba|Caribbean|1100
Montería|Córdoba|Caribbean|3100
Lorica|Córdoba|Caribbean|900
Sahagún|Córdoba|Caribbean|1000
Cereté|Córdoba|Caribbean|1000
Zaragoza|Antioquia|Andean|1000
El Bagre|Antioquia|Andean|1500
Segovia|Antioquia|Andean|1200
Remedios|Antioquia|Andean|2000
Cáceres|Antioquia|Andean|2000
Tarazá|Antioquia|Andean|1300
Briceño|Antioquia|Andean|400
Ituango|Antioquia|Andean|2600
Anorí|Antioquia|Andean|1500
Medellín|Antioquia|Andean|380
Rionegro|Antioquia|Andean|200
Santa Fe de Antioquia|Antioquia|Andean|490
Jardín|Antioquia|Andean|220
Yarumal|Antioquia|Andean|600
Apartadó|Antioquia|Andean|600
Turbo|Antioquia|Caribbean|3000
Necoclí|Antioquia|Caribbean|1400
Carepa|Antioquia|Caribbean|400
Chigorodó|Antioquia|Caribbean|610
Mutatá|Antioquia|Caribbean|1100
Dabeiba|Antioquia|Andean|1900
Frontino|Antioquia|Andean|1300
Murindó|Antioquia|Pacific|1500
Vigía del Fuerte|Antioquia|Pacific|1800
Quibdó|Chocó|Pacific|3300
Istmina|Chocó|Pacific|1300
Condoto|Chocó|Pacific|700
Tadó|Chocó|Pacific|800
Nóvita|Chocó|Pacific|1500
Medio San Juan|Chocó|Pacific|1100
Bajo Baudó|Chocó|Pacific|3900
Riosucio|Chocó|Pacific|6100
Carmen del Darién|Chocó|Pacific|3000
Acandí|Chocó|Pacific|1300
Bahía Solano|Chocó|Pacific|1700
Nuquí|Chocó|Pacific|950
Lloró|Chocó|Pacific|1200
Tumaco|Nariño|Pacific|3700
Barbacoas|Nariño|Pacific|2300
Roberto Payán|Nariño|Pacific|1400
Magüí Payán|Nariño|Pacific|1400
El Charco|Nariño|Pacific|2500
Olaya Herrera|Nariño|Pacific|1500
Francisco Pizarro|Nariño|Pacific|1500
Pasto|Nariño|Andean|1100
Ipiales|Nariño|Andean|1700
Túquerres|Nariño|Andean|300
Guapi|Cauca|Pacific|2700
Timbiquí|Cauca|Pacific|1800
López de Micay|Cauca|Pacific|1200
Argelia|Cauca|Andean|600
El Tambo|Cauca|Andean|3200
Popayán|Cauca|Andean|510
Santander de Quilichao|Cauca|Andean|540
Buenaventura|Valle del Cauca|Pacific|6100
Cali|Valle del Cauca|Andean|560
Jamundí|Valle del Cauca|Andean|1000
Dagua|Valle del Cauca|Andean|870
Tuluá|Valle del Cauca|Andean|910
Santa Rosa del Sur|Bolívar|Caribbean|2200
Simití|Bolívar|Caribbean|1500
San Pablo|Bolívar|Caribbean|2000
Cantagallo|Bolívar|Caribbean|1000
Montecristo|Bolívar|Caribbean|1100
Arenal|Bolívar|Caribbean|400
Cartagena|Bolívar|Caribbean|610
Magangué|Bolívar|Caribbean|1100
Barrancabermeja|Santander|Andean|1300
Puerto Wilches|Santander|Andean|1900
Sabana de Torres|Santander|Andean|1200
Landázuri|Santander|Andean|600
Bucaramanga|Santander|Andean|165
San Gil|Santander|Andean|150
Socorro|Santander|Andean|120
Aguachica|Cesar|Caribbean|900
Pelaya|Cesar|Caribbean|400
Valledupar|Cesar|Caribbean|4500
Codazzi|Cesar|Caribbean|1500
Santa Marta|Magdalena|Caribbean|2400
Ciénaga|Magdalena|Caribbean|1200
Aracataca|Magdalena|Caribbean|1500
Fundación|Magdalena|Caribbean|900
Riohacha|La Guajira|Caribbean|3100
Dibulla|La Guajira|Caribbean|1900
Uribia|La Guajira|Caribbean|7900
Maicao|La Guajira|Caribbean|4100
Fonseca|La Guajira|Caribbean|500
Tame|Arauca|Orinoquia|5200
Saravena|Arauca|Orinoquia|1000
Arauca|Arauca|Orinoquia|5800
Arauquita|Arauca|Orinoquia|3000
Yopal|Casanare|Orinoquia|2700
Paz de Ariporo|Casanare|Orinoquia|7500
Hato Corozal|Casanare|Orinoquia|5800
Aguazul|Casanare|Orinoquia|1700
Maní|Casanare|Orinoquia|3500
San Luis de Palenque|Casanare|Orinoquia|2400
Chaparral|Tolima|Andean|2200
Planadas|Tolima|Andean|1000
Ibagué|Tolima|Andean|1400
Rioblanco|Tolima|Andean|1800
Neiva|Huila|Andean|1500
Pitalito|Huila|Andean|600
La Plata|Huila|Andean|1400
Algeciras|Huila|Andean|600
Tunja|Boyacá|Andean|120
Puerto Boyacá|Boyacá|Andean|1500
Otanche|Boyacá|Andean|500
Manizales|Caldas|Andean|510
Pensilvania|Caldas|Andean|1100
Pereira|Risaralda|Andean|600
Armenia|Quindío|Andean|120
Bogotá D.C.|Cundinamarca|Andean|1600
Soacha|Cundinamarca|Andean|185
La Palma|Cundinamarca|Andean|200
Sincelejo|Sucre|Caribbean|280
San Onofre|Sucre|Caribbean|1100
Barranquilla|Atlántico|Caribbean|155
Sabanalarga|Atlántico|Caribbean|400
""".strip().splitlines()

LN_POP_BASE = {"Andean": 9.7, "Caribbean": 9.8, "Pacific": 9.4, "Orinoquia": 9.0, "Amazon": 8.7}
CATTLE_PER_KM2 = {"Andean": 28, "Caribbean": 45, "Pacific": 4, "Orinoquia": 22, "Amazon": 14}
PLANTED_PER_KM2 = {"Andean": 14, "Caribbean": 12, "Pacific": 3.5, "Orinoquia": 4, "Amazon": 1.4}
NBI_MEAN = {"Andean": 40, "Caribbean": 58, "Pacific": 72, "Orinoquia": 48, "Amazon": 66}
COCA_PROB = {"Andean": 0.10, "Caribbean": 0.15, "Pacific": 0.45, "Orinoquia": 0.25, "Amazon": 0.45}
ARMED_RATE = {"Andean": 0.35, "Caribbean": 0.8, "Pacific": 1.3, "Orinoquia": 0.8, "Amazon": 1.2}
REGION_EFFECT = {"Andean": 0.0, "Caribbean": -0.1, "Pacific": 0.35, "Orinoquia": 0.15, "Amazon": 0.85}
YEARS = [2019, 2020, 2021, 2022, 2023]
BIG_CITIES = {"Bogotá D.C.", "Medellín", "Cali", "Barranquilla", "Cartagena", "Bucaramanga", "Cúcuta"}


def generate(seed: int = 2026) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for line in MUNICIPALITIES:
        name, dept, region, area = line.split("|")
        area = float(area)
        # Fixed (per municipality) characteristics, simulated.
        ln_pop = rng.normal(LN_POP_BASE[region] + 0.22 * (np.log(area) - 5.8), 0.9)
        if name in BIG_CITIES:
            ln_pop += 2.3
        pop0 = float(np.exp(ln_pop))
        cattle0 = area * CATTLE_PER_KM2[region] * float(np.exp(rng.normal(0, 0.9)))
        if region == "Pacific" or name in BIG_CITIES:
            cattle0 *= 0.3 if name in BIG_CITIES else 1.0
        planted0 = area * PLANTED_PER_KM2[region] * float(np.exp(rng.normal(0, 0.9)))
        nbi0 = float(np.clip(rng.normal(NBI_MEAN[region], 14), 5, 98))
        if name in BIG_CITIES:
            nbi0 = float(rng.uniform(6, 20))
        coca0 = float(np.exp(rng.normal(np.log(150), 1.2))) if rng.random() < COCA_PROB[region] else 0.0
        armed0 = rng.poisson(ARMED_RATE[region] + (0.3 if coca0 > 0 else 0))
        muni_effect = rng.normal(0, 0.45)  # unobserved local factor
        for year in YEARS:
            t = year - 2019
            pop = pop0 * (1 + 0.01 * t)
            cattle = cattle0 * (1 + 0.03 * t) * float(np.exp(rng.normal(0, 0.04)))
            planted = planted0 * (1 + 0.015 * t) * float(np.exp(rng.normal(0, 0.04)))
            nbi = float(np.clip(nbi0 - 0.4 * t + rng.normal(0, 0.8), 3, 100))
            coca = coca0 * float(np.exp(rng.normal(0, 0.15)))
            armed = int(np.clip(armed0 + rng.choice([-1, 0, 0, 1]), 0, 5))
            eta = (
                2.95
                + 0.72 * (np.log(area) - 5.8)
                + 0.22 * (np.log1p(cattle) - 9.0)
                + 0.14 * (np.log1p(planted) - 8.0)
                + 0.06 * np.log1p(coca)
                + 0.010 * (nbi - 52)
                + 0.15 * armed
                - 0.05 * (np.log(pop) - 9.5)
                + 0.03 * t
                + REGION_EFFECT[region]
                + muni_effect
                + rng.normal(0, 0.9)
            )
            loss = float(np.clip(np.round(np.expm1(eta)), 0, 12000))
            if name in BIG_CITIES:
                loss = float(np.round(loss * 0.1))
            p_zero = 1 / (1 + np.exp(-(-2.2 - 0.9 * (np.log(area) - 5.8))))
            if rng.random() < p_zero:
                loss = 0.0
            rows.append({
                "municipality": name, "department": dept, "region": region, "year": year,
                "area_km2": round(area, 1), "population": int(round(pop)),
                "cattle_heads": int(round(cattle)), "planted_area_ha": round(planted, 1),
                "nbi_pct": round(nbi, 1), "coca_ha": round(coca, 1), "armed_groups": armed,
                "forest_loss_ha": int(loss),
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "forest_loss_municipalities.csv"
    df = generate()
    df.to_csv(out, index=False)
    print(f"Saved {len(df)} rows ({df.municipality.nunique()} municipalities) to {out}")
