import base64

from langchain_core.messages import HumanMessage

from llm_utils import build_llm


def extract_ingredients_from_image_with_gemini(uploaded_file):
    """
    Streamlit UploadedFile alır, Gemini'ye gönderip
    fotoğraftaki gıda malzemelerini liste halinde döndürür.
    """
    llm = build_llm()

    image_bytes = uploaded_file.getvalue()
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

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

    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    ingredients = []
    for ln in lines:
        ln = ln.lstrip("-•*0123456789. ").strip().lower()
        if ln and ln not in ingredients:
            ingredients.append(ln)

    return ingredients, raw
