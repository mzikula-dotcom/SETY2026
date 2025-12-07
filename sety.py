import streamlit as st
import pandas as pd
from fpdf import FPDF

# --- 1. Funkce pro generování PDF ---
def vytvorit_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="Report Prodeju", ln=1, align="C")
    pdf.ln(10) # Odřádkování
    
    # Jednoduchý výpis dat z tabulky do PDF
    # (Iterujeme přes řádky tabulky)
    for i, row in dataframe.iterrows():
        text_radku = f"Den: {row['Den']} | Prodeje: {row['Prodeje']} | Zakaznici: {row['Zakaznici']}"
        pdf.cell(200, 10, txt=text_radku, ln=1)
        
    # Vrátíme data jako řetězec (latin-1 kódování je pro FPDF standard)
    return pdf.output(dest='S').encode('latin-1')

# --- 2. Hlavní aplikace ---
st.title("Ahoj Martine! 👋")
st.write("Tady je tvůj vylepšený dashboard s exportem do PDF.")

data = {
    'Den': ['Pondeli', 'Utery', 'Streda', 'Ctvrtek', 'Patek'], # FPDF má raději text bez háčků/čárek v základu
    'Prodeje': [100, 150, 130, 200, 180],
    'Zakaznici': [10, 15, 12, 25, 20]
}
df = pd.DataFrame(data)

st.subheader("📊 Tabulka dat")
st.dataframe(df)

st.subheader("📈 Graf")
st.bar_chart(df.set_index('Den')['Prodeje'])

# --- 3. Tlačítko pro stažení PDF ---
st.write("---") # Oddělovací čára
st.subheader("📥 Export")

if st.button("Vygenerovat PDF report"):
    pdf_data = vytvorit_pdf(df)
    st.download_button(
        label="Stáhnout PDF soubor",
        data=pdf_data,
        file_name="report_prodeje.pdf",
        mime="application/pdf"
    )