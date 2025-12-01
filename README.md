Markdown

# 🍳 AI Turkish Recipe Generator (AI Türk Yemek Tarifi Oluşturucu)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT-green?style=for-the-badge&logo=openai&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-orange?style=for-the-badge)

**Evinizdeki malzemelerle Türk mutfağının en lezzetli tariflerini saniyeler içinde oluşturun!**

[Özellikler](#-özellikler) • [Kurulum](#-kurulum) • [Kullanım](#-kullanım) • [İletişim](#-iletişim)

</div>

---

## 📖 Proje Hakkında

**AI Turkish Recipe Generator**,
"Bugün ne pişirsem?" derdine son veren yapay zeka destekli bir web uygulamasıdır. Kullanıcıların ellerindeki malzemeleri girmesiyle, yapay zeka bu malzemelere en uygun Türk yemeğini, gerekli porsiyonları ve adım adım hazırlanış sürecini sunar.

Klasik tarif sitelerinin aksine, bu proje statik bir veritabanı kullanmaz; her tarifi o anki malzemelerinize özel olarak *üretir*.

### 🎯 Neden Bu Proje?
* 🗑️ **Sıfır Atık:** Dolapta kalan tekil malzemeleri değerlendirerek israfı önler.
* ⚡ **Hızlı Çözüm:** Dakikalarca tarif aramak yerine saniyeler içinde sonuç alırsınız.
* 🇹🇷 **Türk Mutfağı:** Yöresel damak tadına uygun tarifler üretir.

---

## ✨ Özellikler

* **🍅 Akıllı Malzeme Analizi:** Girilen malzemeleri (örn: patlıcan, kıyma, domates) analiz eder.
* **🥘 Kategori Seçimi:** Çorba, Ana Yemek, Tatlı veya Kahvaltılık gibi filtreleme imkanı.
* **📝 Detaylı Tarif Kartı:** Malzeme listesi, hazırlanış süresi, porsiyon bilgisi ve adım adım talimatlar.
* **📱 Modern Arayüz:** Streamlit ile geliştirilmiş, mobil uyumlu ve şık tasarım.

---

## 🛠️ Teknolojiler

Bu proje aşağıdaki teknolojiler kullanılarak geliştirilmiştir:

| Teknoloji | Açıklama |
| :--- | :--- |
| **Python** | Projenin ana programlama dili. |
| **Streamlit** | Web arayüzü ve kullanıcı etkileşimi. |
| **Google Gemini API** | Tarif üretimi için kullanılan Büyük Dil Modeli (LLM). |
| **LangChain** | LLM zincirlerini yönetmek için. |
| **Python-Dotenv** | Ortam değişkenlerini ve API anahtarlarını yönetmek için. |

---

## 🚀 Kurulum

Projeyi yerel bilgisayarınızda çalıştırmak için aşağıdaki adımları sırasıyla uygulayın.

### 1. Projeyi Klonlayın

```bash
git clone [https://github.com/SudenurKececi/ai-turkish-recipe-generator.git](https://github.com/SudenurKececi/ai-turkish-recipe-generator.git)
cd ai-turkish-recipe-generator

Bağımlılıkların çakışmaması için sanal ortam kurulumu önerilir:

# Windows için:
python -m venv venv
venv\Scripts\activate

# macOS / Linux için:
python3 -m venv venv
source venv/bin/activate


3. Kütüphaneleri Yükleyin

pip install -r requirements.txt

4. .env Dosyasını Oluşturun

Proje ana dizininde .env adında bir dosya oluşturun ve API anahtarınızı içine ekleyin:

••• Kod snippet'i

OPENAI_API_KEY="sk-BURAYA_API_ANAHTARINIZI_YAZIN"

💡 Kullanım
Kurulum tamamlandıktan sonra terminale şu komutu yazarak uygulamayı başlatın:
streamlit run app.py

Tarayıcınızda otomatik olarak http://localhost:8501 adresi açılacaktır.

Sol menüden veya ana ekrandan elinizdeki malzemeleri girin.
Yemek kategorisini seçin.
"Tarif Oluştur" butonuna basın ve yapay zekanın sihrini izleyin!

📂 Proje Yapısı
Plaintext

ai-turkish-recipe-generator/
├── .env                # API Anahtarı (Git'e eklenmez)
├── .gitignore          # Git yoksayma dosyası
├── app.py              # Ana uygulama dosyası
├── requirements.txt    # Kütüphane listesi
└── README.md           # Dokümantasyon


📄 Lisans
Bu proje MIT Lisansı ile lisanslanmıştır. Daha fazla bilgi için LICENSE dosyasına bakabilirsiniz.
