import re

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def analyze_text_sentiment(user_text):
    """
    Part 1: Text Sensor Logic (VADER Lexicon-Based Sentiment Analysis)
    Determines emotion from text using Valance Aware Dictionary and sEntiment Reasoner.
    """
    if not user_text.strip() or user_text.strip() == "(Unintelligible)" or user_text.strip() == "No transcription":
        return "Neutral", 0.0

    analyzer = SentimentIntensityAnalyzer()
    sentiment_dict = analyzer.polarity_scores(user_text)
    
    # Compound score ranges from -1 (most extreme negative) to +1 (most extreme positive)
    s_text = sentiment_dict['compound']
    
    # Heuristic Thresholding: Map the Compound Score directly to the valence axis.
    if s_text >= 0.05:
        best_emotion = "Happy" # Positive valence
    elif s_text <= -0.05:
        best_emotion = "Sadness" # Negative valence
    else:
        best_emotion = "Neutral"

    # For confidence, we use the absolute value of the compound score
    # We ensure it has a minimum floor of 0.5 so it doesn't sink the fusion engine too hard if weak
    confidence = max(0.5, abs(s_text))
    
    return best_emotion, round(confidence, 2)

def fuse_multimodal_sensors(face_data, voice_data, user_text):
    """
    Part 2: The Fusion Logic (Squared Weighting Algorithm)
    Fuses Face, Voice, and Text inputs.
    """
    
    # --- STEP A: Gather Inputs ---
    
    # 1. Face Input
    if 'visual_score' in face_data:
        # Expected new structure from backend calibration
        face_emo = face_data.get('main_emotion', 'Neutral')
        face_conf = face_data.get('confidence', 0.5)
    else:
        # Fallback to old behavior
        face_emo = face_data.get('emotion', "Neutral")
        if ":" in face_emo: face_emo = face_emo.split(":")[0]
        face_conf = face_data.get('confidence', 0.60)

    
    # 2. Voice Input
    voice_emo = voice_data.get('emotion', "Neutral")
    voice_conf = voice_data.get('energy_score', 0.5) + voice_data.get('pitch_score', 0.5) # Heuristic
    # Normalize voice confidence to 0.5 - 0.95 range
    voice_conf = min(0.95, max(0.4, voice_conf))
    
    # 3. Text Input
    text_emo, text_conf = analyze_text_sentiment(user_text)

    # --- CLOSED-LOOP CONFLICT RESOLUTION ---
    # Since Face is now voice-triggered (only when RMS > 0.02), if the user says
    # something Negative, but their Face is Happy + Voice variance is high (Excited/Happy),
    # the acoustic & visual modality trumps the linguistic modality (e.g., sarcasm or irony).
    
    if text_emo == "Sadness" or text_emo == "Anger":
        if face_emo == "Happy" and (voice_emo == "Happy" or voice_emo == "Excited"):
            # Trust the acoustic/visual synchronization over the words
            text_emo = "Happy" 
            text_conf = 0.50 # Penalize text confidence for lying
            print("   [OVERRIDE] Sarcasm Detected: Negative Text overridden by Active Happy Face + Voice Variance.")


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
