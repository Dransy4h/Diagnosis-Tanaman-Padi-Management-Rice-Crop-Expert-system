!pip install gradio
import gradio as gr
import json
import pandas as pd
from typing import List, Tuple

# ---------------------------------------------------------------------------
# BAGIAN 1: MEMUAT BASIS PENGETAHUAN (KNOWLEDGE BASE)
# ---------------------------------------------------------------------------

FILE_PATH = 'knowledge_base.json'
knowledge_base = {}

try:
    with open(FILE_PATH, 'r') as json_file:
        knowledge_base = json.load(json_file)
    print(f"✅ Basis pengetahuan berhasil dimuat dari '{FILE_PATH}'.")
except FileNotFoundError:
    print(f"❌ Error: File '{FILE_PATH}' tidak ditemukan.")
except json.JSONDecodeError:
    print(f"❌ Error: Gagal membaca file JSON. Format file '{FILE_PATH}' mungkin rusak.")

# ---------------------------------------------------------------------------
# BAGIAN 2: MESIN INFERENSI (FUNGSI DIAGNOSIS)
# ---------------------------------------------------------------------------

def diagnose_pest_disease_from_json(selected_symptom_ids: List[str], kb: dict) -> List[dict]:
    """Fungsi logis inti untuk menghitung diagnosis dan CF."""

    # ... (Logika diagnosis tidak berubah) ...
    print("\n--- Memulai Diagnosis (dari UI) ---")
    print(f"Gejala yang dipilih: {', '.join(selected_symptom_ids)}")

    results = []
    if not kb:
        print("Basis Pengetahuan (kb) kosong.")
        return []

    rules = kb.get('rules', {})
    diseases = kb.get('diseases', {})
    symptoms_cf = kb.get('symptoms', {}).get('certainty_factors', {})

    for disease_id, rule_data in rules.items():
        rule_symptoms = rule_data.get('symptoms', [])
        cf_rule = rule_data.get('cf_rule', 0.0)

        # Forward Chaining: Periksa apakah SEMUA gejala cocok
        if all(symptom in selected_symptom_ids for symptom in rule_symptoms):
            print(f"ATURAN COCOK: {diseases.get(disease_id, disease_id)}")

            # Perhitungan Certainty Factor
            symptom_cfs_in_rule = [symptoms_cf.get(s, 0.0) for s in rule_symptoms]
            parallel_cf = min(symptom_cfs_in_rule) if symptom_cfs_in_rule else 0.0
            final_cf = parallel_cf * cf_rule

            print(f"  CF Paralel: {parallel_cf:.2f}, CF Aturan: {cf_rule:.2f}, CF Final: {final_cf:.2f}")

            results.append({
                'disease_name': diseases.get(disease_id, f"Penyakit {disease_id}"),
                'confidence': final_cf
            })

    if not results:
        print("Tidak ada aturan yang cocok.")

    results.sort(key=lambda x: x['confidence'], reverse=True)
    return results

# ---------------------------------------------------------------------------
# BAGIAN 3: FUNGSI WRAPPER UNTUK GRADIO
# ---------------------------------------------------------------------------

def get_symptom_choices(kb):
    """Mempersiapkan daftar pilihan gejala untuk UI Gradio."""
    if not kb:
        return [("Error: Gagal memuat knowledge_base.json", "NONE")]

    symptom_descriptions = kb.get('symptoms', {}).get('descriptions', {})
    symptoms_cf = kb.get('symptoms', {}).get('certainty_factors', {})

    all_symptom_ids = set(symptom_descriptions.keys()) | set(symptoms_cf.keys())

    choices = []
    for symptom_id in sorted(all_symptom_ids):
        desc = symptom_descriptions.get(symptom_id, f"Gejala {symptom_id} (deskripsi tidak ada)")
        choices.append((f"{symptom_id}: {desc}", symptom_id))
    return choices


def gradio_diagnose_interface(selected_symptom_ids: List[str]) -> pd.DataFrame:
    """
    Fungsi yang dipanggil oleh Gradio, hanya menangani diagnosis.
    """
    if not selected_symptom_ids:
        return pd.DataFrame(columns=["Penyakit / Hama", "Tingkat Keyakinan"])

    diagnoses = diagnose_pest_disease_from_json(selected_symptom_ids, knowledge_base)

    if not diagnoses:
        return pd.DataFrame([["Tidak ada diagnosis yang cocok", "0.00 %"]],
                             columns=["Penyakit / Hama", "Tingkat Keyakinan"])

    output_data = []
    for diag in diagnoses:
        penyakit = diag['disease_name']
        keyakinan_str = f"{diag['confidence'] * 100:.2f} %"
        output_data.append([penyakit, keyakinan_str])

    df = pd.DataFrame(output_data, columns=["Penyakit / Hama", "Tingkat Keyakinan"])
    return df

# ---------------------------------------------------------------------------
# BAGIAN 4: MEMBANGUN DAN MELUNCURKAN UI GRADIO (REVISI MENGGUNAKAN GROUP)
# ---------------------------------------------------------------------------

# Dapatkan daftar pilihan gejala
symptom_choices_list = get_symptom_choices(knowledge_base)

# Tentukan URL gambar untuk background
IMAGE_URL = ""
# CSS Statis (Mengatur Background dan Transparansi Panel)
STATIC_CSS = f"""
/* Mengatur background utama Gradio container menggunakan URL */
.gradio-container {{
    background-image: url('{IMAGE_URL}') !important;
    background-size: cover !important;
    background-repeat: no-repeat !important;
    background-position: center center !important;
    background-attachment: fixed;
}}

/* Membuat panel UI (Group) semi-transparan dan berbingkai */
.group {{
    background-color: rgba(255, 255, 255, 0.95) !important; /* Sedikit kurang transparan */
    border: 1px solid #ddd; /* Bingkai tipis */
    border-radius: 10px !important;
    padding: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.15); /* Menambah bayangan untuk efek box */
}}

/* Memastikan wrapper utama tidak memiliki warna solid */
.gradio-container > .wrap {{
    background-color: transparent !important;
}}

/* Membuat judul dan markdown lebih menonjol */
h1, h2, h3 {{
    color: #004d00;
}}
"""

with gr.Blocks(theme=gr.themes.Soft(), css=STATIC_CSS) as demo:

    # 🌟 GROUP UTAMA: Membungkus seluruh konten UI (Menggantikan gr.Box()) 🌟
    with gr.Group(elem_classes="main-content-group"):
        gr.Markdown(
            """
            # 🌾 Sistem Pakar Diagnosis Hama dan Penyakit Padi
            Aplikasi ini menggunakan metode Forward Chaining dan Certainty Factor.
            """
        )

        with gr.Row():
            # Kolom Input (Kiri) - DIBUNGKUS GROUP
            with gr.Column(scale=1):
                with gr.Group(): # Group untuk kolom Input
                    input_symptoms = gr.CheckboxGroup(
                        choices=symptom_choices_list,
                        label="Pilih Gejala yang Diamati",
                        info="Pilih satu atau lebih gejala yang sesuai."
                    )

                    btn_diagnose = gr.Button("Diagnosis Sekarang", variant="primary")
                    btn_clear = gr.Button("Bersihkan Pilihan", variant="stop")

            # Kolom Output (Kanan) - DIBUNGKUS GROUP
            with gr.Column(scale=2):
                with gr.Group(): # Group untuk kolom Output
                    gr.Markdown("## Hasil Diagnosis")
                    output_diagnosis = gr.DataFrame(
                        headers=["Penyakit / Hama", "Tingkat Keyakinan"],
                        label="Diagnosis",
                        row_count=(1, "dynamic"),
                        col_count=(2, "fixed")
                    )

        # Menghubungkan tombol ke fungsi diagnosis
        btn_diagnose.click(
            fn=gradio_diagnose_interface,
            inputs=input_symptoms,
            outputs=output_diagnosis
        )

        # Menghubungkan tombol clear
        btn_clear.click(
            fn=lambda: ([], pd.DataFrame(columns=["Penyakit / Hama", "Tingkat Keyakinan"])),
            inputs=[],
            outputs=[input_symptoms, output_diagnosis]
        )

        # Menambahkan contoh
        gr.Examples(
            examples=[
                [['A1', 'B2', 'B8', 'B11', 'B17']],
                [['A6', 'B1', 'B8', 'B12']],
                [['A10', 'B10']]
            ],
            inputs=input_symptoms,
            outputs=output_diagnosis,
            fn=gradio_diagnose_interface,
            cache_examples=False
        )

# Meluncurkan aplikasi
if __name__ == "__main__":
    demo.launch(debug=True)