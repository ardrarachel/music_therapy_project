def fuse_emotions(face_input, voice_input):
    """
    Combines Face and Voice emotion inputs to decide the Final Mood.
    Uses pure conditional logic (If-Else) based on psychological rules.
    """
    
    # --- 1. CLEAN & NORMALIZE INPUTS ---
    # Face input comes as a descriptive string (e.g., "Happy: Corners lifted...")
    # We map it to the 5 core categories.
    face = "Neutral"
    if "Happy" in face_input: face = "Happy"
    elif "Sad" in face_input: face = "Sad"
    elif "Surprised" in face_input: face = "Surprise"
    elif "Angry" in face_input: face = "Anger"
    elif "Neutral" in face_input: face = "Neutral"
    
    # Voice input is usually clean, but let's ensure consistency
    voice = voice_input 
    
    print(f"\n   [FUSION ENGINE] Input -> Face: '{face}' | Voice: '{voice}'")

    # --- 2. LOGIC MATRIX (DECISION TREE) ---
    final_mood = "Neutral"
    confidence = 0.0
    reasoning = ""

    # Helper for comparison (Voice 'Sadness' == Face 'Sad')
    voice_as_face_term = voice
    if voice == "Sadness": voice_as_face_term = "Sad"

    # RULE 1: Perfect Match
    if face == voice_as_face_term:
        final_mood = face
        confidence = 1.0
        reasoning = f"Perfect Match: Both face and voice indicate {face}."
    
    # RULE 2: The 'Fake Smile' (Depression Detection)
    elif face == "Happy" and (voice == "Sadness" or voice == "Sad"):
        final_mood = "Hidden Sadness"
        confidence = 0.85
        reasoning = "Fake Smile Detected: Voice tone indicates sadness despite the smiling face."

    # RULE 3: The 'Stoic' (Hidden Anger)
    elif face == "Neutral" and voice == "Anger":
        final_mood = "Frustration"
        confidence = 0.9
        reasoning = "The Stoic: Face is composed (Neutral) but voice carries Anger, suggesting Frustration."

    # RULE 4: The 'Silent Shock'
    elif face == "Surprise" and (voice == "Neutral" or voice == "Calm"):
        final_mood = "Surprise"
        confidence = 0.9
        reasoning = "Silent Shock: Visibly surprised but speechless/calm. Visual cue takes priority."

    # RULE 5: Excitement Override
    elif voice == "Excited" and (face == "Neutral" or face == "Happy"):
        final_mood = "Excited"
        confidence = 0.95
        reasoning = "Excitement Override: High vocal energy overrides the facial expression."

    # RULE 6: The Fallback (Voice Priority)
    else:
        final_mood = voice
        confidence = 0.6
        reasoning = f"Conflicting Signals: Trusting Voice ({voice}) over Face ({face}) as it's a more raw biological signal."

    # --- 3. OUTPUT ---
    print(f"   [FUSION RESULT] Final Mood: {final_mood} | Rule: {reasoning}")
    
    return {
        "final_mood": final_mood,
        "confidence": confidence,
        "reasoning": reasoning
    }
