# Proje Teknik Raporu: RAG Tabanlı AI Şef & Sporcu Menüleri

**Hazırlayan:** [Kullanıcı Adı]
**Tarih:** 20 Nisan 2026
**Proje Amacı:** Sporcuların makro hedeflerine (protein/kalori) ve ellerindeki malzemelere göre kişiselleştirilmiş, veriye dayalı (RAG) sağlıklı öğünler ve tam günlük diyet menüleri üretmek.

---

## 1. Mimari ve Teknoloji Yığını (Tech Stack)

Proje, modern üretken yapay zeka (GenAI) mimarilerinden biri olan **RAG (Retrieval-Augmented Generation)** üzerine inşa edilmiştir.

- **Frontend:** Streamlit (Hızlı ve kullanıcı dostu Python tabanlı web arayüzü)
- **Framework:** LangChain (LLM ve Vektör Veritabanı yönetim zinciri)
- **Vektör Veritabanı:** ChromaDB (Lokal ve kalıcı vektör depolama)
- **Embedding Modeli:** HuggingFace `all-MiniLM-L6-v2` (Lokal çalışan, hızlı ve kaynak dostu vektörleştirme modeli)
- **LLM Motorları:** OpenAI (GPT-4o mini), Google Gemini 1.5 Flash ve Yerel modeller (Ollama/Llama3) desteği.

---

## 2. Veri Hazırlama ve İşleme (Data Engineering)

- **Veri Kaynağı:** `data/saglikli_tarifler.txt` dosyasında bulunan 50 adet özel seçilmiş, Türk mutfağı ağırlıklı sporcu tarifi.
- **Yükleme (Loading):** `TextLoader` kullanılarak ham metin verisi LangChain Document nesnelerine dönüştürülmüştür.
- **Parçalama (Chunking):** 
    - **Strateji:** `RecursiveCharacterTextSplitter`
    - **Parça Boyutu (Chunk Size):** 400 karakter.
    - **Kesişim (Overlap):** 50 karakter (Bağlam kaybını önlemek için parçalar arası geçiş mevcuttur).

---

## 3. RAG Pipeline Geliştirmeleri

- **Vektörleştirme:** Her bir tarif parçası, embedding modeli aracılığıyla 384 boyutlu sayısal vektörlere dönüştürülerek ChromaDB'ye kaydedilmiştir.
- **Geri Çağırma (Retrieval):** Kullanıcı bir girdi verdiğinde, sistem bu girdiyi vektörleştirip veritabanındaki en benzer 4 (günlük menü için) veya 2 (tek öğün için) tarifi bulur.
- **Structured Output (Yapılandırılmış Çıktı):** Pydantic modelleri kullanılarak AI'nın cevabı her zaman geçerli bir JSON formatında vermesi sağlanmıştır.
    - `RecipeResponse`: Tek öğün analizleri için.
    - `DailyMenuResponse`: Kahvaltı, Öğle ve Akşam sekmelerini içeren tam gün planlaması için.

---

## 4. Yapılan Yenilikler ve İyileştirmeler

### A. Günlük Menü Mantığı
Sıradan AI uygulamalarından farklı olarak, sistem "Günlük Menü" modunda toplam kalori ve protein hedefini öğünler arasında paylaştıracak şekilde (Kahvaltı %25, Öğle %35, Akşam %40) özel bir mantıkla çalışır.

### B. Veri Seti Genişletme
Prototip aşamasındaki kısıtlı veri seti, sporcu beslenmesine uygun 50 spesifik tarife çıkarılarak RAG sisteminin doğruluğu ve çeşitliliği artırılmıştır.

### C. Gelişmiş UI/UX
Sonuçlar; Kahvaltınızı, Öğle Yemeğinizi ve Akşam Yemeğinizi ayrı sekmelerde, hem malzeme hem de yapılış adımlarıyla tertipli bir şekilde görebileceğiniz modern bir arayüzle sunulmaktadır.

---

## 5. Sonuç ve Değerlendirme

Bu mimari sayesinde LLM'in (Yapay Zeka) en büyük sorunu olan "halüsinasyon" (uydurma) riski, referans alınan gerçek tarif veritabanı sayesinde minimize edilmiştir. Kullanıcı her cevabın altında AI'nın hangi veritabanı kayıtlarından esinlendiğini şeffaf bir şekilde görebilmektedir.
