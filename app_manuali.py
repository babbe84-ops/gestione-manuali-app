import streamlit as st
import pandas as pd
from datetime import date, datetime
import os
import io
import glob
import shutil

st.set_page_config(
    page_title="Gestione Manuali & Commesse", 
    layout="wide", 
    page_icon="📚",
    initial_sidebar_state="collapsed"
)

# --- STYLING CSS CLEAN & BUTTONS HI-VIS ---
st.markdown("""
<style>
    .stApp {
        background-color: #f1f5f9;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .main-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 0.1rem;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 1.2rem;
    }
    .stButton > button {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 0.55rem 1rem !important;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2) !important;
    }
    .stDownloadButton > button {
        background-color: #0f766e !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
    }
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
</style>
""", unsafe_allow_html=True)

DB_FILE = "manuali_progetti_db.csv"
BACKUP_DIR = "backups"
MAX_BACKUPS = 100
TARGET_FOLDER = r"X:\caselli\Wittur\MANUALI DA FARE"

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
        if row.get("Stato") != "Completato":
            d_consegna = safe_parse_date(row.get("Nuova consegna prevista"))
            if d_consegna and (d_consegna - today).days <= 14:
                dataframe.at[idx, "Priorità"] = "🚨 Urgente"
        if str(row.get("Priorità")).strip() in ["Urgente", "🚨 Urgente"]:
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
        df_disk[dcol] = df_disk[dcol].apply(lambda x: x.strftime('%Y-%m-%d') if isinstance(x, (date, datetime)) else "")
    df_disk.to_csv(DB_FILE, index=False)

if "main_df" not in st.session_state:
    st.session_state.main_df = load_data()

def process_and_save_editor(key_editor, current_view_df):
    editor_state = st.session_state.get(key_editor, {})
    main_df = st.session_state.main_df.copy()

    # 1. Cancellazione righe
    deleted_positions = editor_state.get("deleted_rows", [])
    if deleted_positions:
        indices_to_drop = current_view_df.iloc[deleted_positions].index
        main_df = main_df.drop(index=indices_to_drop, errors="ignore")

    # 2. Modifica celle
    edited_rows = editor_state.get("edited_rows", {})
    if edited_rows:
        for pos_str, changes in edited_rows.items():
            pos = int(pos_str) if isinstance(pos_str, str) else pos_str
            orig_idx = current_view_df.index[pos]
            if orig_idx in main_df.index:
                for col_name, new_val in changes.items():
                    if col_name in DATE_COLUMNS:
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

    # 3. Nuove righe
    added_rows = editor_state.get("added_rows", [])
    if added_rows:
        new_records = []
        for a_row in added_rows:
            rec = {col: a_row.get(col, "") for col in ALL_COLUMNS}
            new_records.append(rec)
        main_df = pd.concat([main_df, pd.DataFrame(new_records)], ignore_index=True)

    main_df = auto_update_urgency(main_df)
    st.session_state.main_df = main_df
    save_data_to_file(main_df)

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
        body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
        h2 {{ text-align: center; margin-bottom: 5px; }}
        p.date {{ text-align: center; font-size: 12px; color: #666; margin-bottom: 20px; }}
        table.print-table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
        table.print-table th, table.print-table td {{ border: 1px solid #ccc; padding: 6px 8px; text-align: left; }}
        table.print-table th {{ background-color: #f2f2f2; font-weight: bold; }}
        table.print-table tr:nth-child(even) {{ background-color: #f1f5f9; }}
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

def export_directly_to_target(df_to_export, filename):
    if not os.path.exists(TARGET_FOLDER):
        try:
            os.makedirs(TARGET_FOLDER)
        except Exception as e:
            return False, f"Impossibile accedere alla cartella: {e}"
    file_path = os.path.join(TARGET_FOLDER, filename)
    df_clean = df_to_export[[c for c in ALL_COLUMNS if c in df_to_export.columns]].copy()
    for dcol in DATE_COLUMNS:
        if dcol in df_clean.columns:
            df_clean[dcol] = df_clean[dcol].apply(lambda x: x.strftime('%d/%m/%Y') if isinstance(x, (date, datetime)) else "")
    try:
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df_clean.to_excel(writer, index=False, sheet_name='Commesse')
        return True, file_path
    except Exception as e:
        return False, str(e)

# --- HEADER APP ---
st.markdown("<div class='main-title'>📚 Gestione Manuali & Commesse</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Piattaforma di tracciamento commesse & documentazione tecnica</div>", unsafe_allow_html=True)

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
        st.session_state.main_df = auto_update_urgency(st.session_state.main_df)
        save_data_to_file(st.session_state.main_df)
        st.sidebar.success(f"Aggiunta commessa '{codice}'!")
        st.rerun()

# --- DATAFRAME CORRENTE ---
df = st.session_state.main_df

# --- ANALISI CRITICITÀ ---
today_ts = date.today()
if not df.empty:
    progetti_in_ritardo = df[(df["Stato"] != "Completato") & (df["Scadenza Prevista"].apply(lambda x: isinstance(x, date) and x < today_ts))]
    progetti_urgenti = df[(df["Stato"] != "Completato") & (df["Priorità"].str.contains("Urgente", case=False, na=False))]
else:
    progetti_in_ritardo = pd.DataFrame()
    progetti_urgenti = pd.DataFrame()

if not progetti_in_ritardo.empty or not progetti_urgenti.empty:
    c_warn1, c_warn2 = st.columns(2)
    with c_warn1:
        if not progetti_in_ritardo.empty:
            st.error(f"🚨 **{len(progetti_in_ritardo)} Attività in Ritardo**")
            for idx, row in progetti_in_ritardo.iterrows():
                scad_val = row['Scadenza Prevista']
                scad_str = scad_val.strftime('%d/%m/%Y') if isinstance(scad_val, date) else ""
                st.caption(f"• **{row['Nr. Commessa']}** - {row['RDL']} (Scaduta: {scad_str})")
    with c_warn2:
        if not progetti_urgenti.empty:
            st.warning(f"🔥 **{len(progetti_urgenti)} Ordini URGENTI in Corso**")
            for idx, row in progetti_urgenti.iterrows():
                st.caption(f"• **{row['Nr. Commessa']}** - {row['RDL']} ({row['Responsabile']})")

# --- KPI METRICS CON PULSANTI DI APERTURA DETTAGLIO ---
k1, k2, k3, k4 = st.columns(4)

df_totale = df.copy() if not df.empty else pd.DataFrame()
df_prev = df[df["Tipo Ordine"] == "Preventivo"].copy() if not df.empty else pd.DataFrame()
df_conf = df[df["Tipo Ordine"] == "Confermato"].copy() if not df.empty else pd.DataFrame()
df_urg = df[(df["Priorità"].str.contains("Urgente", case=False, na=False)) & (df["Stato"] != "Completato")].copy() if not df.empty else pd.DataFrame()

with k1:
    st.metric(label="Totale Attività", value=len(df_totale))
    if st.button("🔍 Apri Totali", key="btn_kpi_tot", use_container_width=True):
        show_kpi_details("Tutte le Attività", df_totale)

with k2:
    st.metric(label="Preventivi 📋", value=len(df_prev))
    if st.button("📋 Apri Preventivi", key="btn_kpi_prev", use_container_width=True):
        show_kpi_details("Elenco Preventivi", df_prev)

with k3:
    st.metric(label="Confermati ✅", value=len(df_conf))
    if st.button("✅ Apri Confermati", key="btn_kpi_conf", use_container_width=True):
        show_kpi_details("Elenco Ordini Confermati", df_conf)

with k4:
    st.metric(label="Urgenti 🔥", value=len(df_urg))
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
    "Nr. Commessa": st.column_config.TextColumn("Nr. Commessa"),
    "RDL": st.column_config.TextColumn("RDL", pinned=True),
    "Nuova consegna prevista": st.column_config.DateColumn("Nuova consegna", format="DD/MM/YYYY"),
    "Descrizione": st.column_config.TextColumn("Descrizione"),
    "Priorità": st.column_config.SelectboxColumn("Priorità", options=PRIORITA_OPTIONS, required=True),
    "Attività": st.column_config.SelectboxColumn("Attività", options=ATTIVITA_OPTIONS, required=True),
    "Tipo Ordine": st.column_config.SelectboxColumn("Tipo Ordine", options=TIPO_ORDINE_OPTIONS, required=True),
    "Responsabile": st.column_config.TextColumn("Responsabile Tecnico"),
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
        return target_df

    df_attivi = prepare_view(df_base[df_base["Stato"] != "Completato"])
    df_completati = prepare_view(df_base[df_base["Stato"] == "Completato"])

    # --- TAB 1: ATTIVITÀ IN CORSO ---
    with tab_operativa:
        if not df_attivi.empty:
            view_attivi = df_attivi[st.session_state.cols_order].copy()
            st.data_editor(
                view_attivi,
                num_rows="dynamic",
                use_container_width=True,
                column_config=col_config,
                hide_index=True,
                key="editor_attivi"
            )

            b0, b1, b2, b3 = st.columns([1.5, 1, 1.2, 1.3])
            with b0:
                if st.button("💾 Salva Modifiche", key="btn_save_attivi", use_container_width=True):
                    process_and_save_editor("editor_attivi", view_attivi)
                    st.toast("✅ Modifiche salvate con successo!", icon="💾")
                    st.rerun()
            with b1:
                excel_data_attivi = convert_df_to_excel(df_attivi)
                st.download_button("📥 Scarica Excel", data=excel_data_attivi, file_name=f"Attivita_In_Corso_{date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            with b2:
                if st.button("📁 Salva in Wittur", key="btn_wittur_attivi", use_container_width=True):
                    ok, res = export_directly_to_target(df_attivi, f"Attivita_In_Corso_{date.today()}.xlsx")
                    if ok: st.success(f"Salvato in {TARGET_FOLDER}")
                    else: st.error(f"Errore: {res}")
            with b3:
                html_print_attivi = generate_printable_html(df_attivi, "Tabella Attività In Corso")
                st.download_button("🖨️ Stampa / PDF", data=html_print_attivi, file_name=f"Stampa_Attivita_In_Corso_{date.today()}.html", mime="text/html", use_container_width=True)
        else:
            st.info("Nessuna attività in corso con i filtri selezionati.")

    # --- TAB 2: ARCHIVIO COMPLETATI ---
    with tab_completati:
        if not df_completati.empty:
            view_comp = df_completati[st.session_state.cols_order].copy()
            st.data_editor(
                view_comp,
                num_rows="dynamic",
                use_container_width=True,
                column_config=col_config,
                hide_index=True,
                key="editor_completati"
            )

            c0, c1, c2, c3 = st.columns([1.5, 1, 1.2, 1.3])
            with c0:
                if st.button("💾 Salva Modifiche Archivio", key="btn_save_comp", use_container_width=True):
                    process_and_save_editor("editor_completati", view_comp)
                    st.toast("✅ Archivio salvato con successo!", icon="💾")
                    st.rerun()
            with c1:
                excel_data_comp = convert_df_to_excel(df_completati)
                st.download_button("📥 Scarica Excel", data=excel_data_comp, file_name=f"Archivio_Completati_{date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            with c2:
                if st.button("📁 Salva in Wittur", key="btn_wittur_comp", use_container_width=True):
                    ok, res = export_directly_to_target(df_completati, f"Archivio_Completati_{date.today()}.xlsx")
                    if ok: st.success(f"Salvato in {TARGET_FOLDER}")
                    else: st.error(f"Errore: {res}")
            with c3:
                html_print_comp = generate_printable_html(df_completati, "Tabella Attività Completate")
                st.download_button("🖨️ Stampa / PDF", data=html_print_comp, file_name=f"Stampa_Archivio_Completati_{date.today()}.html", mime="text/html", use_container_width=True)
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
