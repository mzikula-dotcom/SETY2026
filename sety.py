import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import time

# --- 1. DATA Z TVÝCH SOUBORŮ ---
# Data jsou vložena přímo do kódu pro snadné spuštění bez nutnosti externích CSV.

def load_data():
    # A) ZÁKLADNÍ DATA BAZÉNŮ
    data_pools = {
        "Název Bazénového Setu": [
            "BAZÉNOVÝ SET 4 x 3 x 1,2 m", "BAZÉNOVÝ SET 5 x 3 x 1,2 m", 
            "BAZÉNOVÝ SET 6 x 3 x 1,2 m", "BAZÉNOVÝ SET 6 x 3,5 x 1,2 m",
            "BAZÉNOVÝ SET 7 x 3 x 1,2 m", "BAZÉNOVÝ SET 7 x 3,5 x 1,2 m"
        ],
        "Cena BAZÉNOVÉHO SETU bez DPH": [74000, 88000, 94000, 104000, 105000, 114000],
        "Tvar": ["Obdélník se zakulacenými rohy"] * 6,
        "Barva": ["Světlá modrá"] * 6,
        "Schodiště": ["Protiskluzové ROMÁNSKÉ Vnitřní - 3 stupně"] * 6,
        "Filtrace": [
            "4m3/hod vč. 25 kg pískové náplně", "6m3/hod vč. 50 kg pískové náplně", 
            "6m3/hod vč. 50 kg pískové náplně", "9m3/hod vč. 75 kg pískové náplně", 
            "9m3/hod vč. 75 kg pískové náplně", "9m3/hod vč. 75 kg pískové náplně"
        ],
        "Zateplení dna": ["Zateplení dna extrudovaným polystyrénem 20mm ZDARMA"] * 6,
        "Propojení": ["Kompletní propojovací materiál do max. 2m od bazénového skeletu"] * 6
    }
    df_pools = pd.DataFrame(data_pools)

    # B) ROZŠÍŘENÍ (Ceny a položky z tvého CSV)
    data_extensions = [
        ("Změna hloubky na 1,3 m", 4900),
        ("Změna hloubky na 1,4 m", 6900),
        ("Změna hloubky na 1,5 m", 6900),
        ("Příplatek za ostré rohy skeletu", 7200),
        ("Schody přes celou šíři bazénu", 20090),
        ("Vnitřní trojúhelníkové schody", 7600),
        ("Románské vnější schody", 5600),
        ("Bílá barva skeletu", 0),
        ("Šedá RAL 7032 barva skeletu", 0),
        ("Šedá RAL 7035 barva skeletu", 0),
        ("Dávkovač pevných látek do potrubí vč. montáže", 3900),
        ("Úprava slanou vodou VA Salt 15 (do 5x3) vč. montáže", 25800),
        ("Úprava slanou vodou VA Salt 20 (od 6x3) vč. montáže", 26800),
        ("Tepelné čerpadlo Rapid Mini Inverter 9,5kW s chlazením", 36793),
        ("Tepelné čerpadlo Rapid Mini Inverter 12,5kW s chlazením", 48052),
        ("WiFi modul RAPID - vzdálené ovládání", 3136),
        ("WiFi modul NORM - vzdálené ovládání", 2730),
        ("Automatické ovládání pro filtraci / světlo", 6028),
        ("Automatické ovládání filtraci / světlo / protiproud", 6895),
        ("pH - Plus tekutý - 25kg", 1472),
        ("pH - Mínus tekutý - 35kg", 1288),
        ("Chlornan sodný - 35 kg", 1469),
        ("Chlornan sodný - 24 kg, stabilizovaný", 1114),
        ("Tester tabletkový", 350), # Odhad dle kontextu, můžeš upravit
        ("Doprava (Kč/km)", 25)
    ]
    df_ext = pd.DataFrame(data_extensions, columns=["Název položky", "Cena bez DPH"])

    # C) AUTOŘI
    authors = ["Martin Zikula", "Lenka Finklarová", "Zuzana Zikulová", "Drahoslav Houška"]
    
    return df_pools, df_ext, authors

df_pools, df_extensions_source, authors_list = load_data()

# --- 2. GUI APLIKACE ---
st.set_page_config(page_title="Kalkulátor Bazénů 2026", layout="wide")
st.title("🏊 Kalkulátor Bazénových Setů 2026")

# Sidebar - Nastavení
with st.sidebar:
    st.header("Nastavení nabídky")
    selected_pool_name = st.selectbox("Vyberte bazénový set", df_pools["Název Bazénového Setu"])
    vat_rate = st.radio("Sazba DPH", [0, 12, 21], index=1, format_func=lambda x: f"{x} %")
    author_name = st.selectbox("Nabídku zpracoval", authors_list)
    client_name = st.text_input("Jméno klienta (pro PDF)", "")

# Hlavní logika - Získání dat vybraného bazénu
pool_row = df_pools[df_pools["Název Bazénového Setu"] == selected_pool_name].iloc[0]
base_price = float(pool_row["Cena BAZÉNOVÉHO SETU bez DPH"])

# A) Zobrazení informací o setu
st.subheader("1. Informace o vybraném setu")
col1, col2 = st.columns([2, 1])

with col1:
    # Zobrazíme všechny sloupce kromě ceny a názvu
    details = pool_row.drop(["Název Bazénového Setu", "Cena BAZÉNOVÉHO SETU bez DPH"])
    # Přeformátování do tabulky pro hezčí vzhled
    st.table(pd.DataFrame(details).rename(columns={pool_row.name: "Hodnota"}))

with col2:
    st.success(f"**Cena setu bez DPH:**\n# {base_price:,.0f} Kč".replace(",", " "))

st.divider()

# B) Rozšíření - Editovatelná tabulka
st.subheader("2. Rozšíření a příslušenství")
st.info("Zadejte množství u položek. Cenu za kus můžete v případě potřeby přepsat.")

# Příprava dat pro editor
if "editor_data" not in st.session_state:
    df_extensions_source["Množství"] = 0
    df_extensions_source["Poznámka"] = ""
    # Sloupec pro editaci
    st.session_state.editor_data = df_extensions_source

# Zobrazení editoru
edited_df = st.data_editor(
    st.session_state.editor_data,
    column_config={
        "Cena bez DPH": st.column_config.NumberColumn("Cena/ks (bez DPH)", format="%d Kč", min_value=0),
        "Množství": st.column_config.NumberColumn("Množství", min_value=0, step=1),
        "Název položky": st.column_config.TextColumn("Položka", disabled=True),
    },
    use_container_width=True,
    num_rows="dynamic", # Umožní přidat vlastní řádky
    key="editor"
)

# Filtrace vybraných položek (kde je množství > 0)
selected_extensions = edited_df[edited_df["Množství"] > 0].copy()
selected_extensions["Celkem bez DPH"] = selected_extensions["Cena bez DPH"] * selected_extensions["Množství"]

# C) Kalkulace
st.subheader("3. Celková kalkulace")

extensions_sum = selected_extensions["Celkem bez DPH"].sum()
total_no_vat = base_price + extensions_sum
vat_amount = total_no_vat * (vat_rate / 100)
total_with_vat = total_no_vat + vat_amount

c1, c2, c3 = st.columns(3)
c1.metric("Základní set", f"{base_price:,.0f} Kč".replace(",", " "))
c2.metric("Rozšíření celkem", f"{extensions_sum:,.0f} Kč".replace(",", " "))
c3.metric(f"Mezisoučet (bez DPH)", f"{total_no_vat:,.0f} Kč".replace(",", " "))

st.markdown(f"""
<div style="background-color: #d4edda; padding: 20px; border-radius: 10px; text-align: center;">
    <h2 style="color: #155724; margin:0;">CELKOVÁ CENA (vč. {vat_rate}% DPH): {total_with_vat:,.0f} Kč</h2>
</div>
""", unsafe_allow_html=True)

# Kontrolní tabulka vybraných
if not selected_extensions.empty:
    st.caption("Rekapitulace vybraných položek:")
    st.dataframe(selected_extensions[["Název položky", "Množství", "Cena bez DPH", "Celkem bez DPH"]], hide_index=True)

# --- 3. EXPORT DO PDF ---
def create_pdf():
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 10)
            self.cell(0, 10, 'Cenova nabidka - Bazenove sety 2026', 0, 1, 'R')

    pdf = PDF()
    pdf.add_page()
    
    # Použijeme Arial. Pro českou diakritiku by bylo nutné nahrát .ttf font (např. DejaVuSans).
    # Zde používáme 'latin-1' a transliteraci pro kompatibilitu bez externích souborů.
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"NABIDKA: {selected_pool_name}", 0, 1, 'L')
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"Klient: {client_name}", 0, 1)
    pdf.cell(0, 8, f"Vystavil: {author_name}", 0, 1)
    pdf.cell(0, 8, f"Datum: {time.strftime('%d.%m.%Y')}", 0, 1)
    pdf.ln(5)
    
    # 1. Bazén
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(0, 10, "1. Specifikace bazenoveho setu", 1, 1, 'L', fill=True)
    
    pdf.set_font("Arial", '', 10)
    for key, value in details.items():
        # Jednoduchá normalizace textu (odstranění diakritiky pro základní FPDF)
        key_norm = key.encode('latin-1', 'ignore').decode('latin-1')
        val_norm = str(value).encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(60, 7, f"{key_norm}:", 0)
        pdf.cell(0, 7, f"{val_norm}", 0, 1)
        
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(150, 8, "Cena setu bez DPH:", 0)
    pdf.cell(0, 8, f"{base_price:,.0f} Kc", 0, 1, 'R')
    pdf.ln(5)

    # 2. Rozšíření
    if not selected_extensions.empty:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "2. Vybrane prislusenstvi", 1, 1, 'L', fill=True)
        pdf.set_font("Arial", 'B', 9)
        
        # Hlavička
        pdf.cell(100, 8, "Polozka", 1)
        pdf.cell(20, 8, "Ks", 1, 0, 'C')
        pdf.cell(35, 8, "Cena/ks", 1, 0, 'R')
        pdf.cell(35, 8, "Celkem", 1, 1, 'R')
        
        pdf.set_font("Arial", '', 9)
        for _, row in selected_extensions.iterrows():
            name = str(row['Název položky']).encode('latin-1', 'ignore').decode('latin-1')
            # Zkrácení dlouhých názvů
            if len(name) > 55: name = name[:52] + "..."
            
            pdf.cell(100, 7, name, 1)
            pdf.cell(20, 7, str(row['Množství']), 1, 0, 'C')
            pdf.cell(35, 7, f"{row['Cena bez DPH']:.0f}", 1, 0, 'R')
            pdf.cell(35, 7, f"{row['Celkem bez DPH']:.0f}", 1, 1, 'R')
        pdf.ln(5)

    # 3. Součet
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "3. Rekapitulace ceny", 1, 1, 'L', fill=True)
    pdf.set_font("Arial", '', 11)
    
    pdf.cell(140, 8, "Celkem bez DPH:", 0)
    pdf.cell(0, 8, f"{total_no_vat:,.0f} Kc", 0, 1, 'R')
    
    pdf.cell(140, 8, f"DPH ({vat_rate}%):", 0)
    pdf.cell(0, 8, f"{vat_amount:,.0f} Kc", 0, 1, 'R')
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(140, 12, "CENA CELKEM S DPH:", 0)
    pdf.cell(0, 12, f"{total_with_vat:,.0f} Kc", 0, 1, 'R')

    return pdf.output(dest='S').encode('latin-1')

st.download_button(
    label="📄 Uložit nabídku do PDF",
    data=create_pdf(),
    file_name=f"Nabidka_{selected_pool_name.replace(' ', '_')}.pdf",
    mime="application/pdf"
)
