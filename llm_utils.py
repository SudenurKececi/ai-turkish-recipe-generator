import os
import json

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# .env dosyasını oku (GOOGLE_API_KEY için)
load_dotenv()


def build_llm():
    """
    Gemini modelini oluşturan yardımcı fonksiyon.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY bulunamadı. .env dosyanı kontrol et.")

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
    )


def parse_llm_json(raw: str) -> dict:
    """
    LLM bazen cevabı ```json ... ``` bloğu içinde döndüğü için
    önce kod bloklarını temizleyip sadece { ... } kısmını ayıklıyoruz.
    Sonra json.loads ile parse ediyoruz.
    """
    text = raw.strip()

    # Kod bloğu varsa (```json ... ```) içinden al
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            if "{" in part and "}" in part:
                text = part
                break

    # İlk '{' ve son '}' arasını al
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    return json.loads(text)


# Tarif ürettirmek için kullanacağımız prompt
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


def generate_recipes(ingredients: str, servings: int, extra_constraints: str):
    """
    Verilen malzemeler ve kısıtlarla Gemini'den tarif listesi çek.
    recipes, shopping_list, raw_text döndürür.
    """
    llm = build_llm()
    chain = prompt | llm

    response = chain.invoke(
        {
            "ingredients": ingredients,
            "servings": servings,
            "extra_constraints": extra_constraints,
        }
    )

    raw = getattr(response, "text", None) or response.content
    data = parse_llm_json(raw)

    recipes = data.get("recipes", [])
    shopping_list = data.get("shopping_list", [])

    return recipes, shopping_list, raw
