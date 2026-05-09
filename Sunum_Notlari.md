# AI Şef & Sporcu Menüleri - Sunum Notları

Hocana sunum yaparken bu akışı takip edebilirsin.

---

## 1. Giriş: Problem ve Çözüm
- **Soru:** Neden bu projeyi yaptık?
- **Cevap:** Sporcuların hem ellerindeki malzemeyi değerlendirmesi hem de kalori/protein hedeflerine uyması zordur. Biz bu süreci otomatize ettik.

## 2. Teknik Mimari (RAG Nedir?)
- **Anlatım:** "Sistemimiz bir RAG (Retrieval-Augmented Generation) mimarisidir. Yapay zekaya sadece sormuyoruz; önce veritabanımızda (ChromaDB) arama yapıyoruz, en uygun tarifleri bulup yapay zekaya 'bu verilere bakarak cevap ver' diyoruz."

## 3. Veri İşleme (Pipeline)
- **Veri:** 50 adet sağlıklı tarif.
- **Chunking:** 400 karakter parça boyutu.
- **Embedding:** `all-MiniLM-L6-v2`. (Neden bu model? Çünkü hızlı, ücretsiz ve lokal çalışıyor).
- **Vektör DB:** ChromaDB.

## 4. Akıllı Menü Mantığı
- **Farkımız:** Sadece tarif yazmıyoruz. Kullanıcı "Günlük Menü" istediğinde, sistem toplam kaloriyi öğünlere bölüyor. 
- **Teknik Detay:** Pydantic `BaseModel` kullanarak yapay zekadan gelen ham metni yapılandırılmış (structured) veriye dönüştürüyoruz. Bu sayede arayüzde (Streamlit) sekmeli ve düzenli bir görünüm elde ediyoruz.

## 5. Uygulama Demosu (Gösterilecek Kısımlar)
- Sol menüden LLM motoru seçimi (OpenAI/Gemini).
- Malzeme girişi ve makro hedefleri.
- "Günlük Menü" butonuna basınca çıkan Kahvaltı/Öğle/Akşam sekmeleri.
- Sayfanın en altındaki "RAG Context" kısmı (Hocaya AI'nın hangi veriden beslendiğini kanıtlamak için burayı mutlaka göster).

---

### Hocanın Sorabileceği Olası Sorular:
- **S: Neden verileri parçalara (chunk) ayırdın?**
- *C: Çünkü LLM'lerin bir context window (bağlam penceresi) sınırı vardır. Tüm tarifleri bir anda gönderemeyiz. Sadece en alakalı parçaları göndererek hem maliyeti düşürüyoruz hem de doğruluğu artırıyoruz.*

- **S: Pydantic ne işe yarıyor?**
- *C: Yapay zekadan gelen cevabın her zaman belirlediğimiz şablona (tarif adı, malzemeler, makrolar) uymasını garanti altına alıyor.*
