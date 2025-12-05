"""
Temporary runtime memory shared between /analyze and /chat.
"""

# Vector DBs (after /analyze)
resume_db = None
jd_db = None

# Only keep things needed
resume_text = ""
jd_text = ""

similarity_score = None
match_score = None
