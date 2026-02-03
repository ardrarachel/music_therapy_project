import re

def analyze_text_sentiment(user_text):
    """
    Part 1: Text Sensor Logic (Bag-of-Words)
    Determines emotion from text using keyword counting.
    """
    text = user_text.lower()
    words = re.findall(r'\b\w+\b', text)
    total_words = len(words) if words else 1

    # Emotion dictionary
    keywords = {
        "Happy": ["happy", "good", "great", "joy", "love", "excellent", "excited", "fun", "best", "smile"],
        "Sadness": ["sad", "bad", "terrible", "cry", "lonely", "depressed", "hurt", "pain", "sorry", "miss"],
        "Anger": ["angry", "mad", "hate", "furious", "annoyed", "stupid", "idiot", "rage", "shut"],
        "Excited": ["wow", "amazing", "can't wait", "hurray", "yay", "boom", "party", "win"],
        "Calm": ["calm", "chill", "relax", "peace", "okay", "fine", "sleep", "breathe", "neutral"]
    }

    scores = {emo: 0 for emo in keywords}

    for word in words:
        for emo, vocab in keywords.items():
            if word in vocab:
                scores[emo] += 1

    # Find winner
    best_emotion = max(scores, key=scores.get)
    hits = scores[best_emotion]

    # Heuristic Confidence: If hits > 0, confidence = hits / total_words (capped). 
    # If 0 hits, default to Neutral.
    if hits == 0:
        return "Neutral", 0.50
    
    # Simple semantic density score
    confidence = min(0.99, 0.5 + (hits / total_words)) 
    
    return best_emotion, round(confidence, 2)


def fuse_multimodal_sensors(face_data, voice_data, user_text):
    """
    Part 2: The Fusion Logic (Squared Weighting Algorithm)
    Fuses Face, Voice, and Text inputs.
    """
    
    # --- STEP A: Gather Inputs ---
    
    # 1. Face Input
    # face_data expected: {'emotion': 'Happy', 'confidence': 0.65}
    # If simple string comes in, normalize it.
    face_emo = face_data.get('emotion', "Neutral")
    # Clean up descriptive strings like "Happy: Corners lifted..."
    if ":" in face_emo: face_emo = face_emo.split(":")[0]
    face_conf = face_data.get('confidence', 0.60) # Default if measuring is hard
    
    # 2. Voice Input
    voice_emo = voice_data.get('emotion', "Neutral")
    voice_conf = voice_data.get('energy_score', 0.5) + voice_data.get('pitch_score', 0.5) # Heuristic
    # Normalize voice confidence to 0.5 - 0.95 range
    voice_conf = min(0.95, max(0.4, voice_conf))
    
    # 3. Text Input
    text_emo, text_conf = analyze_text_sentiment(user_text)


    # --- STEP B: Squared Weighting Algorithm ---
    # Formula: W = C^2 / Sum(C^2)
    
    c_face_sq = face_conf ** 2
    c_voice_sq = voice_conf ** 2
    c_text_sq = text_conf ** 2
    
    sum_sq = c_face_sq + c_voice_sq + c_text_sq
    
    w_face = c_face_sq / sum_sq
    w_voice = c_voice_sq / sum_sq
    w_text = c_text_sq / sum_sq
    
    # --- STEP C: Scoring the Candidates ---
    # We sum the weights of each sensor into the buckets of their voted emotion.
    
    scores = {}
    
    def add_score(emotion, weight):
        scores[emotion] = scores.get(emotion, 0) + weight
        
    add_score(face_emo, w_face)
    add_score(voice_emo, w_voice)
    add_score(text_emo, w_text)
    
    # Pick Winner
    final_decision = max(scores, key=scores.get)
    result_score = scores[final_decision]


    # --- PART 3: Terminal Visualization (Forensic Report) ---
    print("\n" + "="*40)
    print("[TRI-MODAL FUSION LOGIC]")
    print("   INPUTS:")
    print(f"   👁️ Face:  {face_emo:<10} (Conf: {face_conf:.2f})")
    print(f"   🎤 Voice: {voice_emo:<10} (Int:  {voice_conf:.2f})")
    print(f"   ⌨️ Text:  {text_emo:<10} (Conf: {text_conf:.2f})")
    print("\n   MATH CALCULATIONS:")
    print(f"   ∑(Conf²): {c_face_sq:.2f} + {c_voice_sq:.2f} + {c_text_sq:.2f} = {sum_sq:.2f}")
    print(f"   ⚖️ W_Face  = {c_face_sq:.2f} / {sum_sq:.2f} = {w_face:.2f}")
    print(f"   ⚖️ W_Voice = {c_voice_sq:.2f} / {sum_sq:.2f} = {w_voice:.2f}")
    print(f"   ⚖️ W_Text  = {c_text_sq:.2f} / {sum_sq:.2f} = {w_text:.2f}")
    print("\n   SCORING:")
    
    # Print logic explaining the sum
    for emo, score in scores.items():
        contributors = []
        if face_emo == emo: contributors.append(f"{w_face:.2f} (Face)")
        if voice_emo == emo: contributors.append(f"{w_voice:.2f} (Voice)")
        if text_emo == emo: contributors.append(f"{w_text:.2f} (Text)")
        
        math_str = " + ".join(contributors)
        print(f"   {emo:<10} Score: {math_str} = {score:.2f}")

    print(f"\n   🏆 FINAL DECISION: {final_decision}")
    print("="*40 + "\n")

    return {
        "final_mood": final_decision,
        "confidence": round(result_score, 2),
        "reasoning": f"Winner by Squared Weighting ({result_score:.2f})"
    }
