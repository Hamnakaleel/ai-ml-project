# Fish Disease Detection System - Architecture

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER BROWSER                            │
│                  (Templates/index.html)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ├──► Upload Image (POST /predict)
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    FLASK SERVER                             │
│                     (app.py)                                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Routes:                                             │  │
│  │  • GET  /              → Render index.html           │  │
│  │  • POST /predict       → ML Prediction               │  │
│  │  • POST /generate_report → PDF Generation            │  │
│  │  • POST /chat          → Gemini AI Response          │  │
│  └──────────────────────────────────────────────────────┘  │
└────────┬────────────────┬──────────────────┬────────────────┘
         │                │                  │
         │                │                  │
    ┌────▼────┐    ┌──────▼──────┐   ┌──────▼───────┐
    │  MODEL  │    │  DISEASE    │   │   GEMINI     │
    │ (TF/K)  │    │    INFO     │   │     API      │
    │  128x128│    │  DATABASE   │   │              │
    │ 7 class │    │   (Python   │   │              │
    │         │    │   dict)     │   │              │
    └────┬────┘    └──────┬──────┘   └──────┬───────┘
         │                │                  │
         └────────────────┴──────────────────┘
                     │
                  JSON Response
                     │
         ┌───────────▼────────────┐
         │   BROWSER RECEIVES:    │
         │  • disease name        │
         │  • confidence %        │
         │  • cause               │
         │  • symptoms            │
         │  • treatment           │
         │  • prevention          │
         │  • organ affected      │
         │  • solution            │
         └────────────────────────┘
```

---

## API Endpoints

### 1. GET `/`
**Purpose:** Serve the web interface  
**Response:** HTML page

---

### 2. POST `/predict`
**Purpose:** Classify uploaded fish image  
**Input:**
```
FormData:
  - file: [image file]
```

**Output (JSON):**
```json
{
  "disease": "Bacterial Red disease",
  "confidence": 95.28,
  "cause": "Bacterial infection through wounds.",
  "symptoms": "Red patches and bleeding fins.",
  "treatment": "Antibiotic treatment.",
  "prevention": "Good hygiene and clean water.",
  "organ": "Skin and fins",
  "solution": "Isolate fish and apply antibiotics."
}
```

**Error Response:**
```json
{
  "error": "This is not a valid fish image."
}
```

---

### 3. POST `/generate_report`
**Purpose:** Generate PDF report of diagnosis  
**Input (JSON):**
```json
{
  "disease": "Bacterial Red disease",
  "confidence": "95.28"
}
```

**Output:** PDF file (binary download)

---

### 4. POST `/chat`
**Purpose:** Chat with AI expert about fish diseases  
**Input (JSON):**
```json
{
  "message": "What is Bacterial Red disease?"
}
```

**Output (JSON):**
```json
{
  "reply": "Bacterial Red Disease is caused by... [AI response]"
}
```

---

## Data Flow: Image Prediction

### Step 1: Image Upload
- User selects image via `<input type="file">`
- JavaScript displays preview

### Step 2: Send to Server
```javascript
fetch('/predict', {
  method: 'POST',
  body: FormData (contains image file)
})
```

### Step 3: Server Processing
```python
# app.py /predict route:
1. Save image to static/uploaded.jpg
2. Load image: target_size=(128, 128)
3. Normalize: divide by 255.0
4. Expand dims: (128,128,3) → (1,128,128,3)
5. Run model.predict()
6. Get class index (argmax)
7. Get confidence (max probability * 100)
8. Map class_idx to disease name
9. Fetch disease info from database
10. Return JSON response
```

### Step 4: Display Results
```javascript
// JavaScript displays:
document.getElementById('diseaseName').textContent = disease
document.getElementById('confidenceScore').textContent = confidence
document.getElementById('causeText').textContent = cause
document.getElementById('treatmentText').textContent = treatment
document.getElementById('solutionText').textContent = solution
document.getElementById('symptomsText').textContent = symptoms
document.getElementById('preventionText').textContent = prevention
document.getElementById('organText').textContent = organ
```

### Step 5: Optional - Generate PDF
```javascript
fetch('/generate_report', {
  
  method: 'POST',
  body: JSON.stringify({disease, confidence})
})
// Returns PDF blob → downloads as fish_disease_report.pdf
```

---

## Class Mapping

The model outputs 7 classes:

| Index | Disease Name |
|-------|--------------|
| 0 | Bacterial Red disease |
| 1 | Bacterial diseases - Aeromoniasis |
| 2 | Bacterial gill disease |
| 3 | Fungal diseases Saprolegniasis |
| 4 | Healthy Fish |
| 5 | Not a fish |
| 6 | Parasitic diseases |

**Note:** If prediction returns class 5 ("Not a fish"), the system returns error instead of result.

---

## Model Architecture

**Base Model:** MobileNetV2 (pretrained on ImageNet)  
**Custom Layers:**
- GlobalAveragePooling2D
- Dense(256, activation='relu')
- Dropout(0.4)
- Dense(7, activation='softmax')

**Input:** 128×128×3 RGB images  
**Output:** 7 class probabilities

**Performance:**
- Training Accuracy: 95.47%
- Validation Accuracy: 80.66%

---

## Disease Information Database

All disease information is hardcoded in `disease_info` dictionary in app.py:

```python
disease_info = {
    'Healthy Fish': {
        'cause': '...',
        'symptoms': '...',
        'treatment': '...',
        'prevention': '...',
        'organ': '...',
        'solution': '...'
    },
    # ... 6 more diseases
}
```

**Fields returned for each disease:**
- `cause` - Root cause
- `symptoms` - Observable signs
- `treatment` - Medical/aquarium treatment
- `prevention` - Preventive measures
- `organ` - Affected body parts
- `solution` - Recommended action

---

## Security Considerations

### API Key Management
- ✅ Never hardcode keys in source
- ✅ Use environment variables (GEMINI_API_KEY)
- ✅ Graceful fallback if key missing

### File Upload
- ✅ Accepts image files only
- ✅ Saves to `static/` directory
- ✅ Validates with model (rejects "Not a fish")

### PDF Generation
- ✅ Server-side only
- ✅ ReportLab library (safe)
- ✅ No user input in PDF

---

## Dependencies

```
Flask>=2.0.0
TensorFlow>=2.10.0
google-generativeai>=0.3.0
reportlab>=4.0.0
numpy>=1.20.0
```

All dependencies can be installed via:
```bash
pip install flask tensorflow google-generativeai reportlab numpy
```

---

## Future Enhancements

- [ ] Database to store predictions history
- [ ] User accounts & login
- [ ] Advanced analytics dashboard
- [ ] Image preprocessing improvements
- [ ] Model versioning system
- [ ] A/B testing for model updates
- [ ] Mobile app
- [ ] Real-time video detection
