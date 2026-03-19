from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def retrieve_top_m(cv_text: str, job_texts: list[str], M: int = 10):
    vec = TfidfVectorizer(ngram_range=(1,2), stop_words="english")
    job_matrix = vec.fit_transform(job_texts)
    cv_vec = vec.transform([cv_text])
    scores = cosine_similarity(cv_vec, job_matrix).flatten()
    top_idx = scores.argsort()[::-1][:M]
    return [(int(i), float(scores[i])) for i in top_idx]