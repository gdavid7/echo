# Echo AI - Test Cases

Here are several test-case scenarios to validate the conversational intelligence of the Echo AI assistant.

### Test Case 1: The Vague Patient

*   **Goal:** Test the AI's ability to persistently probe for specific details when the patient is initially vague.
*   **User Persona:** Act as a patient who knows something is wrong but isn't good at describing it.
*   **Dialogue Guide:**
    *   **AI:** "What is the reason for your upcoming appointment?"
    *   **User:** "I have a toothache."
    *   **AI:** "I'm sorry to hear that. Could you tell me exactly which tooth or area is bothering you?"
    *   **User:** "I'm not sure, one of the back ones, I think."
    *   **AI:** *(Should ask for more specific location, e.g., "Is it on the top or bottom, left or right side?")*
    *   **User:** "Uh, bottom right."
    *   **AI:** *(Should continue down the list of required questions: timeline, sensation, severity, triggers).*
*   **Expected Outcome:** The AI should not move on until it gets a reasonably specific answer for each of the key diagnostic questions.

### Test Case 2: The Patient with Multiple Issues

*   **Goal:** Test the AI's ability to handle multiple reported symptoms logically.
*   **User Persona:** Act as a patient with one major problem and one minor one.
*   **Dialogue Guide:**
    *   **AI:** "What is the reason for your upcoming appointment?"
    *   **User:** "My front tooth really hurts, and also my gums have been bleeding a little when I brush."
*   **Expected Outcome:** The AI should first complete the full investigation of the primary, more severe issue (the tooth pain). After gathering all details (location, severity, etc.) for the toothache, it should then circle back to the secondary issue, e.g., "Thank you for those details. You also mentioned some bleeding gums. Can you tell me more about that?"

### Test Case 3: The Routine Check-up That Isn't

*   **Goal:** Test the AI's ability to transition from a routine check-in to a diagnostic investigation.
*   **User Persona:** You believe you're just coming for a cleaning but have a symptom when asked.
*   **Dialogue Guide:**
    *   **AI:** "What is the reason for your upcoming appointment?"
    *   **User:** "I'm just coming in for my regular cleaning."
    *   **AI:** *(Should say something like: "That's great! Just to be thorough for your chart, have you noticed any new sensitivity or discomfort anywhere in your mouth?")*
    *   **User:** "Actually, yes. One of my back teeth has been a little sensitive to cold this week."
*   **Expected Outcome:** The AI should immediately pivot to the full "pain or a specific problem" line of questioning, starting with clarifying the location of the sensitivity.

### Test Case 4: The Impatient Patient

*   **Goal:** Test the AI's ability to handle interruptions and steer the conversation back on track.
*   **User Persona:** Be hurried and interrupt the AI. The `output_interruption` feature is key here.
*   **Dialogue Guide:**
    *   **AI:** "Can you describe the feeling? Is it a sharp, dull, throbbing..."
    *   **User:** (Interrupting) "Look, it just hurts! Can you just tell the dentist?"
*   **Expected Outcome:** The AI should gracefully handle the interruption and justify its need for more information. For example: "I understand your discomfort, and I will certainly pass this on. To help the dentist prepare properly, could you tell me if the pain feels more like a sharp sting or a dull ache?" 
