import io

import streamlit as st
from PIL import Image

from llm_utils import generate_recipes
from vision_utils import extract_ingredients_from_image_with_gemini


def render_header():
    """Sayfanın üstündeki basit header bar."""
    st.markdown(
        """
        <style>
        .mfk-header {
            border-radius: 12px;
            padding: 0.75rem 1rem;
            margin-bottom: 1rem;
            border: 1px solid rgba(148,163,184,0.6);
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        .mfk-header-icon {
            font-size: 2rem;
        }
        .mfk-header-title {
            font-weight: 600;
            font-size: 1.1rem;
        }
        .mfk-header-subtitle {
            font-size: 0.9rem;
            opacity: 0.8;
        }
        </style>
        <div class="mfk-header">
          <div class="mfk-header-icon">🍳</div>
          <div>
            <div class="mfk-header-title">Mutfak Bilgini</div>
            <div class="mfk-header-subtitle">
              Elindeki malzemelerle veya fotoğrafla Türk yemekleri keşfet.
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_recipe_card(recipe, default_servings, meal_type_filter, diet_filter):
    """Tarif detayını tek bir yerde çizmek için yardımcı fonksiyon."""
    name = recipe.get("name", "İsimsiz Tarif")
    r_servings = recipe.get("servings", default_servings)
    time_minutes = recipe.get("time_minutes", "?")
    difficulty = recipe.get("difficulty", "?")
    r_meal_type = recipe.get(
        "meal_type",
        meal_type_filter if meal_type_filter not in ("", "Farketmez") else "",
    )
    r_diet = recipe.get(
        "diet",
        diet_filter if diet_filter not in ("", "Yok") else "",
    )

    # Kartın dış çerçevesi: sadece border + padding, renkleri temaya bırakıyoruz
    st.markdown(
        """
        <div style="
            border: 1px solid rgba(148,163,184,0.6);
            border-radius: 10px;
            padding: 0.9rem 1rem;
            margin: 0.6rem 0 1rem 0;
        ">
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"### 🍽️ {name}")

    info_line = f"👥 {r_servings} kişilik | ⏱️ {time_minutes} dk"
    if difficulty:
        info_line += f" | Zorluk: **{difficulty}**"
    if r_meal_type:
        info_line += f" | Tür: {r_meal_type}"
    if r_diet:
        info_line += f" | Diyet: {r_diet}"

    st.write(info_line)

    st.markdown("---")

    st.markdown("**🧺 Elimizde olan malzemeler:**")
    have = recipe.get("ingredients_have", [])
    st.write(", ".join(have) if have else "-")

    st.markdown("**🧾 Eksik malzemeler:**")
    missing = recipe.get("ingredients_missing", [])
    st.write(", ".join(missing) if missing else "-")

    st.markdown("**👩‍🍳 Yapılış adımları:**")
    steps = recipe.get("steps", [])
    if steps:
        for i, step in enumerate(steps, start=1):
            st.markdown(f"{i}. {step}")
    else:
        st.write("-")

    # Kart kapatma
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="Mutfak Bilgini", page_icon="🍳")

    # --- Session state başlangıçları ---
    if "favorites" not in st.session_state:
        st.session_state["favorites"] = []
    if "last_recipes" not in st.session_state:
        st.session_state["last_recipes"] = []
    if "last_shopping_list" not in st.session_state:
        st.session_state["last_shopping_list"] = []

    # Üst header bar
    render_header()

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

    # --- Sekmeler ---
    tab_search, tab_favs = st.tabs(["🔍 Tarif Bul", "⭐ Favorilerim"])

    # ===== TAB 1: TARİF BUL =====
    with tab_search:
        # 1) Fotoğraf yükleme
        st.subheader("1️⃣ İstersen fotoğraf yükle (opsiyonel)")
        uploaded_file = st.file_uploader(
            "Mutfak tezgahının veya malzemelerin fotoğrafını yükle",
            type=["jpg", "jpeg", "png"],
            key="file_uploader",
        )

        if uploaded_file is not None:
            image = Image.open(io.BytesIO(uploaded_file.getvalue())).convert("RGB")
            st.image(image, caption="Yüklenen fotoğraf", use_column_width=True)

            if st.button("📸 Fotoğraftan malzemeleri çıkar (Gemini)", key="extract_btn"):
                with st.spinner("Gemini fotoğrafı analiz ediyor..."):
                    ingredients, _ = extract_ingredients_from_image_with_gemini(
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

                    existing = st.session_state.get("ingredients_input", "").strip()
                    if existing:
                        st.session_state["ingredients_input"] = (
                            existing + ", " + readable
                        )
                    else:
                        st.session_state["ingredients_input"] = readable

        st.markdown("---")

        # 2) Metin ile malzeme girişi / düzenleme
        st.subheader("2️⃣ Elindeki malzemeleri yaz veya düzenle")
        st.write("Örnek: `domates, kıyma, soğan, pirinç, salça`")

        ingredients_input = st.text_area(
            label="Malzemeler",
            height=120,
            placeholder="Elindeki malzemeleri virgülle ayırarak yaz...",
            key="ingredients_input",
        )

        # 3) LLM'den tarif isteme (state güncelleme)
        if st.button("🧠 Tarif öner", key="generate_btn"):
            if not ingredients_input.strip():
                st.warning("Lütfen en az bir malzeme gir.")
            else:
                with st.spinner("Gemini tarifleri hazırlıyor..."):
                    try:
                        recipes, shopping_list, _ = generate_recipes(
                            ingredients=ingredients_input,
                            servings=servings,
                            extra_constraints=extra_constraints,
                        )
                    except Exception as e:
                        st.error(f"Tarif üretilirken hata oluştu: {e}")
                    else:
                        if not recipes:
                            st.warning(
                                "Herhangi bir tarif bulunamadı. Malzeme listenizi veya filtreleri biraz değiştirmeyi deneyin."
                            )
                        else:
                            st.session_state["last_recipes"] = recipes
                            st.session_state["last_shopping_list"] = shopping_list

        # 3B) STATE'TEKİ TARİFLERİ GÖSTER
        recipes = st.session_state["last_recipes"]
        shopping_list = st.session_state["last_shopping_list"]

        if recipes:
            st.subheader("3️⃣ Önerilen tarifler")

            for idx, r in enumerate(recipes):
                render_recipe_card(r, servings, meal_type, diet)

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

            if shopping_list:
                st.subheader("🛒 Alışveriş listesi")
                st.write(", ".join(shopping_list))

    # ===== TAB 2: FAVORİLER =====
    with tab_favs:
        st.subheader("⭐ Favori tariflerin")

        if not st.session_state["favorites"]:
            st.write("Henüz favoriye eklenmiş bir tarif yok.")
        else:
            for idx, fav in enumerate(st.session_state["favorites"]):
                render_recipe_card(fav, fav.get("servings", 2), "", "")

                # Favoriden sil butonu
                if st.button(
                    "🗑️ Bu tarifi favorilerden sil",
                    key=f"del_fav_{idx}",
                ):
                    st.session_state["favorites"].pop(idx)
                    st.success("Tarif favorilerden silindi.")
                    st.rerun()


if __name__ == "__main__":
    main()
