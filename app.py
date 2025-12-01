import os
import io
import base64
import json

import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI


# 1) .env dosyasını yükle
load_dotenv()


# 2) Gemini modelini hazırlayan fonksiyon
def build_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY bulunamadı. .env dosyandaki değeri kontrol et."
        )

    # gemini-2.5-flash hem metin hem görseli destekliyor
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
    )
    return llm


# 3) FOTOĞRAFTAN MALZEME ÇEKEN FONKSİYON (GEMINI VISION)
def extract_ingredients_from_image_with_gemini(uploaded_file):
    """
    Streamlit UploadedFile alır, Gemini'ye gönderip
    fotoğraftaki malzemeleri liste halinde döndürür.
    """
    llm = build_llm()

    # UploadedFile -> raw bytes
    image_bytes = uploaded_file.getvalue()
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    # Gemini'ye text + image birlikte gönderiyoruz
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": """
Bu bir mutfak fotoğrafı.
Bu fotoğraftaki YENİLEBİLİR gıda malzemelerini listele.

Kurallar:
- Sadece açıkça görünen gıda malzemelerini yaz (domates, biber, soğan, patates, yumurta, süt vb.).
- Her satırda SADECE malzeme adı olsun.
- Türkçe ve küçük harfle yaz.
- Açıklama yazma, sadece liste.

Örnek çıktı:
domates
biber
soğan
""",
            },
            {
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{encoded_image}",
            },
        ]
    )

    response = llm.invoke([message])
    raw = getattr(response, "text", None) or response.content

    # Gelen metni satır satır temizleyip liste haline getirelim
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    ingredients = []
    for ln in lines:
        # başındaki "-" vs. temizle
        ln = ln.lstrip("-•*0123456789. ").strip().lower()
        if ln and ln not in ingredients:
            ingredients.append(ln)

    return ingredients, raw


# 4) LLM JSON'unu güvenli parse eden yardımcı fonksiyon
def parse_llm_json(raw: str):
    """
    LLM bazen cevabı ```json ... ``` kod bloğu içinde döndüğü için
    bu fonksiyon önce sadece { ... } kısmını çıkarır, sonra json.loads yapar.
    """
    text = raw.strip()

    # Kod bloğu varsa (```json ... ```) içinden al
    if "```" in text:
        parts = text.split("```")
        # İçinde { ve } olan ilk bloğu seç
        for part in parts:
            if "{" in part and "}" in part:
                text = part
                break

    # İlk '{' ve son '}' arasını al
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    # Artık sadece JSON kalmış olmalı
    return json.loads(text)


# 5) TARİF ÜRETME PROMPT'U (JSON İSTİYORUZ, EN AZ 3 TARİF)
prompt = ChatPromptTemplate.from_template(
    """
Sen Türk mutfağı konusunda uzman bir aşçısın.

Elimde şu malzemeler var:
{ingredients}

Kısıtlar:
{extra_constraints}

Varsayılan kişi sayısı: {servings} kişilik.

EN AZ 3 ve mümkünse 4–5 FARKLI yemek öner.

Cevabı AŞAĞIDAKİ JSON formatında ver.
Ekstra açıklama yazma, sadece GEÇERLİ bir JSON ver.

Beklenen JSON şeması:

{{
  "recipes": [
    {{
      "name": "yemek adı",
      "servings": 2,
      "time_minutes": 30,
      "difficulty": "kolay",
      "meal_type": "ana yemek",
      "diet": "vegan",
      "ingredients_have": ["malzeme1", "malzeme2"],
      "ingredients_missing": ["eksik1", "eksik2"],
      "steps": ["adım1", "adım2", "adım3"]
    }}
  ],
  "shopping_list": ["eksik1", "eksik2"]
}}

Kurallar:
- JSON dışında hiçbir şey yazma.
- Tek bir JSON objesi döndür.
- "recipes" listesinde EN AZ 3 tarif olsun.
- Tüm alanları doldurmaya çalış.
"""
)


def main():
    st.set_page_config(page_title="Mutfak Bilgini", page_icon="🍳")

    # --- Session state başlangıçları ---
    if "favorites" not in st.session_state:
        st.session_state["favorites"] = []
    if "last_recipes" not in st.session_state:
        st.session_state["last_recipes"] = []
    if "last_shopping_list" not in st.session_state:
        st.session_state["last_shopping_list"] = []

    st.title("🍳 Mutfak Bilgini")
    st.write(
        "Elindeki malzemeleri yaz veya fotoğraf yükle, sana Türk mutfağından tarifler önereyim (Gemini metin + görsel)."
    )

    # --- Yan panel: ayarlar + filtreler ---
    with st.sidebar:
        st.header("Ayarlar")
        servings = st.slider(
            "Kaç kişilik tarif istersin?", min_value=1, max_value=8, value=2
        )

        st.subheader("Filtreler")
        meal_type = st.selectbox(
            "Yemek türü",
            ["Farketmez", "Ana yemek", "Çorba", "Tatlı", "Meze", "Kahvaltı"],
        )
        diet = st.selectbox(
            "Diyet tercihi",
            ["Yok", "Vegan", "Vejetaryen"],
        )
        max_time = st.selectbox(
            "Maksimum süre (dk)",
            ["Farketmez", "20", "30", "45", "60"],
        )

        st.markdown("---")
        st.caption(
            "Fotoğraftan malzeme tanıma Gemini Vision ile yapılıyor; sonuçları her zaman aşağıda düzenleyebilirsin."
        )

    # Filtrelerden gelen kısıtları tek string halinde hazırlayalım
    constraints = []
    if meal_type != "Farketmez":
        constraints.append(f"Yemek türü: {meal_type.lower()} olmalı.")
    if diet != "Yok":
        constraints.append(f"Tarifler {diet.lower()} olmalı.")
    if max_time != "Farketmez":
        constraints.append(
            f"Tariflerin pişirme süresi en fazla {max_time} dakika olmalı."
        )

    extra_constraints = "\n".join(constraints) if constraints else "Özel bir kısıt yok."

    # --- 1) Fotoğraf yükleme ---
    st.subheader("1️⃣ İstersen fotoğraf yükle (opsiyonel)")
    uploaded_file = st.file_uploader(
        "Mutfak tezgahının veya malzemelerin fotoğrafını yükle",
        type=["jpg", "jpeg", "png"],
    )

    if uploaded_file is not None:
        # UploadedFile'dan image oluşturmak için bytes kullanıyoruz
        image = Image.open(io.BytesIO(uploaded_file.getvalue())).convert("RGB")
        st.image(image, caption="Yüklenen fotoğraf", use_column_width=True)

        if st.button("Fotoğraftan malzemeleri çıkar (Gemini)"):
            with st.spinner("Gemini fotoğrafı analiz ediyor..."):
                ingredients, raw_text = extract_ingredients_from_image_with_gemini(
                    uploaded_file
                )

            if not ingredients:
                st.warning(
                    "Gemini bu fotoğrafta net malzemeler bulamadı. "
                    "Farklı bir açı/ışıkla tekrar deneyebilir veya malzemeleri elle yazabilirsin."
                )
            else:
                readable = ", ".join(ingredients)
                st.success(f"Bulunan malzemeler: {readable}")

                # Metin kutusuna otomatik doldur
                existing = st.session_state.get("ingredients_input", "").strip()
                if existing:
                    st.session_state["ingredients_input"] = existing + ", " + readable
                else:
                    st.session_state["ingredients_input"] = readable

    st.markdown("---")

    # --- 2) Metin ile malzeme girişi / düzenleme ---
    st.subheader("2️⃣ Elindeki malzemeleri yaz veya düzenle")
    st.write("Örnek: `domates, kıyma, soğan, pirinç, salça`")

    ingredients_input = st.text_area(
        label="Malzemeler",
        height=120,
        placeholder="Elindeki malzemeleri virgülle ayırarak yaz...",
        key="ingredients_input",  # fotoğraftan otomatik doldurmak için önemli
    )

    # --- 3) LLM'den tarif isteme (sadece state'i güncelliyor) ---
    if st.button("Tarif öner 🧠"):
        if not ingredients_input.strip():
            st.warning("Lütfen en az bir malzeme gir.")
        else:
            try:
                llm = build_llm()
            except Exception as e:
                st.error(f"LLM başlatılırken hata oluştu: {e}")
                st.info(
                    ".env dosyandaki GOOGLE_API_KEY satırını ve Gemini anahtarını kontrol et."
                )
            else:
                chain = prompt | llm

                with st.spinner("Gemini tarifleri hazırlıyor..."):
                    try:
                        response = chain.invoke(
                            {
                                "ingredients": ingredients_input,
                                "servings": servings,
                                "extra_constraints": extra_constraints,
                            }
                        )
                        raw = getattr(response, "text", None) or response.content

                        # JSON'a güvenli şekilde çevirmeyi dene
                        try:
                            data = parse_llm_json(raw)
                        except Exception:
                            st.error(
                                "Model beklenen JSON formatında cevap vermedi. Ham çıktıyı gösteriyorum:"
                            )
                            st.markdown(raw)
                        else:
                            recipes = data.get("recipes", [])
                            shopping_list = data.get("shopping_list", [])

                            if not recipes:
                                st.warning(
                                    "Herhangi bir tarif bulunamadı. Malzeme listenizi veya filtreleri biraz değiştirmeyi deneyin."
                                )
                            else:
                                # SONUÇLARI STATE'E KAYDET
                                st.session_state["last_recipes"] = recipes
                                st.session_state["last_shopping_list"] = shopping_list
                    except Exception as e:
                        st.error(f"Bir hata oluştu: {e}")
                        st.info(
                            "İnternet bağlantını ve Gemini API kotanı kontrol et. Sorun devam ederse hata mesajını bana gönder."
                        )

    # --- 3B) STATE'TEKİ TARİFLERİ HER ZAMAN GÖSTER ---
    recipes = st.session_state["last_recipes"]
    shopping_list = st.session_state["last_shopping_list"]

    if recipes:
        st.subheader("3️⃣ Önerilen tarifler")

        for idx, r in enumerate(recipes):
            name = r.get("name", "İsimsiz Tarif")
            r_servings = r.get("servings", servings)
            time_minutes = r.get("time_minutes", "?")
            difficulty = r.get("difficulty", "?")
            r_meal_type = r.get(
                "meal_type",
                meal_type if meal_type != "Farketmez" else "",
            )
            r_diet = r.get("diet", diet if diet != "Yok" else "")

            # Kart başlığı
            st.markdown(f"### 🍽️ {name}")

            # Bilgi satırı
            info_line = f"👥 {r_servings} kişilik | ⏱️ {time_minutes} dk"
            if difficulty:
                info_line += f" | Zorluk: **{difficulty}**"
            if r_meal_type:
                info_line += f" | Tür: {r_meal_type}"
            if r_diet:
                info_line += f" | Diyet: {r_diet}"

            st.write(info_line)

            # Malzemeler
            st.markdown("**Elimizde olan malzemeler:**")
            have = r.get("ingredients_have", [])
            st.write(", ".join(have) if have else "-")

            st.markdown("**Eksik malzemeler:**")
            missing = r.get("ingredients_missing", [])
            st.write(", ".join(missing) if missing else "-")

            # Adımlar
            st.markdown("**Yapılış adımları:**")
            steps = r.get("steps", [])
            if steps:
                for i, step in enumerate(steps, start=1):
                    st.markdown(f"{i}. {step}")
            else:
                st.write("-")

            # Favorilere ekle butonu
            if st.button(
                "⭐ Bu tarifi favorilere ekle",
                key=f"fav_btn_{idx}",
            ):
                names_in_favs = [
                    f.get("name") for f in st.session_state["favorites"]
                ]
                if r.get("name") not in names_in_favs:
                    st.session_state["favorites"].append(r)
                    st.success("Tarif favorilere eklendi.")
                else:
                    st.info("Bu tarif zaten favorilerinde yer alıyor.")

            st.markdown("---")

        # Alışveriş listesi
        if shopping_list:
            st.subheader("🛒 Alışveriş listesi")
            st.write(", ".join(shopping_list))

    # --- 4) Favori tarifler bölümü ---
    st.subheader("⭐ Favori tariflerin")
    if not st.session_state["favorites"]:
        st.write("Henüz favoriye eklenmiş bir tarif yok.")
    else:
        for fav in st.session_state["favorites"]:
            st.markdown(f"#### 🍽️ {fav.get('name', 'İsimsiz Tarif')}")
            info_line = (
                f"👥 {fav.get('servings', '?')} kişilik | "
                f"⏱️ {fav.get('time_minutes', '?')} dk"
            )
            st.write(info_line)
        st.markdown("---")


if __name__ == "__main__":
    main()
