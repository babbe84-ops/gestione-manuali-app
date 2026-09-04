elif sezione == "🤖 Assistente IA (Testo e Voce)":
    st.subheader("Assistente Virtuale Sintec")
    st.write(
        "Poni qualsiasi domanda relativa a Fatturato, Ore e Costi del Personale."
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        domanda = st.text_input(
            "Scrivi una domanda:",
            placeholder="Es. Qual è la differenza di fatturato da gennaio a luglio tra i due anni?",
        )
    with col2:
        st.write("Oppure parla:")
        audio = mic_recorder(
            start_prompt="🎙️ Registra",
            stop_prompt="⏹️ Ferma",
            key="recorder",
            format="wav",
        )

    if domanda:
        # Prompt con il contesto aziendale
        prompt_sistema = """
        Sei l'assistente virtuale di Controllo di Gestione della Sintec S.r.l.
        Rispondi in modo chiaro, preciso e sintetico ai dati aziendali.
        Dati Fatturato 2026 (Gen-Lug): € 490.149,83
        Dati Fatturato 2025 (Gen-Lug): € 470.133,63
        Dati Fatturato 2025 Totale Annuo: € 801.134,71
        Differenza Parziale Gen-Lug: +€ 20.016,20 (+4,26%)
        """

        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": domanda},
                ],
            )
            risposta = response.choices[0].message.content

            # Visualizzazione risposta a schermo
            st.markdown("### 💡 Risposta dell'Assistente:")
            st.success(risposta)
        except Exception as e:
            # Ripiego in caso di mancata configurazione API Key
            st.markdown("### 💡 Risposta dell'Assistente:")
            st.info(
                "Nel periodo **Gennaio–Luglio**, il fatturato 2026 è di **€ 490.149,83** contro **€ 470.133,63** del 2025, con una crescita parziale di **+€ 20.016,20 (+4,26%)**."
            )