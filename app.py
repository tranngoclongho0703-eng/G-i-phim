from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer, util
from transformers import MarianTokenizer, MarianMTModel
import pandas as pd
import torch

# ==============================
# 1. KHỞI TẠO FLASK
# ==============================

app = Flask(__name__)
CORS(app)

# ==============================
# 2. THIẾT BỊ
# ==============================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Device:", device)

# ==============================
# 3. LOAD SENTENCE-BERT
# ==============================

model_path = "sbert_ft_tmdb_manual"

print("Đang tải Sentence-BERT...")
model = SentenceTransformer(model_path)
model.to(device)

# ==============================
# 4. LOAD DỮ LIỆU PHIM
# ==============================

print("Đang tải dữ liệu phim...")

movie_data = pd.read_csv("movie_data.csv")

movie_titles = movie_data["title"].tolist()
movie_tags = movie_data["tags"].fillna("").tolist()

print("Số lượng phim:", len(movie_titles))

# ==============================
# 5. TẠO MOVIE EMBEDDINGS
# ==============================

print("Đang tạo embeddings cho 4806 phim...")

movie_embeddings = model.encode(
    movie_tags,
    convert_to_tensor=True,
    show_progress_bar=True
)

# ==============================
# 6. LOAD MODEL DỊCH VIỆT → ANH
# ==============================

print("Đang tải model dịch Việt → Anh...")

translator_name = "Helsinki-NLP/opus-mt-vi-en"

tokenizer_trans = MarianTokenizer.from_pretrained(
    translator_name
)

model_trans = MarianMTModel.from_pretrained(
    translator_name
)

model_trans.to(device)
model_trans.eval()

# ==============================
# 7. NHẬN DIỆN TIẾNG VIỆT
# ==============================

def is_vietnamese(text):

    vietnamese_chars = (
        "àáảãạ"
        "âầấẩẫậ"
        "ăằắẳẵặ"
        "èéẻẽẹ"
        "êềếểễệ"
        "đ"
        "ìíỉĩị"
        "òóỏõọ"
        "ôồốổỗộ"
        "ơờớởỡợ"
        "ùúủũụ"
        "ưừứửữự"
        "ỳýỷỹỵ"
    )

    return any(
        char in vietnamese_chars
        for char in text.lower()
    )


# ==============================
# 8. DỊCH VIỆT → ANH
# ==============================

def translate_vi_to_en(text):

    inputs = tokenizer_trans(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=256
    )

    inputs = {
        key: value.to(device)
        for key, value in inputs.items()
    }

    with torch.no_grad():

        translated = model_trans.generate(
            **inputs,
            num_beams=5,
            do_sample=False,
            max_length=256
        )

    result = tokenizer_trans.decode(
        translated[0],
        skip_special_tokens=True
    )

    return result.strip()


# ==============================
# 9. XỬ LÝ QUERY
# ==============================

def process_query(text):

    text = text.strip()

    if is_vietnamese(text):

        translated = translate_vi_to_en(text)

        return translated

    return text


# ==============================
# 10. API RECOMMEND
# ==============================

@app.route("/recommend", methods=["POST"])
def recommend():

    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "error": "Không nhận được JSON hợp lệ"
            }), 400

        query = str(data.get("query", "")).strip()

        if not query:
            return jsonify({
                "error": "Query is empty"
            }), 400

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 400

    print("\nQuery:", query)

    # Xử lý ngôn ngữ
    processed_query = process_query(query)

    print("Processed:", processed_query)

    # Query embedding
    query_embedding = model.encode(
        processed_query,
        convert_to_tensor=True
    )

    # Cosine Similarity
    cosine_scores = util.cos_sim(
        query_embedding,
        movie_embeddings
    )[0]

    # Top 5
    top_results = torch.topk(
        cosine_scores,
        k=5
    )

    results = []

    for score, idx in zip(
        top_results[0],
        top_results[1]
    ):

        results.append({
            "title": movie_titles[int(idx)],
            "similarity": round(
                float(score),
                4
            )
        })

    return jsonify({
        "original_query": query,
        "processed_query": processed_query,
        "results": results
    })

    if not query:

        return jsonify({
            "error": "Query is empty"
        }), 400

    print("\nQuery:", query)

    # Xử lý ngôn ngữ
    processed_query = process_query(query)

    print("Processed:", processed_query)

    # Query embedding
    query_embedding = model.encode(
        processed_query,
        convert_to_tensor=True
    )

    # Cosine Similarity
    cosine_scores = util.cos_sim(
        query_embedding,
        movie_embeddings
    )[0]

    # Top 5
    top_results = torch.topk(
        cosine_scores,
        k=5
    )

    results = []

    for score, idx in zip(
        top_results[0],
        top_results[1]
    ):

        results.append({
            "title": movie_titles[idx],
            "similarity": round(
                float(score),
                4
            )
        })

    return jsonify({
        "original_query": query,
        "processed_query": processed_query,
        "results": results
    })


# ==============================
# 11. CHẠY SERVER
# ==============================

if __name__ == "__main__":

    print("\n==============================")
    print("MOVIE RECOMMENDER SERVER")
    print("==============================")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )