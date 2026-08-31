import streamlit as st
import pandas as pd
from datetime import date, datetime
import os
import io
import glob
import shutil

st.set_page_config(
    page_title="SinTec | Gestione Manuali & Commesse", 
    layout="wide", 
    page_icon="⚙️",
    initial_sidebar_state="collapsed"
)

# --- STYLING BRANDIZZATO SINTEC (DA WWW.SIN-TEC.IT) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background-color: #f4f6f9 !important;
    }
    
    /* Header Brand SinTec */
    .sintec-header {
        background: linear-gradient(135deg, #0a2540 0%, #003366 100%);
        padding: 1.5rem 2rem;
        border-radius: 14px;
        color: #ffffff;
        box-shadow: 0 4px 12px rgba(10, 37, 64, 0.12);
        margin-bottom: 1.5rem;
        border-left: 6px solid #00a3e0;
    }
    .sintec-brand {
        font-size: 0.85rem;
        font-weight: 800;
        letter-spacing: 0.15em;
        color: #00a3e0;
        text-transform: uppercase;
        margin-bottom: 0.2rem;
    }
    .sintec-header h1 {
        font-size: 1.85rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
        letter-spacing: -0.025em;
    }
    .sintec-header p {
        font-size: 0.9rem;
        color: #e2e8f0;
        margin-top: 0.3rem;
        font-weight: 400;
    }

    /* KPI Cards SinTec Style */
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 1.1rem 1.3rem !important;
        box-shadow: 0 4px 10px rgba(10, 37, 64, 0.03) !important;
        position: relative !important;
        overflow: hidden !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(10, 37, 64, 0.08) !important;
    }
    div[data-testid="stMetric"]::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: #00a3e0;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        color: #0a2540 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.9rem !important;
        font-weight: 800 !important;
        color: #00a3e0 !important;
    }

    /* Styling Tabelle DataEditor */
    div[data-testid="stDataEditor"], div[data-testid="stDataFrame"] {
        background-color: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: 0 4px 12px rgba(10, 37, 64, 0.04) !important;
        padding: 6px !important;
    }

    /* Pulsanti d'Azione SinTec (Blu/Azzurro) */
    .stButton > button {
        background: linear-gradient(135deg, #0a2540 0%, #003366 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.6rem 1.25rem !important;
        box-shadow: 0 3px 8px rgba(10, 37, 64, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #003366 0%, #00a3e0 100%) !important;
        box-shadow: 0 5px 12px rgba(0, 163, 224, 0.3) !important;
        transform: translateY(-1px);
    }

    .stDownloadButton > button {
        background: linear-gradient(135deg, #00a3e0 0%, #0082b3 100%) !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0 3px 8px rgba(0, 163, 224, 0.2) !important;
    }

    /* Tabs Styling Clean */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
        border-bottom: 2px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 46px;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
        font-size: 0.95rem;
        color: #64748b;
        background-color: transparent;
        padding: 0 1.25rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #0a2540 !important;
        border-bottom: 3px solid #00a3e0 !important;
    }

    /* Container Filtri Expander */
    div[data-testid="stExpander"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 6px rgba(10, 37, 64, 0.02) !important;
    }
</style>
""", unsafe_allow_html=True)

DB_FILE = "manuali_progetti_db.csv"
BACKUP_DIR = "backups"
MAX_BACKUPS = 100

TECNICI = [
    "Non ancora assegnato",
    "Caselli Katia",
    "Lanzi Francesco",
    "Michela D'Alsazia",
    "Alessia Magno",
    "Camilla Petrò"
]

ATTIVITA_OPTIONS = [
    "Installation",
    "Spare parts / Maintenance",
    "Altro"
]

TIPO_ORDINE_OPTIONS = [
    "Preventivo",
    "Confermato"
]

PRIORITA_OPTIONS = [
    "Bassa",
    "Normale",
    "Alta",
    "🚨 Urgente"
]

ALL_COLUMNS = [
    "Nr. Commessa", "RDL", "Descrizione", "Tipo Ordine", "Attività", "Priorità", "Ore Valutate", "Responsabile", 
    "Stato", "Avanzamento (%)", "Modelli 3D dal", "Scadenza Prevista", "Nuova consegna prevista", "Spedizione Wittur", "Data Chiusura", "Percorso Cartella", "Note"
]

DEFAULT_ORDER = [
    "Nr. Commessa", "RDL", "Nuova consegna prevista", "Descrizione", "Priorità", "Attività", 
    "Tipo Ordine", "Ore Valutate", "Responsabile", "Stato", "Avanzamento (%)", "Modelli 3D dal", 
    "Scadenza Prevista", "Spedizione Wittur", "Data Chiusura", "Percorso Cartella", "Note"
]

DATE_COLUMNS = [
    "Modelli 3D dal", "Scadenza Prevista", "Nuova consegna prevista", "Spedizione Wittur", "Data Chiusura"
]

if "cols_order" not in st.session_state:
    st.session_state.cols_order = DEFAULT_ORDER
if "sort_column" not in st.session_state:
    st.session_state.sort_column = "Nuova consegna prevista"
if "sort_ascending" not in st.session_state:
    st.session_state.sort_ascending = True

def safe_parse_date(val):
    if pd.isnull(val) or val == "" or str(val).strip().lower() in ["nan", "none", "nat"]:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    val_str = str(val).strip()
    parsed = pd.to_datetime(val_str, dayfirst=True, errors="coerce")
    return parsed.date() if pd.notnull(parsed) else None

def create_automatic_backup():
    if os.path.exists(DB_FILE):
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"manuali_progetti_db_{timestamp}.csv")
        shutil.copy(DB_FILE, backup_path)
        backup_files = sorted(glob.glob(os.path.join(BACKUP_DIR, "manuali_progetti_db_*.csv")))
        if len(backup_files) > MAX_BACKUPS:
            for old_file in backup_files[:-MAX_BACKUPS]:
                try:
                    os.remove(old_file)
                except Exception:
                    pass

def auto_update_urgency(dataframe):
    today = date.today()
    if dataframe.empty:
        return dataframe
    for idx, row in dataframe.iterrows():
        prio_curr = str(row.get("Priorità", "")).strip()
        if prio_curr in ["Urgente", "🚨 Urgente"]:
            dataframe.at[idx, "Priorità"] = "🚨 Urgente"
        elif prio_curr not in PRIORITA_OPTIONS:
            dataframe.at[idx, "Priorità"] = "Normale"

        if row.get("Stato") != "Completato":
            d_consegna = safe_parse_date(row.get("Nuova consegna prevista"))
            if d_consegna and (d_consegna - today).days <= 14:
                dataframe.at[idx, "Priorità"] = "🚨 Urgente"
    return dataframe

def load_data():
    if not os.path.exists(DB_FILE):
        df_empty = pd.DataFrame(columns=ALL_COLUMNS)
        df_empty.to_csv(DB_FILE, index=False)
        return df_empty
    
    df = pd.read_csv(DB_FILE, dtype=str)
    if "Nuova consegna prevista iniziale" in df.columns:
        df.rename(columns={"Nuova consegna prevista iniziale": "Nuova consegna prevista"}, inplace=True)
    
    if not df.empty:
        for col in ALL_COLUMNS:
            if col not in df.columns:
                df[col] = ""
            elif col not in ["Ore Valutate", "Avanzamento (%)"] + DATE_COLUMNS:
                df[col] = df[col].fillna("").astype(str).str.strip()
        
        df = df[ALL_COLUMNS]
        df["Ore Valutate"] = pd.to_numeric(df["Ore Valutate"], errors="coerce").fillna(0.0)
        df["Avanzamento (%)"] = pd.to_numeric(df["Avanzamento (%)"], errors="coerce").fillna(0).astype(int)
        for dcol in DATE_COLUMNS:
            df[dcol] = df[dcol].apply(safe_parse_date)
        df = auto_update_urgency(df)
    else:
        df = pd.DataFrame(columns=ALL_COLUMNS)
    return df

def save_data_to_file(df_to_save):
    create_automatic_backup()
    df_disk = df_to_save[ALL_COLUMNS].copy()
    for dcol in DATE_COLUMNS:
        df_disk[dcol] = df_disk[dcol].apply(lambda x: x.strftime('%d/%m/%Y') if isinstance(x, (date, datetime)) else "")
    df_disk.to_csv(DB_FILE, index=False)

if "main_df" not in st.session_state:
    st.session_state.main_df = load_data()

# --- CALLBACK PER SALVATAGGIO AUTOMATICO CELLE ---
def handle_editor_change(key_editor, current_view_df):
    changes = st.session_state.get(key_editor, {})
    edited_rows = changes.get("edited_rows", {})
    if not edited_rows:
        return
        
    main_df = st.session_state.main_df.copy()
    has_updated = False
    
    for pos_str, row_changes in edited_rows.items():
        pos = int(pos_str)
        if pos < len(current_view_df):
            target_row = current_view_df.iloc[pos]
            c_num = target_row["Nr. Commessa"]
            c_rdl = target_row["RDL"]
            c_att = target_row.get("Attività", "")
            
            matches = main_df[
                (main_df["Nr. Commessa"].astype(str) == str(c_num)) & 
                (main_df["RDL"].astype(str) == str(c_rdl)) & 
                (main_df["Attività"].astype(str) == str(c_att))
            ]
            
            if not matches.empty:
                orig_idx = matches.index[0]
                for col_name, new_val in row_changes.items():
                    if col_name == "Seleziona":
                        continue
                    elif col_name in DATE_COLUMNS:
                        main_df.at[orig_idx, col_name] = safe_parse_date(new_val)
                    elif col_name == "Ore Valutate":
                        main_df.at[orig_idx, col_name] = float(pd.to_numeric(new_val, errors="coerce") or 0.0)
                    elif col_name == "Avanzamento (%)":
                        main_df.at[orig_idx, col_name] = int(pd.to_numeric(new_val, errors="coerce") or 0)
                    elif col_name == "Stato":
                        old_st = main_df.at[orig_idx, "Stato"]
                        main_df.at[orig_idx, col_name] = str(new_val)
                        if new_val == "Completato" and old_st != "Completato":
                            main_df.at[orig_idx, "Avanzamento (%)"] = 100
                            main_df.at[orig_idx, "Data Chiusura"] = date.today()
                        elif new_val != "Completato":
                            main_df.at[orig_idx, "Data Chiusura"] = None
                    else:
                        main_df.at[orig_idx, col_name] = str(new_val) if pd.notnull(new_val) else ""
                has_updated = True

    if has_updated:
        st.session_state.main_df = main_df
        save_data_to_file(main_df)
        st.toast("⚡ Modifica salvata automaticamente!", icon="💾")

# --- DIALOG POPUP PER EDITING SCHEDA SINGOLA ---
@st.dialog("✏️ Scheda Dettaglio & Modifica Commessa", width="large")
def edit_single_row_dialog(row_dict, orig_index):
    st.write(f"Modifica dettagliata per **Commessa: {row_dict.get('Nr. Commessa', '')}** | **RDL: {row_dict.get('RDL', '')}**")
    
    with st.form("form_edit_row_dialog"):
        col1, col2 = st.columns(2)
        with col1:
            nr_commessa = st.text_input("Nr. Commessa", value=str(row_dict.get("Nr. Commessa", "")))
            rdl = st.text_input("RDL / Titolo", value=str(row_dict.get("RDL", "")))
            descrizione = st.text_input("Descrizione", value=str(row_dict.get("Descrizione", "")))
            tipo_ord = st.selectbox("Tipo Ordine", options=TIPO_ORDINE_OPTIONS, index=TIPO_ORDINE_OPTIONS.index(row_dict.get("Tipo Ordine")) if row_dict.get("Tipo Ordine") in TIPO_ORDINE_OPTIONS else 1)
            attivita = st.selectbox("Attività", options=ATTIVITA_OPTIONS, index=ATTIVITA_OPTIONS.index(row_dict.get("Attività")) if row_dict.get("Attività") in ATTIVITA_OPTIONS else 0)
            priorita = st.selectbox("Priorità", options=PRIORITA_OPTIONS, index=PRIORITA_OPTIONS.index(row_dict.get("Priorità")) if row_dict.get("Priorità") in PRIORITA_OPTIONS else 1)
            ore_val = st.number_input("Ore Valutate", value=float(row_dict.get("Ore Valutate", 0.0)), step=0.5)

        with col2:
            resp_curr = [r.strip() for r in str(row_dict.get("Responsabile", "")).split(",") if r.strip() in TECNICI]
            responsabile_sel = st.multiselect("Responsabili Tecnici", options=TECNICI, default=resp_curr if resp_curr else ["Non ancora assegnato"])
            stato = st.selectbox("Stato", options=["Da iniziare", "In corso", "In revisione", "Completato"], index=["Da iniziare", "In corso", "In revisione", "Completato"].index(row_dict.get("Stato")) if row_dict.get("Stato") in ["Da iniziare", "In corso", "In revisione", "Completato"] else 0)
            avanzamento = st.slider("Avanzamento (%)", 0, 100, int(row_dict.get("Avanzamento (%)", 0)))
            
            d_3d = safe_parse_date(row_dict.get("Modelli 3D dal")) or date.today()
            d_scad = safe_parse_date(row_dict.get("Scadenza Prevista")) or date.today()
            d_nconsegna = safe_parse_date(row_dict.get("Nuova consegna prevista")) or date.today()
            d_wittur = safe_parse_date(row_dict.get("Spedizione Wittur")) or date.today()
            
            modelli_3d_dal = st.date_input("Modelli 3D dal", value=d_3d, format="DD/MM/YYYY")
            scadenza_prev = st.date_input("Scadenza Prevista", value=d_scad, format="DD/MM/YYYY")
            nuova_consegna = st.date_input("Nuova Consegna Prevista", value=d_nconsegna, format="DD/MM/YYYY")
            spedizione_wittur = st.date_input("Spedizione Wittur", value=d_wittur, format="DD/MM/YYYY")

        st.divider()
        percorso_cartella = st.text_input("Percorso Cartella Locale", value=str(row_dict.get("Percorso Cartella", "")))
        note = st.text_area("Note / Osservazioni", value=str(row_dict.get("Note", "")))
        
        save_btn = st.form_submit_button("💾 Salva Modifiche Commessa", use_container_width=True)
        if save_btn:
            main_df = st.session_state.main_df
            main_df.at[orig_index, "Nr. Commessa"] = nr_commessa.strip()
            main_df.at[orig_index, "RDL"] = rdl.strip()
            main_df.at[orig_index, "Descrizione"] = descrizione.strip()
            main_df.at[orig_index, "Tipo Ordine"] = tipo_ord
            main_df.at[orig_index, "Attività"] = attivita
            main_df.at[orig_index, "Priorità"] = priorita
            main_df.at[orig_index, "Ore Valutate"] = float(ore_val)
            main_df.at[orig_index, "Responsabile"] = ", ".join(responsabile_sel) if responsabile_sel else "Non ancora assegnato"
            
            old_st = main_df.at[orig_index, "Stato"]
            main_df.at[orig_index, "Stato"] = stato
            if stato == "Completato" and old_st != "Completato":
                main_df.at[orig_index, "Avanzamento (%)"] = 100
                main_df.at[orig_index, "Data Chiusura"] = date.today()
            elif stato != "Completato":
                main_df.at[orig_index, "Avanzamento (%)"] = avanzamento
                main_df.at[orig_index, "Data Chiusura"] = None

            main_df.at[orig_index, "Modelli 3D dal"] = modelli_3d_dal
            main_df.at[orig_index, "Scadenza Prevista"] = scadenza_prev
            main_df.at[orig_index, "Nuova consegna prevista"] = nuova_consegna
            main_df.at[orig_index, "Spedizione Wittur"] = spedizione_wittur
            main_df.at[orig_index, "Percorso Cartella"] = percorso_cartella.strip()
            main_df.at[orig_index, "Note"] = note.strip()
            
            st.session_state.main_df = main_df
            save_data_to_file(main_df)
            st.toast("✅ Commessa aggiornata con successo!", icon="💾")
            st.rerun()

# --- DIALOG POPUP PER DUPLICAZIONE ---
@st.dialog("📋 Duplica / Copia Nuova Commessa da Esistente", width="large")
def duplicate_single_row_dialog(row_dict):
    st.write(f"Copia dei dati da **Commessa originale: {row_dict.get('Nr. Commessa', '')}**")
    
    with st.form("form_duplicate_row_dialog"):
        col1, col2 = st.columns(2)
        with col1:
            nr_commessa = st.text_input("Nuovo Nr. Commessa*", value=f"{row_dict.get('Nr. Commessa', '')}_COPIA")
            rdl = st.text_input("RDL / Titolo*", value=str(row_dict.get("RDL", "")))
            descrizione = st.text_input("Descrizione", value=str(row_dict.get("Descrizione", "")))
            tipo_ord = st.selectbox("Tipo Ordine", options=TIPO_ORDINE_OPTIONS, index=TIPO_ORDINE_OPTIONS.index(row_dict.get("Tipo Ordine")) if row_dict.get("Tipo Ordine") in TIPO_ORDINE_OPTIONS else 1)
            attivita = st.selectbox("Attività", options=ATTIVITA_OPTIONS, index=ATTIVITA_OPTIONS.index(row_dict.get("Attività")) if row_dict.get("Attività") in ATTIVITA_OPTIONS else 0)
            priorita = st.selectbox("Priorità", options=PRIORITA_OPTIONS, index=PRIORITA_OPTIONS.index(row_dict.get("Priorità")) if row_dict.get("Priorità") in PRIORITA_OPTIONS else 1)
            ore_val = st.number_input("Ore Valutate", value=float(row_dict.get("Ore Valutate", 0.0)), step=0.5)

        with col2:
            resp_curr = [r.strip() for r in str(row_dict.get("Responsabile", "")).split(",") if r.strip() in TECNICI]
            responsabile_sel = st.multiselect("Responsabili Tecnici", options=TECNICI, default=resp_curr if resp_curr else ["Non ancora assegnato"])
            stato = st.selectbox("Stato Iniziale", options=["Da iniziare", "In corso", "In revisione", "Completato"], index=0)
            avanzamento = st.slider("Avanzamento Iniziale (%)", 0, 100, 0)
            
            d_3d = safe_parse_date(row_dict.get("Modelli 3D dal")) or date.today()
            d_scad = safe_parse_date(row_dict.get("Scadenza Prevista")) or date.today()
            d_nconsegna = safe_parse_date(row_dict.get("Nuova consegna prevista")) or date.today()
            d_wittur = safe_parse_date(row_dict.get("Spedizione Wittur")) or date.today()
            
            modelli_3d_dal = st.date_input("Modelli 3D dal", value=d_3d, format="DD/MM/YYYY")
            scadenza_prev = st.date_input("Scadenza Prevista", value=d_scad, format="DD/MM/YYYY")
            nuova_consegna = st.date_input("Nuova Consegna Prevista", value=d_nconsegna, format="DD/MM/YYYY")
            spedizione_wittur = st.date_input("Spedizione Wittur", value=d_wittur, format="DD/MM/YYYY")

        st.divider()
        percorso_cartella = st.text_input("Percorso Cartella Locale", value=str(row_dict.get("Percorso Cartella", "")))
        note = st.text_area("Note / Osservazioni", value=str(row_dict.get("Note", "")))
        
        save_dup_btn = st.form_submit_button("➕ Salva come Nuova Commessa Copiata", use_container_width=True)
        if save_dup_btn and nr_commessa and rdl:
            new_record = {
                "Nr. Commessa": nr_commessa.strip(),
                "RDL": rdl.strip(),
                "Descrizione": descrizione.strip(),
                "Tipo Ordine": tipo_ord,
                "Attività": attivita,
                "Priorità": priorita,
                "Ore Valutate": float(ore_val),
                "Responsabile": ", ".join(responsabile_sel) if responsabile_sel else "Non ancora assegnato",
                "Stato": stato,
                "Avanzamento (%)": 100 if stato == "Completato" else avanzamento,
                "Modelli 3D dal": modelli_3d_dal,
                "Scadenza Prevista": scadenza_prev,
                "Nuova consegna prevista": nuova_consegna,
                "Spedizione Wittur": spedizione_wittur,
                "Data Chiusura": date.today() if stato == "Completato" else None,
                "Percorso Cartella": percorso_cartella.strip(),
                "Note": note.strip()
            }
            
            main_df = pd.concat([st.session_state.main_df, pd.DataFrame([new_record])], ignore_index=True)
            st.session_state.main_df = main_df
            save_data_to_file(main_df)
            st.toast(f"✅ Nuova commessa '{nr_commessa}' creata con successo!", icon="📋")
            st.rerun()

# --- DIALOG POPUP CONFERMA ELIMINAZIONE ---
@st.dialog("🗑️ Conferma Eliminazione Commessa")
def delete_single_row_dialog(row_dict, orig_index):
    st.error(f"⚠️ Sei sicuro di voler eliminare la commessa **{row_dict.get('Nr. Commessa', '')}** ({row_dict.get('RDL', '')})?")
    st.write("Questa operazione rimuoverà la riga dal database (verrà comunque salvato un backup automatico).")
    
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("🔴 Sì, Elimina Definitivamente", type="primary", use_container_width=True):
            main_df = st.session_state.main_df.drop(index=orig_index).reset_index(drop=True)
            st.session_state.main_df = main_df
            save_data_to_file(main_df)
            st.toast("🗑️ Commessa eliminata con successo!", icon="🗑️")
            st.rerun()
            
    with col_cancel:
        if st.button("Annulla", use_container_width=True):
            st.rerun()

@st.dialog("📊 Dettaglio Attività", width="large")
def show_kpi_details(title, sub_df):
    st.subheader(f"{title} ({len(sub_df)})")
    if sub_df.empty:
        st.info("Nessuna attività presente in questa categoria.")
    else:
        display_cols = [
            "Nr. Commessa", "RDL", "Nuova consegna prevista", "Descrizione", "Priorità", "Attività", 
            "Tipo Ordine", "Ore Valutate", "Responsabile", "Stato", 
            "Avanzamento (%)", "Scadenza Prevista", "Spedizione Wittur", "Note"
        ]
        cols_to_show = [c for c in display_cols if c in sub_df.columns]
        
        dialog_col_config = {
            "Nuova consegna prevista": st.column_config.DateColumn("Nuova consegna", format="DD/MM/YYYY"),
            "Modelli 3D dal": st.column_config.DateColumn("Modelli 3D dal", format="DD/MM/YYYY"),
            "Scadenza Prevista": st.column_config.DateColumn("Scadenza Prevista", format="DD/MM/YYYY"),
            "Spedizione Wittur": st.column_config.DateColumn("Spedizione Wittur", format="DD/MM/YYYY"),
            "Data Chiusura": st.column_config.DateColumn("Data Chiusura", format="DD/MM/YYYY"),
        }
        
        st.dataframe(
            sub_df[cols_to_show], 
            use_container_width=True, 
            hide_index=True,
            column_config=dialog_col_config
        )

@st.dialog("🔄 Ripristina Backup")
def restore_backup_dialog():
    backup_files = sorted(glob.glob(os.path.join(BACKUP_DIR, "manuali_progetti_db_*.csv")), reverse=True)
    if not backup_files:
        st.info("Nessun backup disponibile.")
        return

    options = {}
    for f in backup_files:
        filename = os.path.basename(f)
        try:
            raw_ts = filename.replace("manuali_progetti_db_", "").replace(".csv", "")
            dt_obj = datetime.strptime(raw_ts, "%Y%m%d_%H%M%S")
            label = dt_obj.strftime("Backup del %d/%m/%Y ore %H:%M:%S")
        except Exception:
            label = filename
        options[label] = f

    selected_label = st.selectbox("Seleziona versione:", list(options.keys()))
    selected_file = options[selected_label]

    st.warning("⚠️ **ATTENZIONE:** Il ripristino sovrascriverà i dati attuali!")
    
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("🔴 Conferma Ripristino", type="primary", use_container_width=True):
            create_automatic_backup()
            shutil.copy(selected_file, DB_FILE)
            st.session_state.main_df = load_data()
            st.toast("✅ Database ripristinato!", icon="🔄")
            st.rerun()
            
    with col_cancel:
        if st.button("Annulla", use_container_width=True):
            st.rerun()

def generate_printable_html(df_to_print, title):
    cols = ["Nr. Commessa", "RDL", "Nuova consegna prevista", "Descrizione", "Priorità", "Attività", "Tipo Ordine", "Ore Valutate", "Responsabile", "Stato", "Avanzamento (%)", "Scadenza Prevista", "Spedizione Wittur"]
    df_clean = df_to_print[[c for c in cols if c in df_to_print.columns]].copy()
    for dcol in DATE_COLUMNS:
        if dcol in df_clean.columns:
            df_clean[dcol] = df_clean[dcol].apply(lambda x: x.strftime('%d/%m/%Y') if isinstance(x, (date, datetime)) else "")
    html_table = df_clean.to_html(index=False, classes="print-table")
    return f"""
    <!DOCTYPE html><html><head><meta charset="utf-8"><title>{title}</title>
    <style>
        body {{ font-family: Inter, Arial, sans-serif; margin: 20px; color: #333; }}
        h2 {{ text-align: center; margin-bottom: 5px; color: #0a2540; }}
        p.date {{ text-align: center; font-size: 12px; color: #666; margin-bottom: 20px; }}
        table.print-table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
        table.print-table th, table.print-table td {{ border: 1px solid #cbd5e1; padding: 6px 8px; text-align: left; }}
        table.print-table th {{ background-color: #0a2540; color: #ffffff; font-weight: bold; }}
        table.print-table tr:nth-child(even) {{ background-color: #f8fafc; }}
    </style></head>
    <body onload="window.print()"><h2>{title}</h2><p class="date">Data stampa: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>{html_table}</body></html>
    """

def convert_df_to_excel(df_to_export):
    df_clean = df_to_export[[c for c in ALL_COLUMNS if c in df_to_export.columns]].copy()
    for dcol in DATE_COLUMNS:
        if dcol in df_clean.columns:
            df_clean[dcol] = df_clean[dcol].apply(lambda x: x.strftime('%d/%m/%Y') if isinstance(x, (date, datetime)) else "")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_clean.to_excel(writer, index=False, sheet_name='Commesse')
    return output.getvalue()

# --- HEADER SINTEC BRAND ---
st.markdown("""
<div class='sintec-header'>
    <div class='sintec-brand'>SinTec S.r.l. • Soluzioni Tecniche</div>
    <h1>⚙️ Gestione Manuali & Commesse</h1>
    <p>Piattaforma operativa per Progettazione Meccanica, Manualistica Tecnica & Documentazione</p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.header("⚙️ Opzioni & Colonne")
selected_cols = st.sidebar.multiselect("Colonne visibili:", options=DEFAULT_ORDER, default=st.session_state.cols_order)
if selected_cols:
    st.session_state.cols_order = selected_cols

st.sidebar.divider()
st.sidebar.header("➕ Nuova Commessa")
with st.sidebar.form("form_nuovo_progetto", clear_on_submit=True):
    codice = st.text_input("Nr. Commessa*")
    rdl_val = st.text_input("RDL / Titolo*")
    descrizione_val = st.text_input("Descrizione Commessa")
    tipo_ordine = st.radio("Tipo Ordine*", TIPO_ORDINE_OPTIONS, index=1, horizontal=True)
    attivita_selezionate = st.multiselect("Attività*", options=ATTIVITA_OPTIONS, default=["Installation"])
    priorita = st.selectbox("Priorità*", PRIORITA_OPTIONS, index=1)
    ore_valutate = st.number_input("Ore Valutate", min_value=0.0, step=0.5)
    responsabili_sel = st.multiselect("Tecnici", options=TECNICI, default=["Non ancora assegnato"])
    stato = st.selectbox("Stato Iniziale", ["Da iniziare", "In corso", "In revisione", "Completato"])
    avanzamento = st.slider("Avanzamento (%)", 0, 100, 0, step=5)
    modelli_3d_dal = st.date_input("Modelli 3D dal", value=date.today(), format="DD/MM/YYYY")
    scadenza = st.date_input("Scadenza Prevista", value=date.today(), format="DD/MM/YYYY")
    nuova_consegna = st.date_input("Nuova consegna prevista", value=date.today(), format="DD/MM/YYYY")
    spedizione_wittur = st.date_input("Spedizione Wittur", value=date.today(), format="DD/MM/YYYY")
    cartella = st.text_input("Percorso Cartella Locale")
    note = st.text_area("Note")
    
    submitted = st.form_submit_button("Salva Commessa", use_container_width=True)
    if submitted and codice and rdl_val:
        if not attivita_selezionate:
            attivita_selezionate = ["Altro"]
        resp_stringa = ", ".join([r for r in responsabili_sel if r]) if responsabili_sel else "Non ancora assegnato"
        today_val = date.today() if stato == "Completato" else None
        if stato != "Completato" and (nuova_consegna - date.today()).days <= 14:
            priorita = "🚨 Urgente"

        new_rows = []
        for att in attivita_selezionate:
            new_rows.append({
                "Nr. Commessa": str(codice).strip(),
                "RDL": str(rdl_val).strip(),
                "Descrizione": str(descrizione_val).strip(),
                "Tipo Ordine": tipo_ordine,
                "Attività": att,
                "Priorità": priorita,
                "Ore Valutate": float(ore_valutate / len(attivita_selezionate) if len(attivita_selezionate) > 1 else ore_valutate),
                "Responsabile": resp_stringa,
                "Stato": stato,
                "Avanzamento (%)": int(100 if stato == "Completato" else avanzamento),
                "Modelli 3D dal": modelli_3d_dal,
                "Scadenza Prevista": scadenza,
                "Nuova consegna prevista": nuova_consegna,
                "Spedizione Wittur": spedizione_wittur,
                "Data Chiusura": today_val,
                "Percorso Cartella": str(cartella).strip(),
                "Note": str(note).strip()
            })
            
        st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame(new_rows)], ignore_index=True)
        save_data_to_file(st.session_state.main_df)
        st.sidebar.success(f"Aggiunta commessa '{codice}'!")
        st.rerun()

st.sidebar.divider()
if st.sidebar.button("🔄 Ripristina Backup", use_container_width=True):
    restore_backup_dialog()

# --- DATAFRAME CORRENTE ---
df = st.session_state.main_df

# --- ANALISI CRITICITÀ CON BANNER CLICCABILI ---
today_ts = date.today()
if not df.empty:
    progetti_in_ritardo = df[
        (df["Stato"] != "Completato") & 
        (df["Nuova consegna prevista"].apply(lambda x: isinstance(x, date) and x < today_ts))
    ]
    progetti_urgenti = df[
        (df["Stato"] != "Completato") & 
        (df["Priorità"].str.contains("Urgente", case=False, na=False))
    ]
else:
    progetti_in_ritardo = pd.DataFrame()
    progetti_urgenti = pd.DataFrame()

if not progetti_in_ritardo.empty or not progetti_urgenti.empty:
    c_warn1, c_warn2 = st.columns(2)
    with c_warn1:
        if not progetti_in_ritardo.empty:
            btn_ritardo_label = f"🚨 ATTENZIONE: {len(progetti_in_ritardo)} Commessa/e in Ritardo (Clicca per aprire la tabella)"
            if st.button(btn_ritardo_label, key="btn_open_dialog_ritardi", use_container_width=True):
                show_kpi_details("🚨 Commesse in Ritardo sulla Nuova Consegna", progetti_in_ritardo)
    with c_warn2:
        if not progetti_urgenti.empty:
            btn_urgenti_label = f"🔥 URGENTI: {len(progetti_urgenti)} Ordini in Scadenza (Clicca per aprire la tabella)"
            if st.button(btn_urgenti_label, key="btn_open_dialog_urgenti", use_container_width=True):
                show_kpi_details("🔥 Ordini e Commesse Urgenti", progetti_urgenti)

# --- KPI METRICS SINTEC ---
k1, k2, k3, k4 = st.columns(4)

df_totale = df.copy() if not df.empty else pd.DataFrame()
df_prev = df[df["Tipo Ordine"] == "Preventivo"].copy() if not df.empty else pd.DataFrame()
df_conf = df[df["Tipo Ordine"] == "Confermato"].copy() if not df.empty else pd.DataFrame()
df_urg = df[(df["Priorità"].str.contains("Urgente", case=False, na=False)) & (df["Stato"] != "Completato")].copy() if not df.empty else pd.DataFrame()

with k1:
    st.metric(label="TOTALE ATTIVITÀ", value=len(df_totale))
    if st.button("🔍 Apri Totali", key="btn_kpi_tot", use_container_width=True):
        show_kpi_details("Tutte le Attività", df_totale)

with k2:
    st.metric(label="PREVENTIVI 📋", value=len(df_prev))
    if st.button("📋 Apri Preventivi", key="btn_kpi_prev", use_container_width=True):
        show_kpi_details("Elenco Preventivi", df_prev)

with k3:
    st.metric(label="CONFERMATI ✅", value=len(df_conf))
    if st.button("✅ Apri Confermati", key="btn_kpi_conf", use_container_width=True):
        show_kpi_details("Elenco Ordini Confermati", df_conf)

with k4:
    st.metric(label="URGENTI / SCADUTI 🔥", value=len(df_urg))
    if st.button("🔥 Apri Urgenti", key="btn_kpi_urg", use_container_width=True):
        show_kpi_details("Elenco Attività Urgenti", df_urg)

st.divider()

# --- FILTRI & ORDINAMENTO ---
if not df.empty:
    with st.expander("🔍 **Filtri & Ordinamento Tabelle**", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns([2, 1, 1, 1])
        with f_col1: search_query = st.text_input("🔍 Cerca testo (Commessa, RDL, Note...):", "")
        with f_col2: filtro_tecnico = st.multiselect("Tecnico:", options=TECNICI)
        with f_col3: filtro_attivita = st.multiselect("Attività:", options=ATTIVITA_OPTIONS)
        with f_col4: filtro_prio = st.multiselect("Priorità:", options=PRIORITA_OPTIONS)

        available_sort_cols = [c for c in DEFAULT_ORDER if c in st.session_state.cols_order]
        if "Nuova consegna prevista" in available_sort_cols:
            available_sort_cols.remove("Nuova consegna prevista")
            available_sort_cols.insert(0, "Nuova consegna prevista")

        s_col1, s_col2 = st.columns([3, 1])
        with s_col1:
            sort_col_selected = st.selectbox(
                "Ordina per colonna:",
                options=available_sort_cols,
                index=available_sort_cols.index(st.session_state.sort_column) if st.session_state.sort_column in available_sort_cols else 0
            )
            st.session_state.sort_column = sort_col_selected
        with s_col2:
            sort_order = st.radio("Ordine:", options=["Crescente ⬆️", "Decrescente ⬇️"], horizontal=True)
            st.session_state.sort_ascending = (sort_order == "Crescente ⬆️")

# --- TABELLE PRINCIPALI ---
tab_operativa, tab_completati, tab_reports = st.tabs(["📋 Attività In Corso", "✅ Archivio Completati", "📊 Reportistica & Analytics"])

col_config = {
    "Seleziona": st.column_config.CheckboxColumn("📌", default=False),
    "Nr. Commessa": st.column_config.TextColumn("Nr. Commessa"),
    "RDL": st.column_config.TextColumn("RDL", pinned=True),
    "Nuova consegna prevista": st.column_config.DateColumn("Nuova Consegna", format="DD/MM/YYYY"),
    "Descrizione": st.column_config.TextColumn("Descrizione"),
    "Priorità": st.column_config.SelectboxColumn("Priorità", options=PRIORITA_OPTIONS, required=True),
    "Attività": st.column_config.SelectboxColumn("Attività", options=ATTIVITA_OPTIONS, required=True),
    "Tipo Ordine": st.column_config.SelectboxColumn("Tipo Ordine", options=TIPO_ORDINE_OPTIONS, required=True),
    "Responsabile": st.column_config.SelectboxColumn("Responsabile Tecnico", options=TECNICI, required=True),
    "Stato": st.column_config.SelectboxColumn("Stato", options=["Da iniziare", "In corso", "In revisione", "Completato"], required=True),
    "Avanzamento (%)": st.column_config.ProgressColumn("Avanzamento", min_value=0, max_value=100, format="%d%%"),
    "Modelli 3D dal": st.column_config.DateColumn("Modelli 3D dal", format="DD/MM/YYYY"),
    "Scadenza Prevista": st.column_config.DateColumn("Scadenza Prevista", format="DD/MM/YYYY"),
    "Spedizione Wittur": st.column_config.DateColumn("Spedizione Wittur", format="DD/MM/YYYY"),
    "Data Chiusura": st.column_config.DateColumn("Data Chiusura", format="DD/MM/YYYY"),
    "Percorso Cartella": st.column_config.TextColumn("Cartella Locale"),
    "Ore Valutate": st.column_config.NumberColumn("Ore Val.", format="%.1f")
}

if not df.empty:
    df_base = df.copy()
    if search_query:
        mask = df_base.astype(str).apply(lambda row: row.str.contains(search_query, case=False, na=False)).any(axis=1)
        df_base = df_base[mask]
    if filtro_tecnico:
        pattern = "|".join([rf"\b{tec}\b" for tec in filtro_tecnico])
        df_base = df_base[df_base["Responsabile"].astype(str).str.contains(pattern, case=False, na=False)]
    if filtro_attivita:
        df_base = df_base[df_base["Attività"].isin(filtro_attivita)]
    if filtro_prio:
        df_base = df_base[df_base["Priorità"].isin(filtro_prio)]

    def prepare_view(target_df):
        target_df = target_df.copy()
        if st.session_state.sort_column in target_df.columns:
            target_df = target_df.sort_values(
                by=st.session_state.sort_column, 
                ascending=st.session_state.sort_ascending, 
                na_position='last'
            )
        target_df.insert(0, "Seleziona", False)
        return target_df

    df_attivi = prepare_view(df_base[df_base["Stato"] != "Completato"])
    df_completati = prepare_view(df_base[df_base["Stato"] == "Completato"])

    # --- TAB 1: ATTIVITÀ IN CORSO ---
    with tab_operativa:
        if not df_attivi.empty:
            view_attivi = df_attivi[["Seleziona"] + st.session_state.cols_order].copy()
            
            edited_attivi = st.data_editor(
                view_attivi,
                num_rows="dynamic",
                use_container_width=True,
                column_config=col_config,
                hide_index=True,
                key="editor_attivi",
                on_change=handle_editor_change,
                args=("editor_attivi", view_attivi)
            )

            # Rilevamento spunta prima colonna "Seleziona"
            selected_rows = edited_attivi[edited_attivi["Seleziona"] == True]
            if not selected_rows.empty:
                row_selected = selected_rows.iloc[0]
                c_num = row_selected["Nr. Commessa"]
                c_rdl = row_selected["RDL"]
                c_att = row_selected.get("Attività", "")
                orig_matches = st.session_state.main_df[
                    (st.session_state.main_df["Nr. Commessa"].astype(str) == str(c_num)) & 
                    (st.session_state.main_df["RDL"].astype(str) == str(c_rdl)) & 
                    (st.session_state.main_df["Attività"].astype(str) == str(c_att))
                ]
                if not orig_matches.empty:
                    orig_index = orig_matches.index[0]
                    st.info(f"📍 Commessa selezionata: **{c_num}** - *{c_rdl}*")
                    col_action1, col_action2, col_action3 = st.columns(3)
                    with col_action1:
                        if st.button("✏️ Apri & Modifica Scheda", key="btn_open_editor_attivi", use_container_width=True):
                            edit_single_row_dialog(row_selected.to_dict(), orig_index)
                    with col_action2:
                        if st.button("📋 Duplica / Copia Commessa", key="btn_open_duplicate_attivi", use_container_width=True):
                            duplicate_single_row_dialog(row_selected.to_dict())
                    with col_action3:
                        if st.button("🗑️ Elimina Commessa", key="btn_open_delete_attivi", use_container_width=True):
                            delete_single_row_dialog(row_selected.to_dict(), orig_index)

            st.divider()
            b1, b2 = st.columns([1, 1.3])
            with b1:
                excel_data_attivi = convert_df_to_excel(df_attivi)
                st.download_button("📥 Scarica Excel", data=excel_data_attivi, file_name=f"Attivita_In_Corso_{date.today().strftime('%d_%m_%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            with b2:
                html_print_attivi = generate_printable_html(df_attivi, "Tabella Attività In Corso")
                st.download_button("🖨️ Stampa / PDF", data=html_print_attivi, file_name=f"Stampa_Attivita_In_Corso_{date.today().strftime('%d_%m_%Y')}.html", mime="text/html", use_container_width=True)
        else:
            st.info("Nessuna attività in corso con i filtri selezionati.")

    # --- TAB 2: ARCHIVIO COMPLETATI ---
    with tab_completati:
        if not df_completati.empty:
            view_comp = df_completati[["Seleziona"] + st.session_state.cols_order].copy()
            
            edited_comp = st.data_editor(
                view_comp,
                num_rows="dynamic",
                use_container_width=True,
                column_config=col_config,
                hide_index=True,
                key="editor_completati",
                on_change=handle_editor_change,
                args=("editor_completati", view_comp)
            )

            selected_rows_comp = edited_comp[edited_comp["Seleziona"] == True]
            if not selected_rows_comp.empty:
                row_selected_comp = selected_rows_comp.iloc[0]
                c_num = row_selected_comp["Nr. Commessa"]
                c_rdl = row_selected_comp["RDL"]
                c_att = row_selected_comp.get("Attività", "")
                orig_matches_comp = st.session_state.main_df[
                    (st.session_state.main_df["Nr. Commessa"].astype(str) == str(c_num)) & 
                    (st.session_state.main_df["RDL"].astype(str) == str(c_rdl)) & 
                    (st.session_state.main_df["Attività"].astype(str) == str(c_att))
                ]
                if not orig_matches_comp.empty:
                    orig_index_comp = orig_matches_comp.index[0]
                    st.info(f"📍 Commessa selezionata: **{c_num}** - *{c_rdl}*")
                    col_action_comp1, col_action_comp2, col_action_comp3 = st.columns(3)
                    with col_action_comp1:
                        if st.button("✏️ Apri & Modifica Scheda", key="btn_open_editor_comp", use_container_width=True):
                            edit_single_row_dialog(row_selected_comp.to_dict(), orig_index_comp)
                    with col_action_comp2:
                        if st.button("📋 Duplica / Copia Commessa", key="btn_open_duplicate_comp", use_container_width=True):
                            duplicate_single_row_dialog(row_selected_comp.to_dict())
                    with col_action_comp3:
                        if st.button("🗑️ Elimina Commessa", key="btn_open_delete_comp", use_container_width=True):
                            delete_single_row_dialog(row_selected_comp.to_dict(), orig_index_comp)

            st.divider()
            c1, c2 = st.columns([1, 1.3])
            with c1:
                excel_data_comp = convert_df_to_excel(df_completati)
                st.download_button("📥 Scarica Excel", data=excel_data_comp, file_name=f"Archivio_Completati_{date.today().strftime('%d_%m_%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            with c2:
                html_print_comp = generate_printable_html(df_completati, "Tabella Attività Completate")
                st.download_button("🖨️ Stampa / PDF", data=html_print_comp, file_name=f"Stampa_Archivio_Completati_{date.today().strftime('%d_%m_%Y')}.html", mime="text/html", use_container_width=True)
        else:
            st.info("Nessuna attività completata con i filtri selezionati.")

# --- TAB 3: REPORTISTICA ---
with tab_reports:
    st.subheader("📈 Analisi e Distribuzione Carico Lavoro")
    if df.empty:
        st.info("Nessun dato disponibile.")
    else:
        df_rep = df.copy()
        df_rep["Ore Valutate"] = pd.to_numeric(df_rep["Ore Valutate"], errors="coerce").fillna(0.0)
        
        r_k1, r_k2, r_k3, r_k4 = st.columns(4)
        r_k1.metric("Ore Totali Valutate", f"{df_rep['Ore Valutate'].sum():.1f} h")
        r_k2.metric("Ore Residue (In Corso)", f"{df_rep[df_rep['Stato'] != 'Completato']['Ore Valutate'].sum():.1f} h")
        r_k3.metric("Commesse Attive", len(df_rep[df_rep['Stato'] != 'Completato']))
        r_k4.metric("Commesse Completate", len(df_rep[df_rep['Stato'] == 'Completato']))
        
        st.divider()
        rep_col1, rep_col2 = st.columns(2)
        with rep_col1:
            st.write("### 👥 Attività per Tecnico Responsabile")
            tec_counts = df_rep[df_rep["Stato"] != "Completato"]["Responsabile"].value_counts().reset_index()
            tec_counts.columns = ["Tecnico", "Numero Attività"]
            st.bar_chart(data=tec_counts, x="Tecnico", y="Numero Attività")
        with rep_col2:
            st.write("### ⏱️ Carico Ore per Tecnico (Attività In Corso)")
            ore_tec = df_rep[df_rep["Stato"] != "Completato"].groupby("Responsabile")["Ore Valutate"].sum().reset_index()
            ore_tec.columns = ["Tecnico", "Ore Totali"]
            st.bar_chart(data=ore_tec, x="Tecnico", y="Ore Totali")
