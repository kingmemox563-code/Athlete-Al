import streamlit as st
import os
import json
import io
import requests
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
from fpdf import FPDF
from streamlit_option_menu import option_menu
from openai import OpenAI

# ReportLab Imports
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import JsonOutputParser

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# --- Load Environment Variables ---
load_dotenv()

# --- Pydantic Models for AI Response ---
class NutritionalValues(BaseModel):
    kalori: int = Field(description="Toplam kalori (kcal)")
    protein_g: int = Field(description="Toplam protein (gram)")
    karbonhidrat_g: int = Field(description="Toplam karbonhidrat (gram)")
    yag_g: int = Field(description="Toplam yağ (gram)")

class RecipeResponse(BaseModel):
    tarif_adi: str = Field(description="Tarifin yaratıcı veya bilindik adı")
    mutfak: str = Field(description="Hangi dünya mutfağına ait olduğu")
    kullanilacak_olculer: List[str] = Field(description="Malzemeler ve ölçüleri")
    hazirlanis: List[str] = Field(description="Adım adım hazırlanış talimatları")
    besin_degerleri: NutritionalValues = Field(description="Tahmini besin değerleri")
    sporcu_uygunlugu: str = Field(description="Sporcu hedeflerine uygunluk yorumu")
    zamanlama: str = Field(description="Antrenman öncesi mi sonrası mı")

class Meal(BaseModel):
    ogun_adi: str = Field(description="Öğün adı")
    tarif_adi: str = Field(description="Yemeğin adı")
    malzemeler: List[str] = Field(description="Malzemeler ve ölçüleri")
    hazirlanis: List[str] = Field(description="Adım adım hazırlanış")
    besin_degerleri: NutritionalValues = Field(description="Besin değerleri")

class DailyMenuResponse(BaseModel):
    menu_adi: str = Field(description="Günlük menü adı")
    ogunler: List[Meal] = Field(description="Öğün listesi")
    toplam_besin_degerleri: NutritionalValues = Field(description="Tüm günün toplamı")
    sporcu_uygunlugu: str = Field(description="Genel sporcu yorumu")

# --- RAG Database Initialization ---
@st.cache_resource
def init_rag_db():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    persist_directory = "chroma_db_v4"
    
    if os.path.exists(persist_directory):
        return Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        
    try:
        loader = TextLoader("data/saglikli_tarifler.txt", encoding="utf-8")
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        texts = text_splitter.split_documents(documents)
        vectorstore = Chroma.from_documents(documents=texts, embedding=embeddings, persist_directory=persist_directory)
        return vectorstore
    except Exception as e:
        st.error(f"Veritabanı hatası: {e}")
        return None

vectorstore = init_rag_db()

# --- Utility: Image Generator & Saver ---
def get_recipe_image(recipe_name, details=""):
    clean_name = "".join([c for c in recipe_name if c.isalnum() or c==' ']).rstrip().replace(" ", "_").lower()
    img_path = f"images/{clean_name}.png"
    
    if os.path.exists(img_path):
        return img_path
    
    # Strict literal prompt to prevent AI hallucinations
    no_egg = "NO eggs, " if "yumurta" not in details.lower() and "egg" not in details.lower() else ""
    if "Menü" in recipe_name or "Menu" in recipe_name or "Günlük" in recipe_name:
        prompt = f"A realistic, professional studio food photography of exactly three plates on a white table: {details}. {no_egg}Each plate contains one of the mentioned meals. NO random seeds, NO extra fruits, NO unrelated items. Only the meals listed. High resolution, hyper-realistic, top-down view."
    else:
        prompt = f"A high-end professional food photography of {recipe_name} containing exactly these ingredients: {details}. {no_egg}Centered, high resolution, realistic texture, no extra decorations, professional lighting."
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        img_data = requests.get(image_url).content
        with open(img_path, 'wb') as handler:
            handler.write(img_data)
        return img_path
    except Exception as e:
        return None

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle

# --- Utility: PDF Generator (Pro Platypus Version) ---
def create_pdf(content_dict, mode="Tek Öğün", image_path=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    story = []
    
    # Font Registration
    font_path = r"C:\Windows\Fonts\arial.ttf"
    font_name = "Helvetica"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('ArialTR', font_path))
        font_name = 'ArialTR'

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TRTitle', fontName=font_name, fontSize=24, leading=28, alignment=1, textColor=colors.HexColor("#0f172a"), spaceAfter=20))
    styles.add(ParagraphStyle(name='TRHeader', fontName=font_name, fontSize=14, leading=18, textColor=colors.HexColor("#2563eb"), spaceBefore=15, spaceAfter=10, borderPadding=5))
    styles.add(ParagraphStyle(name='TRBody', fontName=font_name, fontSize=10, leading=14, textColor=colors.HexColor("#334155")))
    styles.add(ParagraphStyle(name='TRMacro', fontName=font_name, fontSize=11, leading=14, alignment=1, textColor=colors.white, backColor=colors.HexColor("#1e293b"), borderPadding=10))

    # 1. Branding Title
    story.append(Paragraph("AthletePro AI - Beslenme Raporu", styles['TRTitle']))
    story.append(Spacer(1, 10))

    # 2. Image
    if image_path and os.path.exists(image_path):
        try:
            img = Image(image_path, width=400, height=250)
            img.hAlign = 'CENTER'
            story.append(img)
            story.append(Spacer(1, 20))
        except: pass

    # 3. Recipe Name
    title = str(content_dict.get('tarif_adi') or content_dict.get('menu_adi', 'Beslenme Plani'))
    story.append(Paragraph(title, styles['TRHeader']))

    if mode == "Tek Öğün":
        # 4. Macros
        m = content_dict.get('besin_degerleri', {})
        macro_text = f"KALORİ: {m.get('kalori')} | PROTEİN: {m.get('protein_g')}g | KARB: {m.get('karbonhidrat_g')}g | YAĞ: {m.get('yag_g')}g"
        story.append(Paragraph(macro_text, styles['TRMacro']))
        story.append(Spacer(1, 15))

        # 5. Ingredients
        story.append(Paragraph("Gerekli Malzemeler", styles['TRHeader']))
        for item in content_dict.get('kullanilacak_olculer', []):
            story.append(Paragraph(f"• {item}", styles['TRBody']))
        
        story.append(Spacer(1, 15))

        # 6. Preparation
        story.append(Paragraph("Hazırlanış", styles['TRHeader']))
        for i, step in enumerate(content_dict.get('hazirlanis', [])):
            story.append(Paragraph(f"<b>{i+1}.</b> {step}", styles['TRBody']))
            story.append(Spacer(1, 5))
            
    else: # Daily Menu
        for ogun in content_dict.get('ogunler', []):
            story.append(Paragraph(f"{ogun['ogun_adi']}: {ogun['tarif_adi']}", styles['TRHeader']))
            story.append(Paragraph("<b>Malzemeler:</b> " + ", ".join(ogun['malzemeler']), styles['TRBody']))
            story.append(Spacer(1, 5))
            story.append(Paragraph("<b>Hazırlanış:</b> " + " ".join(ogun['hazirlanis']), styles['TRBody']))
            story.append(Spacer(1, 10))

    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph("<hr/>", styles['TRBody']))
    story.append(Paragraph("Bu plan AthletePro AI tarafından size özel hazırlanmıştır.", styles['TRBody']))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# --- UI Setup ---
st.set_page_config(page_title="AthletePro AI", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #f8fafc; }
    .glass-card { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1); padding: 25px; margin-bottom: 20px; }
    .metric-card { background: rgba(59, 130, 246, 0.1); border-left: 5px solid #3b82f6; padding: 15px; border-radius: 10px; text-align: center; }
    h1, h2, h3 { color: #3b82f6 !important; font-weight: 800 !important; }
    .stButton>button { background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%); color: white; border-radius: 10px; border: none; padding: 10px 25px; font-weight: 600; transition: all 0.3s ease; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(37, 99, 235, 0.3); }
    section[data-testid="stSidebar"] { background-color: #0f172a !important; border-right: 1px solid rgba(255, 255, 255, 0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar Navigation ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: white !important;'>⚡ AthletePro</h1>", unsafe_allow_html=True)
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "AI Şef", "Tarif Arşivi", "Alışveriş Listesi", "Sporcu Rehberi", "Ayarlar"],
        icons=["house", "cpu", "book", "cart", "lightning", "gear"],
        default_index=0,
        styles={
            "container": {"background-color": "transparent"},
            "nav-link": {"color": "white", "font-size": "0.9rem"},
            "nav-link-selected": {"background-color": "rgba(59, 130, 246, 0.2)"}
        }
    )

# --- Pages ---
if selected == "Dashboard":
    st.title("📊 Sporcu Dashboard")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("<div class='glass-card'><h3>🎯 Makro Hesaplayıcı</h3>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        w = c1.number_input("Kilo (kg)", value=75)
        h = c2.number_input("Boy (cm)", value=180)
        a = c3.number_input("Yaş", value=25)
        g = st.radio("Cinsiyet", ["Erkek", "Kadın"], horizontal=True)
        lvl = st.selectbox("Aktivite", ["Sedanter", "Hafif", "Orta", "Çok Aktif"])
        if st.button("Hesapla"):
            bmr = 10*w + 6.25*h - 5*a + (5 if g=="Erkek" else -161)
            mult = {"Sedanter": 1.2, "Hafif": 1.375, "Orta": 1.55, "Çok Aktif": 1.725}
            tdee = bmr * mult[lvl]
            st.session_state['tdee'] = int(tdee)
            st.session_state['protein_target'] = int(w * 2)
            st.success(f"Günlük Hedef: {int(tdee)} kcal | {st.session_state['protein_target']}g Protein")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><small>Hedef Kalori</small><h2>{st.session_state.get('tdee','---')}</h2></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card'><small>Hedef Protein</small><h2>{st.session_state.get('protein_target','---')}g</h2></div>", unsafe_allow_html=True)

elif selected == "AI Şef":
    st.title("🍳 AI Şef")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        ing = st.text_area("Malzemeler", placeholder="Tavuk, pirinç...")
        tp = st.number_input("Hedef P (g)", value=st.session_state.get('protein_target', 0))
        tc = st.number_input("Hedef Kcal", value=st.session_state.get('tdee', 0))
        mode = st.radio("Mod", ["Tek Öğün", "Günlük Menü"], horizontal=True)
        gen_img = st.checkbox("🖼️ Görsel Oluştur (DALL-E)", value=True)
        
        if st.button("Üret"):
            provider = st.session_state.get('provider', "OpenAI")
            model = st.session_state.get('model', "gpt-4o")
            try:
                if "Google" in provider:
                    llm = ChatGoogleGenerativeAI(model=model)
                else:
                    llm = ChatOpenAI(model=model)
                
                with st.spinner("Şefimiz mutfakta çalışıyor..."):
                    docs = vectorstore.similarity_search(f"{ing} {tp}g P", k=6)
                    context = "\n\n".join([d.page_content for d in docs])
                    st.session_state['last_docs'] = docs # Store for references
                    
                    if mode == "Günlük Menü":
                        parser = JsonOutputParser(pydantic_object=DailyMenuResponse)
                        instr = "MUTLAKA 3 ÖĞÜN (Kahvaltı, Öğle, Akşam) içeren bir günlük sporcu menüsü oluştur."
                    else:
                        parser = JsonOutputParser(pydantic_object=RecipeResponse)
                        instr = "Tek bir doyurucu ve sağlıklı sporcu tarifi oluştur."
                        
                    prompt = PromptTemplate(
                        template="Sen profesyonel bir sporcu şefisin.\n\n"
                                 "KATI KURAL 1: SADECE kullanıcının verdiği malzemeleri kullan. Kullanıcı 'yumurta' yazmadıysa kahvaltıda bile yumurta KULLANMA.\n"
                                 "KATI KURAL 2: Eksik malzemeleri uydurma. Kullanıcının elinde sadece kıyma ve patates varsa, öğünleri bunlarla tasarla (örn: kahvaltıda patatesli kıyma sote).\n"
                                 "KATI KURAL 3: Referans tarifleri sadece teknik ve format için kullan, içindeki malzemeleri (tavuk, yumurta vb.) kopyalama.\n\n"
                                 "REFERANS TARİFLER:\n{context}\n\n"
                                 "TALİMAT: {instr}\n"
                                 "KULLANICI MALZEMELERİ: {ing}\n"
                                 "HEDEF: {tp}g Protein, {tc} kcal\n\n"
                                 "TÜM METİNLERİ TÜRKÇE VE DETAYLI YAZ.\n"
                                 "JSON formatına uy:\n{format_instructions}",
                        input_variables=["context", "instr", "ing", "tp", "tc"],
                        partial_variables={"format_instructions": parser.get_format_instructions()}
                    )
                    res = (prompt | llm | parser).invoke({"context": context, "instr": instr, "ing": ing, "tp": tp, "tc": tc})
                    st.session_state['last_res'] = res
                    st.session_state['last_mode'] = mode
                    
                    if gen_img:
                        with st.spinner("Yemeğin fotoğrafı çekiliyor..."):
                            name = res.get('tarif_adi') or res.get('menu_adi')
                            # Prepare context for better image accuracy
                            if mode == "Günlük Menü":
                                det = ", ".join([f"{o['ogun_adi']}: {o['tarif_adi']}" for o in res.get('ogunler', [])])
                            else:
                                det = ", ".join(res.get('kullanilacak_olculer', []))[:200]
                            
                            img_path = get_recipe_image(name, details=det)
                            st.session_state['last_img'] = img_path
                    else:
                        st.session_state['last_img'] = None
                        
            except Exception as e: st.error(str(e))
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        if 'last_res' in st.session_state:
            res = st.session_state['last_res']
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            if st.session_state.get('last_img'):
                st.image(st.session_state['last_img'], width="stretch")
            
            if st.session_state['last_mode'] == "Tek Öğün":
                st.header(res.get('tarif_adi'))
                st.write("**Mutfak:**", res.get('mutfak'))
                st.write("**Malzemeler:**")
                for m in res.get('kullanilacak_olculer', []): st.write(f"- {m}")
                st.write("**Hazırlanış:**")
                for s in res.get('hazirlanis', []): st.write(f"- {s}")
                st.session_state['last_list'] = res.get('kullanilacak_olculer', [])
            else:
                st.header(res.get('menu_adi'))
                for o in res.get('ogunler', []):
                    with st.expander(f"🍴 {o['ogun_adi']}: {o['tarif_adi']}"):
                        st.write("**Malzemeler:**", ", ".join(o['malzemeler']))
                        st.write("**Hazırlanış:**", " ".join(o['hazirlanis']))
                        m = o.get('besin_degerleri', {})
                        st.info(f"📊 {m.get('kalori')} kcal | {m.get('protein_g')}g P")
                all_m = []
                for o in res.get('ogunler', []): all_m.extend(o['malzemeler'])
                st.session_state['last_list'] = all_m
            
            try:
                pdf_data = create_pdf(res, mode=st.session_state['last_mode'], image_path=st.session_state.get('last_img'))
                st.download_button("📥 Profesyonel Menüyü PDF İndir", data=pdf_data, file_name="sporcu_menusu.pdf", width="stretch")
            except Exception as e:
                st.warning(f"PDF oluşturulurken bir hata oluştu: {e}")
            
            # --- RAG References Expander ---
            if 'last_docs' in st.session_state:
                with st.expander("📌 Referans Alınan Kaynaklar (RAG)"):
                    st.write("Yapay zeka bu tarifi üretirken veritabanındaki şu kayıtlardan faydalandı:")
                    for doc in st.session_state['last_docs']:
                        title = doc.page_content.split("\n")[0]
                        st.markdown(f"- **{title}**")
                        st.caption(doc.page_content[:150] + "...")
            
            st.markdown("</div>", unsafe_allow_html=True)

elif selected == "Tarif Arşivi":
    st.title("📖 Tarif Arşivi")
    q = st.text_input("🔍 Tariflerde Ara...")
    with open("data/saglikli_tarifler.txt", "r", encoding="utf-8") as f:
        recipes = f.read().split("\n\n")
    filtered = [x for x in recipes if q.lower() in x.lower()]
    cols = st.columns(2)
    for i, r in enumerate(filtered[:100]):
        with cols[i%2]:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            title_line = r.split("\n")[0]
            title = title_line.split(":")[-1].strip() if ":" in title_line else title_line
            clean_name = "".join([c for c in title if c.isalnum() or c==' ']).rstrip().replace(" ", "_").lower()
            img_path = f"images/{clean_name}.png"
            
            if os.path.exists(img_path):
                st.image(img_path, width="stretch")
            else:
                if st.button(f"🖼️ Görsel Oluştur: {title[:20]}...", key=f"gen_{i}"):
                    with st.spinner("Görsel oluşturuluyor..."):
                        get_recipe_image(title)
                        st.rerun()
            
            st.markdown(f"### {title}")
            st.write(r.replace(title_line, "").strip()[:200] + "...")
            st.markdown("</div>", unsafe_allow_html=True)

elif selected == "Alışveriş Listesi":
    st.title("🛒 Alışveriş Listesi")
    list_items = st.session_state.get('last_list', [])
    if list_items:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        for item in list_items: st.checkbox(item, key=f"shop_{item}")
        if st.button("Listeyi Temizle"): st.session_state.pop('last_list'); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    else: st.info("Liste boş. AI Şef ile bir menü oluşturun.")

elif selected == "Sporcu Rehberi":
    st.title("💡 Sporcu Beslenme Rehberi")
    t1, t2, t3 = st.tabs(["🕒 Zamanlama", "⚖️ Makrolar", "💧 Hidrasyon"])
    with t1:
        st.markdown("### Antrenman Öncesi\n- 1-2 saat önce kompleks karbonhidrat alımı enerji sağlar.")
        st.markdown("### Antrenman Sonrası\n- İlk 30-60 dakika içinde protein alımı kas onarımı için hayatidir.")
    with t2:
        st.markdown("- **Protein:** Kg başına 1.6g - 2g idealdir.\n- **Karb:** Enerji ihtiyacına göre ayarlanmalıdır.\n- **Yağ:** Sağlıklı yağlar (Avokado, Zeytinyağı) hormon sağlığı için gereklidir.")
    with t3:
        st.markdown("- Her 20 kg vücut ağırlığı için yaklaşık 1 litre su tüketilmelidir.")

elif selected == "Ayarlar":
    st.title("⚙️ Ayarlar")
    st.session_state['provider'] = st.selectbox("LLM Sağlayıcı", ["OpenAI", "Google Gemini"], index=0)
    
    default_model = "gpt-4o" if st.session_state['provider'] == "OpenAI" else "gemini-1.5-flash"
    st.session_state['model'] = st.text_input("Model Adı", value=st.session_state.get('model', default_model))
    
    key = st.text_input("API Key", type="password", value=os.getenv("OPENAI_API_KEY" if st.session_state['provider'] == "OpenAI" else "GOOGLE_API_KEY", ""))
    
    if st.button("Ayarları Kaydet"):
        if key:
            env_var = "OPENAI_API_KEY" if st.session_state['provider'] == "OpenAI" else "GOOGLE_API_KEY"
            os.environ[env_var] = key
            st.success(f"Ayarlar Kaydedildi! ({st.session_state['provider']} - {st.session_state['model']})")
        else:
            st.warning("Lütfen bir API anahtarı girin.")
