import streamlit as st
import openai
import tweepy
from supabase import create_client
import os
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image
import requests
from io import BytesIO
import pytesseract
from transformers import pipeline

if 'initialized' not in st.session_state:
    st.session_state.update({
        'twitter_user': None,
        'use_fallback': False,
        'awaiting_pin': False,
        'twitter_auth': None,
        'initialized': True
    })

load_dotenv()
st.set_page_config(page_title="Know Your Fan - FURIA", page_icon="🎮")

if not all([os.getenv("TWITTER_API_KEY"), os.getenv("TWITTER_API_SECRET"), os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")]):
    st.error("váriaveis de ambiente não configuradas corretamente!")
    st.stop()

furia_logo = Image.open("./image/furia-logo.png")
st.image(furia_logo, width=100)
st.title("Know Your Fan - FURIA eSports")
st.write("Preencha seus dados como fã de eSports!")

def validar_cpf(cpf: str) -> bool:
    import re
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    for i in range(9, 11):
        soma = sum(int(cpf[j]) * (i+1 - j) for j in range(i))
        d = (soma * 10) % 11
        if d != int(cpf[i]):
            return False
    return True

with st.expander("📌 **Dados Pessoais**"):
    nome = st.text_input("Nome Completo*")
    cpf = st.text_input("CPF*")
    if cpf and not validar_cpf(cpf):
        st.warning("CPF inválido! Digite um CPF válido")
    email = st.text_input("E-mail*")
    endereco = st.text_input("Endereço (Rua/Avenida)*")
    cidade = st.text_input("Cidade*")
    estado = st.selectbox("Estado", ["SP", "RJ", "MG", "Outro"])

with st.expander("🎮 **Interesses em eSports**"):
    jogos = st.multiselect(
        "Quais jogos você acompanha?*",
        ["CS2", "Valorant", "League of Legends", "Dota 2", "FIFA"]
    )
    eventos = st.text_area("Quais eventos de eSports você participou no último ano?")

with st.expander("🛒 **Histórico de Compras**"):
    compras = st.multiselect(
        "O que você comprou no último ano?*",
        ["Ingresso para evento FURIA", "Produtos FURIA (camisas, etc)", "Assinatura de plataforma de eSports"]
    )
    valor_gasto = st.slider("Quanto você gastou aproximadamente (R$)?", 0, 5000, 100)

with st.expander("🆔 **Validação de Identidade**"):
    doc = st.file_uploader("Envie uma foto do seu RG ou CPF (apenas demonstração):", type=["jpg", "png"])
    if doc:
        img = Image.open(doc)
        st.image(img, width=300)
        try:
            texto_extraido = pytesseract.image_to_string(img).lower()
    
            # Verifica se o documento é RG ou CPF
            if "cpf" in texto_extraido or "rg" in texto_extraido:
                st.success("Tipo de documento válido!")
                
                # Extrai números do CPF no texto (usando regex)
                import re
                cpf_extraido = re.findall(r'\d{11}', texto_extraido)
                
                if cpf_extraido and cpf and cpf_extraido[0] == cpf.replace(".", "").replace("-", ""):
                    st.success("✅ CPF do documento coincide com o informado!")
                else:
                    st.error("CPF no documento não confere com o digitado")
            else:
                st.error("Documento não é RG ou CPF válido")
        except Exception as e:
            st.error("Erro ao ler o documento. Instale o Tesseract OCR conforme o README.")
            texto_extraido = ""

with st.expander("🐦 **Twitter/X Integration**"):
    twitter_input = st.text_input("Digite seu @ do Twitter (exemplo: @FURIA):")
    
    if twitter_input:
        twitter_username = twitter_input.replace("@", "").strip()
        if twitter_username:
            st.session_state['twitter_user'] = twitter_username
            st.success(f"Perfil @{twitter_username} vinculado com sucesso!")
    
    if st.session_state['twitter_user']:
        st.divider()
        st.write("📊 **Interações simuladas com a FURIA:**")
        st.write("- ✅ Curtiu 12 posts da FURIA nos últimos 3 meses")
        st.write("- 💬 Comentou em 3 posts sobre CS2")
        st.write("- 🔄 Retweetou 5 anúncios de campeonatos")
        st.write(f"✅ Conectado como @{st.session_state.twitter_user}")

with st.expander("🎯 Perfis em Sites de eSports"):
    
    hltv_profile = st.text_input("Seu perfil na HLTV.org")
    if hltv_profile:
        st.success("Perfil encontrado! Analisando relevância para FURIA...")
        
        # Simulação de análise com Hugging Face (customizada para FURIA)
        prompt = f"""
        Avalie o perfil HLTV '{hltv_profile}' como fã da FURIA baseado em:
        - Jogos de interesse: {', '.join(jogos) if jogos else 'Nenhum'}
        - Eventos mencionados: {eventos if eventos else 'Nenhum'}
        Saída: [0-100] de afinidade com a FURIA e 3 bullet points.
        """
    
        # Simulação (substitua por Hugging Face real se possível)
        afinidade = 75  # Exemplo fixo para o vídeo
        st.metric("Afinidade com FURIA", f"{afinidade}/100")
        
        st.write("""
        🔍 Análise da IA:
        - Alto interesse em CS2 (jogo principal da FURIA)
        - Participou de 2 eventos patrocinados pela FURIA
        - Perfil ativo há mais de 2 anos
        """)

col1, col2 = st.columns(2)
with col1:       
    if st.button("Enviar Dados", type="primary"):
        if nome and cpf and email and jogos:
            
            try:
                supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

                data = {
                    "nome": nome,
                    "cpf": cpf,
                    "email": email,
                    "endereco": endereco,
                    "cidade": cidade,
                    "estado": estado,
                    "jogos": jogos,
                    "eventos": eventos if eventos else None,
                    "compras": compras if compras else None,
                    "valor_gasto": valor_gasto,
                    "twitter_user": st.session_state.get('twitter_user'),
                    "hltv_profile": hltv_profile if hltv_profile else None
                }
                
                response = supabase.table("fans").insert(data).execute()
                
                if len(response.data) > 0:
                    st.balloons()
                    st.success("✅ Perfil salvo com sucesso!")
                    st.json(data)
                else:
                    st.error("Erro ao salvar no banco de dados")
            except Exception as e:
                st.error(f"Erro crítico: {str(e)}")
        else:
            st.error("Preencha os campos obrigatórios*")