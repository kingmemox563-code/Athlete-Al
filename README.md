# AthletePro AI - RAG Tabanlı Sporcu Beslenme Platformu

AthletePro AI, sporcuların performanslarını optimize etmek için geliştirilmiş, **RAG (Retrieval-Augmented Generation)** mimarisini kullanan gelişmiş bir yapay zeka platformudur.

## 🚀 Özellikler

- **Akıllı Tarif Üretimi:** 100+ özel sporcu tarifinden oluşan veri seti ile kişiselleştirilmiş öğün planları.
- **RAG Mimarisi:** Halüsinasyonu minimize eden, tamamen gerçek verilere dayalı yanıtlar.
- **Multimodal Destek:** GPT-4o ile gelişmiş analiz ve DALL-E 3 ile fotogerçekçi yemek görselleri.
- **Kompakt Raporlama:** Proje detaylarını ve mimariyi özetleyen otomatik Word raporu üretimi.

## 🛠️ Mimari Adımlar

1. **Indexing:** Verilerin temizlenmesi ve ChromaDB vektör veritabanına indekslenmesi.
2. **Retrieval:** Kullanıcı sorgusuyla en alakalı bilgilerin anlamsal olarak getirilmesi.
3. **Augmentation:** Getirilen bilgilerin prompt içine entegre edilmesi.
4. **Generation:** GPT-4o ile profesyonel yanıt üretimi.

## 📦 Kurulum

1. Repoyu klonlayın:
   ```bash
   git clone <repo-url>
   ```

2. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

3. Uygulamayı başlatın:
   ```bash
   streamlit run app.py
   ```

## 📄 Dosya Yapısı

- `app.py`: Ana Streamlit uygulaması.
- `generate_pro_report.py`: Teknik rapor oluşturma scripti.
- `data/`: Ham tarif verileri.
- `chroma_db/`: Vektör veritabanı dosyaları (yerelde tutulur).

## 📝 Lisans

Bu proje eğitim ve geliştirme amaçlıdır.
