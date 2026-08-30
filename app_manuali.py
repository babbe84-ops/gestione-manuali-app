import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import os
import io
import glob
import shutil
import subprocess
import platform

st.set_page_config(page_title="Gestione Manuali & Commesse", layout="wide", page_icon="📚")

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
    "Urgente"
]

ALL_COLUMNS = [
    "Nr. Commessa", "RDL", "Descrizione", "Tipo Ordine", "Attività", "Priorità", "Ore Valutate", "Responsabile", 
    "Stato", "Avanzamento (%)", "Modelli 3D dal", "Scadenza Prevista", "Nuova consegna prevista", "Spedizione Wittur", "Data Chiusura", "Percorso Cartella", "Note"
]

DEFAULT_ORDER = [
    "Nr. Commessa",
    "RDL",
    "Nuova consegna prevista",
    "Descrizione",
    "Priorità",
    "Attività",
    "Tipo Ordine",
    "Ore Valutate",
    "Responsabile",
    "Stato",
    "Avanzamento (%)",
    "Modelli 3D dal",
    "Scadenza Prevista",
    "Spedizione Wittur",
    "Data Chiusura",
    "Percorso Cartella",
    "Note",
    "Apri Cartella"
]

DATE_COLUMNS = [
    "Modelli 3D dal", 
    "Scadenza Prevista", 
    "Nuova consegna prevista", 
    "Spedizione Wittur", 
    "Data Chiusura"
]

if "cols_order" not in st.session_state:
    st.session_state.cols_order = DEFAULT_ORDER
if "sort_column" not in st.session_state:
    st.session_state.sort_column = "Nuova consegna prevista"
if "sort_ascending" not in st.session_state:
    st.session_state.sort_ascending = True

def init_db():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    if not os.path.exists(DB_FILE):
        df_initial = pd.DataFrame(columns=ALL_COLUMNS)
        df_initial.to_csv(DB_FILE, index=False)

init_db()

def safe_parse_date(val):
    if pd.isnull(val) or val == "" or str(val).strip().lower() in ["nan", "none", "nat"]:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    
    val_str = str(val).strip()
    parsed = pd.to_datetime(val_str, dayfirst=True, errors="coerce")
    if pd.notnull(parsed):
        return parsed.date()
    return None

def auto_update_urgency(dataframe):
    """Verifica la 'Nuova consegna prevista': se mancano <= 14 giorni di calendario e non è completata, imposta Priorità = Urgente."""
    today = date.today()
    if dataframe.empty:
        return dataframe
    
    for idx, row in dataframe.iterrows():
        if row["Stato"] != "Completato":
            d_consegna = safe_parse_date(row.get("Nuova consegna prevista"))
            if d_consegna:
                giorni_rimasti = (d_consegna - today).days
                if giorni_rimasti <= 14:
                    dataframe.at[idx, "Priorità"] = "Urgente"
    return dataframe

def generate_printable_html(df_to_print, title):
    cols = ["Nr. Commessa", "RDL", "Nuova consegna prevista", "Descrizione", "Priorità", "Attività", "Tipo Ordine", "Ore Valutate", "Responsabile", "Stato", "Avanzamento (%)", "Scadenza Prevista", "Spedizione Wittur"]
    df_clean = df_to_print[[c for c in cols if c in df_to_print.columns]].copy()
    
    for dcol in DATE_COLUMNS:
        if dcol in df_clean.columns:
            df_clean[dcol] = df_clean[dcol].apply(lambda x: x.strftime('%d/%m/%Y') if isinstance(x, (date, datetime)) else "")

    html_table = df_clean.to_html(index=False, classes="print-table")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                color: #333;
            }}
            h2 {{
                text-align: center;
                margin-bottom: 5px;
            }}
            p.date {{
                text-align: center;
                font-size: 12px;
                color: #666;
                margin-bottom: 20px;
            }}
            table.print-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 11px;
            }}
            table.print-table th, table.print-table td {{
                border: 1px solid #ccc;
                padding: 6px 8px;
                text-align: left;
            }}
            table.print-table th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            table.print-table tr:nth-child(even) {{
                background-color: #fafafa;
            }}
            @media print {{
                @page {{
                    size: landscape;
                    margin: 10mm;
                }}
                body {{
                    margin: 0;
                }}
            }}
        </style>
    </head>
    <body onload="window.print()">
        <h2>{title}</h2>
        <p class="date">Data stampa: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        {html_table}
    </body>
    </html>
    """
    return html_content

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

def load_data():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame(columns=ALL_COLUMNS)
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

def save_data(df):
    create_automatic_backup()
    df_to_save = df[ALL_COLUMNS].copy()
    
    for dcol in DATE_COLUMNS:
        df_to_save[dcol] = df_to_save[dcol].apply(lambda x: x.strftime('%Y-%m-%d') if isinstance(x, (date, datetime)) else "")
        
    df_to_save.to_csv(DB_FILE, index=False)

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

def open_folder(path):
    clean_path = str(path).strip()
    if not os.path.exists(clean_path):
        st.error(f"La cartella non esiste: {clean_path}")
        return
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["open", clean_path])
        elif system == "Windows":
            os.startfile(clean_path)
        else:
            subprocess.run(["xdg-open", clean_path])
    except Exception as e:
        st.error(f"Errore apertura cartella: {e}")

if "main_df" not in st.session_state:
    st.session_state.main_df = load_data()

st.session_state.main_df = auto_update_urgency(st.session_state.main_df)
df = st.session_state.main_df

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
        st.dataframe(
            sub_df[cols_to_show], 
            use_container_width=True, 
            hide_index=True
        )

@st.dialog("🔄 Ripristina un Backup precedente")
def restore_backup_dialog():
    backup_files = sorted(glob.glob(os.path.join(BACKUP_DIR, "manuali_progetti_db_*.csv")), reverse=True)
    
    if not backup_files:
        st.info("Nessun backup disponibile al momento.")
        return

    options = {}
    for f in backup_files:
        filename = os.path.basename(f)
        try:
            raw_ts = filename.replace("manuali_progetti_db_", "").replace(".csv", "")
            dt_obj = datetime.strptime(raw_ts, "%Y%m%d_%H%M%S")
            label = dt_obj.strftime("Backup del %d/%m/%Y alle ore %H:%M:%S")
        except Exception:
            label = filename
        options[label] = f

    selected_label = st.selectbox("Seleziona la versione da ripristinare:", list(options.keys()))
    selected_file = options[selected_label]

    st.warning("⚠️ **ATTENZIONE:** Il ripristino sovrascriverà i dati attuali con quelli del backup selezionato!")
    
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("🔴 Conferma Ripristino", type="primary", use_container_width=True):
            create_automatic_backup()
            shutil.copy(selected_file, DB_FILE)
            st.session_state.main_df = load_data()
            st.toast("✅ Database ripristinato con successo!", icon="🔄")
            st.rerun()
            
    with col_cancel:
        if st.button("Annulla", use_container_width=True):
            st.rerun()

st.title("📚 Gestione Manuali & Commesse")

# --- SIDEBAR: Configurazione Ordine Colonne ---
st.sidebar.header("⚙️ Visibilità Colonne")
selected_cols = st.sidebar.multiselect(
    "Seleziona colonne da mostrare:",
    options=DEFAULT_ORDER,
    default=st.session_state.cols_order
)
if selected_cols:
    st.session_state.cols_order = selected_cols

st.sidebar.divider()

# --- SIDEBAR: Inserimento Manuale ---
st.sidebar.header("➕ Nuova Commessa")
with st.sidebar.form("form_nuovo_progetto", clear_on_submit=True):
    codice = st.text_input("Nr. Commessa*")
    rdl_val = st.text_input("RDL / Titolo*")
    descrizione_val = st.text_input("Descrizione Commessa")
    tipo_ordine = st.radio("Tipo Ordine*", TIPO_ORDINE_OPTIONS, index=1, horizontal=True)
    attivita_selezionate = st.multiselect("Attività da svolgere*", options=ATTIVITA_OPTIONS, default=["Installation"])
    priorita = st.selectbox("Priorità / Urgenza*", PRIORITA_OPTIONS, index=1)
    ore_valutate = st.number_input("Ore Valutate (totali o per attività)", min_value=0.0, step=0.5)
    responsabili_sel = st.multiselect("Responsabili Tecnici", options=TECNICI, default=["Non ancora assegnato"])
    stato = st.selectbox("Stato Iniziale", ["Da iniziare", "In corso", "In revisione", "Completato"])
    avanzamento = st.slider("Avanzamento (%)", 0, 100, 0, step=5)
    modelli_3d_dal = st.date_input("Modelli 3D dal (GG/MM/AAAA)", value=date.today(), format="DD/MM/YYYY")
    scadenza = st.date_input("Scadenza Prevista (GG/MM/AAAA)", value=date.today(), format="DD/MM/YYYY")
    nuova_consegna = st.date_input("Nuova consegna prevista (GG/MM/AAAA)", value=date.today(), format="DD/MM/YYYY")
    spedizione_wittur = st.date_input("Spedizione Wittur (GG/MM/AAAA)", value=date.today(), format="DD/MM/YYYY")
    cartella = st.text_input("Percorso Cartella Locale")
    note = st.text_area("Note")
    
    submitted = st.form_submit_button("Salva Commessa / Attività")
    
    if submitted and codice and rdl_val:
        if not attivita_selezionate:
            attivita_selezionate = ["Altro"]
            
        resp_stringa = ", ".join([r for r in responsabili_sel if r]) if responsabili_sel else "Non ancora assegnato"
        today_val = date.today() if stato == "Completato" else None
        
        if stato != "Completato" and (nuova_consegna - date.today()).days <= 14:
            priorita = "Urgente"

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
        save_data(st.session_state.main_df)
        st.sidebar.success(f"Aggiunte {len(new_rows)} attività per la commessa '{codice}'!")
        st.rerun()

# --- SIDEBAR: Importazione & Merge Excel ---
st.sidebar.divider()
st.sidebar.header("📥 Importa / Unisci Excel")
uploaded_file = st.sidebar.file_uploader("Carica Excel (.xlsx / .xls)", type=["xlsx", "xls"])

if uploaded_file is not None:
    if st.sidebar.button("Procedi Importazione & Merge"):
        try:
            excel_df = pd.read_excel(uploaded_file, header=0, dtype=str)
            excel_df.columns = [str(c).strip() for c in excel_df.columns]
            
            df_current = st.session_state.main_df.copy()
            df_current["Nr. Commessa"] = df_current["Nr. Commessa"].astype(str).str.strip()
            
            aggiornati_count = 0
            nuovi_count = 0
            
            for idx, row in excel_df.iterrows():
                cod_val = row.get("Nr. Commessa", row.get("Commessa", row.iloc[0] if len(row) > 0 else ""))
                cod = str(cod_val).strip() if pd.notnull(cod_val) else ""
                
                rdl_imp = str(row.get("RDL", "")).strip() if pd.notnull(row.get("RDL")) else ""
                desc_imp = str(row.get("Descrizione", row.get("Titolo", ""))).strip() if pd.notnull(row.get("Descrizione", row.get("Titolo"))) else ""

                if (not cod or cod.lower() in ["nan", "none", "unnamed: 0"]) and (not rdl_imp or rdl_imp.lower() in ["nan", "none"]):
                    continue

                resp_val = str(row.get("Responsabile", "")).strip() if pd.notnull(row.get("Responsabile")) else "Non ancora assegnato"
                stato_imp = str(row.get("Stato", "Da iniziare")).strip() if pd.notnull(row.get("Stato")) else "Da iniziare"
                dt_chiusura = date.today() if stato_imp == "Completato" else None

                row_data = {
                    "Nr. Commessa": cod if cod.lower() not in ["nan", "none"] else f"COMM-{idx+1}",
                    "RDL": rdl_imp if rdl_imp.lower() not in ["nan", "none"] else "Senza RDL",
                    "Descrizione": desc_imp if desc_imp.lower() not in ["nan", "none"] else "",
                    "Tipo Ordine": str(row.get("Tipo Ordine", "Confermato")).strip(),
                    "Attività": str(row.get("Attività", "Installation")).strip(),
                    "Priorità": str(row.get("Priorità", "Normale")).strip(),
                    "Ore Valutate": pd.to_numeric(row.get("Ore Valutate", 0), errors="coerce") or 0.0,
                    "Responsabile": resp_val if resp_val.lower() not in ["nan", "none"] else "Non ancora assegnato",
                    "Stato": stato_imp,
                    "Avanzamento (%)": int(pd.to_numeric(row.get("Avanzamento (%)", 0), errors="coerce") or 0),
                    "Modelli 3D dal": safe_parse_date(row.get("Modelli 3D dal")),
                    "Scadenza Prevista": safe_parse_date(row.get("Scadenza Prevista")),
                    "Nuova consegna prevista": safe_parse_date(row.get("Nuova consegna prevista", row.get("Nuova consegna prevista iniziale"))),
                    "Spedizione Wittur": safe_parse_date(row.get("Spedizione Wittur")),
                    "Data Chiusura": dt_chiusura,
                    "Percorso Cartella": str(row.get("Percorso Cartella", "")),
                    "Note": str(row.get("Note", ""))
                }

                mask = df_current["Nr. Commessa"] == row_data["Nr. Commessa"]
                if mask.any():
                    match_indices = df_current[mask].index
                    for match_idx in match_indices:
                        for key, value in row_data.items():
                            val_str = str(value).strip() if isinstance(value, str) else value
                            if val_str and str(val_str).lower() not in ["nan", "none"]:
                                df_current.at[match_idx, key] = value
                    aggiornati_count += 1
                else:
                    df_current = pd.concat([df_current, pd.DataFrame([row_data])], ignore_index=True)
                    nuovi_count += 1

            df_current = auto_update_urgency(df_current)
            st.session_state.main_df = df_current
            save_data(df_current)
            st.sidebar.success(f"Merge completato! Commesse aggiornate: {aggiornati_count}, Nuove commesse: {nuovi_count}")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Errore durante l'importazione: {e}")

# --- SIDEBAR: Gestione e Ripristino Backup ---
st.sidebar.divider()
st.sidebar.header("🛡️ Ripristino Dati")
if st.sidebar.button("🔄 Gestione e Ripristino Backup", use_container_width=True):
    restore_backup_dialog()

# --- ANALISI CRITICITÀ ---
today_ts = date.today()
if not df.empty:
    progetti_in_ritardo = df[(df["Stato"] != "Completato") & (df["Scadenza Prevista"].apply(lambda x: isinstance(x, date) and x < today_ts))]
    progetti_urgenti = df[(df["Stato"] != "Completato") & (df["Priorità"] == "Urgente")]
else:
    progetti_in_ritardo = pd.DataFrame()
    progetti_urgenti = pd.DataFrame()

if not progetti_in_ritardo.empty or not progetti_urgenti.empty:
    st.subheader("⚠️ Avvisi & Criticità")
    c_warn1, c_warn2 = st.columns(2)
    
    with c_warn1:
        if not progetti_in_ritardo.empty:
            st.error(f"🚨 **{len(progetti_in_ritardo)} Attività in Ritardo!**")
            for idx, row in progetti_in_ritardo.iterrows():
                scad_val = row['Scadenza Prevista']
                scad_str = scad_val.strftime('%d/%m/%Y') if isinstance(scad_val, date) else ""
                st.caption(f"• **{row['Nr. Commessa']}** - {row['RDL']} [{row['Attività']}] (Scaduta il {scad_str})")
                
    with c_warn2:
        if not progetti_urgenti.empty:
            st.warning(f"🔥 **{len(progetti_urgenti)} Ordini URGENTI in Corso!**")
            for idx, row in progetti_urgenti.iterrows():
                st.caption(f"• **{row['Nr. Commessa']}** - {row['RDL']} (Tecnici: {row['Responsabile']})")

st.divider()

# --- KPI GENERALI INTERATTIVI ---
k1, k2, k3, k4 = st.columns(4)

df_totale = df.copy() if not df.empty else pd.DataFrame()
df_prev = df[df["Tipo Ordine"] == "Preventivo"].copy() if not df.empty else pd.DataFrame()
df_conf = df[df["Tipo Ordine"] == "Confermato"].copy() if not df.empty else pd.DataFrame()
df_urg = df[(df["Priorità"] == "Urgente") & (df["Stato"] != "Completato")].copy() if not df.empty else pd.DataFrame()

with k1:
    st.caption("Totale Attività")
    if st.button(f"🔍 **{len(df_totale)}**", key="btn_kpi_tot", use_container_width=True):
        show_kpi_details("Tutte le Attività", df_totale)

with k2:
    st.caption("Preventivi 📋")
    if st.button(f"📋 **{len(df_prev)}**", key="btn_kpi_prev", use_container_width=True):
        show_kpi_details("Elenco Preventivi", df_prev)

with k3:
    st.caption("Confermati ✅")
    if st.button(f"✅ **{len(df_conf)}**", key="btn_kpi_conf", use_container_width=True):
        show_kpi_details("Elenco Ordini Confermati", df_conf)

with k4:
    st.caption("Urgenti 🔥")
    if st.button(f"🔥 **{len(df_urg)}**", key="btn_kpi_urg", use_container_width=True):
        show_kpi_details("Elenco Attività Urgenti in Corso", df_urg)

st.divider()

# --- AGGIORNAMENTO RAPIDO ---
if not df.empty:
    st.subheader("⚡ Aggiornamento Rapido Attività")
    c_sel, c_tipo, c_prio, c_resp, c_st, c_av, c_btn = st.columns([2.5, 1.2, 1.2, 2.2, 1.2, 1.2, 1])
    
    with c_sel:
        options_list = [f"ID:{i} | {row['Nr. Commessa']} - {row['RDL']} ({row['Attività']})" for i, row in df.iterrows()]
        commessa_mod = st.selectbox("Seleziona Attività:", options=options_list, key="sel_mod")
    
    idx_target = int(commessa_mod.split(" | ")[0].replace("ID:", ""))
    row_attuale = df.iloc[idx_target]
    
    with c_tipo:
        tipo_curr = row_attuale["Tipo Ordine"] if row_attuale["Tipo Ordine"] in TIPO_ORDINE_OPTIONS else "Confermato"
        nuovo_tipo = st.selectbox("Tipo Ordine", TIPO_ORDINE_OPTIONS, index=TIPO_ORDINE_OPTIONS.index(tipo_curr))

    with c_prio:
        prio_curr = row_attuale["Priorità"] if row_attuale["Priorità"] in PRIORITA_OPTIONS else "Normale"
        nuova_prio = st.selectbox("Priorità", PRIORITA_OPTIONS, index=PRIORITA_OPTIONS.index(prio_curr))

    with c_resp:
        current_resps = [r.strip() for r in str(row_attuale["Responsabile"]).split(",") if r.strip() in TECNICI]
        if not current_resps:
            current_resps = ["Non ancora assegnato"]
        nuovi_resp = st.multiselect("Tecnici", TECNICI, default=current_resps)

    with c_st:
        stati_opt = ["Da iniziare", "In corso", "In revisione", "Completato"]
        st_curr = row_attuale["Stato"] if row_attuale["Stato"] in stati_opt else stati_opt[0]
        nuovo_stato = st.selectbox("Stato", stati_opt, index=stati_opt.index(st_curr))
        
    with c_av:
        avanz_default = 100 if nuovo_stato == "Completato" else int(row_attuale["Avanzamento (%)"])
        nuovo_avanzamento = st.slider("Avanzamento %", 0, 100, avanz_default, step=5)
        
    with c_btn:
        st.write("")
        st.write("")
        if st.button("✅ Applica"):
            st.session_state.main_df.at[idx_target, "Tipo Ordine"] = nuovo_tipo
            st.session_state.main_df.at[idx_target, "Priorità"] = nuova_prio
            st.session_state.main_df.at[idx_target, "Responsabile"] = ", ".join(nuovi_resp) if nuovi_resp else "Non ancora assegnato"
            
            if nuovo_stato == "Completato" and row_attuale["Stato"] != "Completato":
                st.session_state.main_df.at[idx_target, "Data Chiusura"] = date.today()
            elif nuovo_stato != "Completato":
                st.session_state.main_df.at[idx_target, "Data Chiusura"] = None
                
            st.session_state.main_df.at[idx_target, "Stato"] = nuovo_stato
            st.session_state.main_df.at[idx_target, "Avanzamento (%)"] = 100 if nuovo_stato == "Completato" else nuovo_avanzamento
            
            st.session_state.main_df = auto_update_urgency(st.session_state.main_df)
            save_data(st.session_state.main_df)
            st.success("Attività aggiornata!")
            st.rerun()

st.divider()

# --- TABELLE OPERATIVE ---

if not df.empty:
    st.subheader("🔍 Filtri & Ordinamento Tabelle")
    
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        search_query = st.text_input("Cerca testo (Commessa, RDL, Descrizione, Note):", "")
    with f_col2:
        filtro_tecnico = st.multiselect("Filtra per Tecnico:", options=TECNICI)
    with f_col3:
        filtro_attivita = st.multiselect("Filtra per Attività:", options=ATTIVITA_OPTIONS)
    with f_col4:
        filtro_prio = st.multiselect("Filtra per Priorità:", options=PRIORITA_OPTIONS)

    available_sort_cols = [c for c in DEFAULT_ORDER if c in st.session_state.cols_order and c != "Apri Cartella"]
    if "Nuova consegna prevista" in available_sort_cols:
        available_sort_cols.remove("Nuova consegna prevista")
        available_sort_cols.insert(0, "Nuova consegna prevista")

    s_col1, s_col2 = st.columns([3, 1])
    with s_col1:
        sort_col_selected = st.selectbox(
            "Sort/Ordina tabella in base alla colonna:",
            options=available_sort_cols,
            index=available_sort_cols.index(st.session_state.sort_column) if st.session_state.sort_column in available_sort_cols else 0
        )
        st.session_state.sort_column = sort_col_selected
    with s_col2:
        sort_order = st.radio("Ordine:", options=["Crescente ⬆️", "Decrescente ⬇️"], horizontal=True)
        st.session_state.sort_ascending = (sort_order == "Crescente ⬆️")
    
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

    df_attivi = df_base[df_base["Stato"] != "Completato"].copy()
    df_completati = df_base[df_base["Stato"] == "Completato"].copy()

    def process_table_df(target_df):
        for c in ALL_COLUMNS:
            if c not in ["Ore Valutate", "Avanzamento (%)"] + DATE_COLUMNS:
                target_df[c] = target_df[c].fillna("").astype(str)
                
        target_df["Ore Valutate"] = pd.to_numeric(target_df["Ore Valutate"], errors="coerce").fillna(0.0)
        target_df["Avanzamento (%)"] = pd.to_numeric(target_df["Avanzamento (%)"], errors="coerce").fillna(0).astype(int)
        
        for dcol in DATE_COLUMNS:
            target_df[dcol] = target_df[dcol].apply(safe_parse_date)

        target_df["Apri Cartella"] = False

        if st.session_state.sort_column in target_df.columns:
            target_df = target_df.sort_values(
                by=st.session_state.sort_column, 
                ascending=st.session_state.sort_ascending, 
                na_position='last'
            )

        return target_df

    col_config = {
        "Nr. Commessa": st.column_config.TextColumn("Nr. Commessa"),
        "RDL": st.column_config.TextColumn("RDL", pinned=True),
        "Nuova consegna prevista": st.column_config.DateColumn("Nuova consegna prevista", format="DD/MM/YYYY"),
        "Descrizione": st.column_config.TextColumn("Descrizione"),
        "Priorità": st.column_config.SelectboxColumn("Priorità", options=PRIORITA_OPTIONS, required=True),
        "Attività": st.column_config.SelectboxColumn("Attività", options=ATTIVITA_OPTIONS, required=True),
        "Tipo Ordine": st.column_config.SelectboxColumn("Tipo Ordine", options=TIPO_ORDINE_OPTIONS, required=True),
        "Responsabile": st.column_config.TextColumn("Responsabile Tecnico"),
        "Stato": st.column_config.SelectboxColumn("Stato", options=["Da iniziare", "In corso", "In revisione", "Completato"], required=True),
        "Avanzamento (%)": st.column_config.NumberColumn("Avanzamento (%)", min_value=0, max_value=100, step=5),
        "Modelli 3D dal": st.column_config.DateColumn("Modelli 3D dal", format="DD/MM/YYYY"),
        "Scadenza Prevista": st.column_config.DateColumn("Scadenza Prevista", format="DD/MM/YYYY"),
        "Spedizione Wittur": st.column_config.DateColumn("Spedizione Wittur", format="DD/MM/YYYY"),
        "Data Chiusura": st.column_config.DateColumn("Data Chiusura", format="DD/MM/YYYY"),
        "Percorso Cartella": st.column_config.TextColumn("Percorso Cartella Locale"),
        "Apri Cartella": st.column_config.CheckboxColumn("📂 Apri", help="Spunta per aprire la cartella nel sistema"),
        "Ore Valutate": st.column_config.NumberColumn("Ore Valutate", format="%.1f")
    }

    def sync_edited_changes(edited_df):
        for idx, row in edited_df.iterrows():
            if idx in st.session_state.main_df.index:
                for c in ALL_COLUMNS:
                    if c in edited_df.columns:
                        val = row[c]
                        if c in DATE_COLUMNS:
                            st.session_state.main_df.at[idx, c] = safe_parse_date(val)
                        elif c == "Ore Valutate":
                            st.session_state.main_df.at[idx, c] = float(pd.to_numeric(val, errors="coerce") or 0.0)
                        elif c == "Avanzamento (%)":
                            st.session_state.main_df.at[idx, c] = int(pd.to_numeric(val, errors="coerce") or 0)
                        else:
                            st.session_state.main_df.at[idx, c] = str(val) if pd.notnull(val) else ""
                            
        st.session_state.main_df = auto_update_urgency(st.session_state.main_df)

    # --- TABELLA 1: ATTIVITÀ IN CORSO ---
    st.subheader("📋 1. Attività In Corso / Da Iniziare")
    if not df_attivi.empty:
        df_attivi = process_table_df(df_attivi)

        edited_attivi = st.data_editor(
            df_attivi[st.session_state.cols_order],
            num_rows="dynamic",
            use_container_width=True,
            column_config=col_config,
            hide_index=True,
            key="editor_attivi"
        )

        sync_edited_changes(edited_attivi)

        opened = edited_attivi[edited_attivi["Apri Cartella"] == True] if "Apri Cartella" in edited_attivi.columns else pd.DataFrame()
        if not opened.empty:
            for idx, r in opened.iterrows():
                if r.get("Percorso Cartella"):
                    open_folder(r["Percorso Cartella"])

        c_btn1, c_btn2, c_btn3, c_btn4 = st.columns([1.8, 1, 1.3, 1.4])
        with c_btn1:
            if st.button("💾 Salva Modifiche Attività In Corso"):
                save_data(st.session_state.main_df)
                st.success("Modifiche e backup salvati con successo!")
                st.rerun()
                
        with c_btn2:
            excel_data_attivi = convert_df_to_excel(df_attivi)
            st.download_button(
                label="📥 Scarica Excel",
                data=excel_data_attivi,
                file_name=f"Attivita_In_Corso_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        with c_btn3:
            if st.button("📁 Salva in Wittur/MANUALI", key="btn_wittur_attivi", use_container_width=True):
                fname = f"Attivita_In_Corso_{date.today()}.xlsx"
                ok, res = export_directly_to_target(df_attivi, fname)
                if ok:
                    st.success(f"Salvato in {TARGET_FOLDER}")
                else:
                    st.error(f"Errore durante il salvataggio: {res}")

        with c_btn4:
            html_print_attivi = generate_printable_html(df_attivi, "Tabella Attività In Corso / Da Iniziare")
            st.download_button(
                label="🖨️ Stampa / Esporta PDF Tabella",
                data=html_print_attivi,
                file_name=f"Stampa_Attivita_In_Corso_{date.today()}.html",
                mime="text/html",
                use_container_width=True
            )

    else:
        st.info("Nessuna attività in corso.")

    st.divider()

    # --- TABELLA 2: ATTIVITÀ COMPLETATE ---
    st.subheader("✅ 2. Attività Completate (Archivio)")
    if not df_completati.empty:
        df_completati = process_table_df(df_completati)

        edited_comp = st.data_editor(
            df_completati[st.session_state.cols_order],
            num_rows="dynamic",
            use_container_width=True,
            column_config=col_config,
            hide_index=True,
            key="editor_completati"
        )

        sync_edited_changes(edited_comp)

        opened_comp = edited_comp[edited_comp["Apri Cartella"] == True] if "Apri Cartella" in edited_comp.columns else pd.DataFrame()
        if not opened_comp.empty:
            for idx, r in opened_comp.iterrows():
                if r.get("Percorso Cartella"):
                    open_folder(r["Percorso Cartella"])

        c_comp1, c_comp2, c_comp3, c_comp4 = st.columns([1.8, 1, 1.3, 1.4])
        with c_comp1:
            if st.button("💾 Salva Modifiche Archivio Completati"):
                save_data(st.session_state.main_df)
                st.success("Archivio e backup salvati con successo!")
                st.rerun()
                
        with c_comp2:
            excel_data_comp = convert_df_to_excel(df_completati)
            st.download_button(
                label="📥 Scarica Excel",
                data=excel_data_comp,
                file_name=f"Archivio_Completati_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        with c_comp3:
            if st.button("📁 Salva in Wittur/MANUALI", key="btn_wittur_comp", use_container_width=True):
                fname = f"Archivio_Completati_{date.today()}.xlsx"
                ok, res = export_directly_to_target(df_completati, fname)
                if ok:
                    st.success(f"Salvato in {TARGET_FOLDER}")
                else:
                    st.error(f"Errore durante il salvataggio: {res}")

        with c_comp4:
            html_print_comp = generate_printable_html(df_completati, "Tabella Attività Completate (Archivio)")
            st.download_button(
                label="🖨️ Stampa / Esporta PDF Tabella",
                data=html_print_comp,
                file_name=f"Stampa_Archivio_Completati_{date.today()}.html",
                mime="text/html",
                use_container_width=True
            )
    else:
        st.info("Nessuna attività completata.")

else:
    st.info("Nessuna commessa presente. Carica il file Excel a sinistra per iniziare.")