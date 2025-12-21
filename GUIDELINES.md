# Indonesian Fintech LLM Data Pipeline - Guidelines

**Version:** 1.0  
**Last Updated:** December 19, 2025  
**Target Domain:** Indonesian Fintech Customer Support (GoPay-like)

---

## Table of Contents

1. [Overview](#overview)
2. [Data Standards](#data-standards)
3. [Cleaning Guidelines](#cleaning-guidelines)
4. [Labeling Guidelines](#labeling-guidelines)
5. [Quality Criteria](#quality-criteria)
6. [Validation Rules](#validation-rules)
7. [Edge Cases & Troubleshooting](#edge-cases--troubleshooting)
8. [Best Practices](#best-practices)

---

##  Overview

### Purpose
This pipeline prepares Indonesian fintech customer messages for LLM training, focusing on:
- Intent classification (complaint, inquiry, urgent_request, feedback)
- Sentiment analysis (positive, neutral, negative, very_negative)
- Urgency detection (low, medium, high, critical)
- Safety filtering (safe, toxic, offensive)

### Dataset Context
- **Source:** Synthetic fintech customer messages
- **Domain:** Payment transactions, refunds, account issues
- **Language:** Indonesian with colloquial terms (gaul)
- **Use Case:** Customer support automation

### Pipeline Stages
```
Raw Data (555 msgs)
    ↓
Deduplication (-395 msgs, 71.2% removed)
    ↓
Text Normalization (160 msgs)
    ↓
Length Filter (-8 msgs, <20 or >300 chars)
    ↓
Language Filter (-20 msgs, non-Indonesian)
    ↓
Cleaned Data (132 msgs, 23.8% retention)
    ↓
Manual Labeling (weak supervision, 2 annotators)
    ↓
Quality Validation (Kappa: 0.93, 6 outliers)
    ↓
Final Labeled Dataset ✓
```

### Key Statistics
- **Original:** 555 messages
- **Final:** 132 unique Indonesian messages (23.8% retention)
- **Inter-Annotator Agreement:** Cohen's Kappa = 0.93 (Excellent)
- **Quality Status:** PASS

---

##  Data Standards

### Input Format

**Raw CSV (no header):**
```csv
"msg_117","transaksi gagal tapi duit udh kepotong bangsat"
"msg_355","akun di suspend tiba2 padahal baru top up 1jt"
```

**Schema:**
- Column 1: Message ID (string, format: `msg_XXX`)
- Column 2: Customer message text (string, Indonesian)

### Output Format

**Cleaned JSONL:**
```jsonl
{
  "id": "msg_117",
  "text": "transaksi gagal tapi duit udh kepotong bangsat",
  "text_length": 46,
  "detected_lang": "id"
}
```

**Labeled JSONL:**
```jsonl
{
  "id": "msg_117",
  "text": "transaksi gagal tapi duit udh kepotong bangsat",
  "text_length": 46,
  "detected_lang": "id",
  "labels": {
    "intent": "complaint",
    "sentiment": "very_negative",
    "urgency": "medium",
    "safety": "toxic"
  }
}
```

### Text Constraints

| Property | Constraint | Rationale |
|----------|-----------|-----------|
| **Length** | 20-300 characters | Too short lacks context; too long is unusual for customer messages |
| **Language** | Indonesian (id) | Target domain; includes Malay/Tagalog detection as Indonesian |
| **Encoding** | UTF-8 | Standard for Indonesian text |
| **Duplicates** | Not allowed | Ensures data diversity |

---

##  Cleaning Guidelines

### 1. Duplicate Detection

**Method:** MD5 hash of full text string

**Action:** Keep first occurrence, remove all duplicates

**Example:**
```python
# 84.5% of raw data were duplicates
# From 555 → 160 unique messages (395 removed)
```

**Why This Matters:**
- Duplicates inflate dataset size without adding information
- Can cause overfitting in model training
- Skew distribution metrics

### 2. Text Normalization

**Applied transformations:**

#### a) Whitespace Normalization
```python
# Before: "  transaksi   gagal  "
# After:  "transaksi gagal"

text = text.strip()  # Remove leading/trailing
text = re.sub(r'\s+', ' ', text)  # Multiple spaces → single space
```

**Statistics:** 74 messages had whitespace issues (13.3%)

#### b) Punctuation Normalization
```python
# Limit excessive punctuation (emotional emphasis)
text = re.sub(r'\.{6,}', '.....', text)  # Max 5 dots
text = re.sub(r'!{6,}', '!!!!!', text)   # Max 5 exclamations
text = re.sub(r'\?{4,}', '???', text)    # Max 3 questions
```

**Why Keep Some:** Emotional indicators are useful for urgency/sentiment classification

**Statistics:**
- Excessive dots: 14 messages (2.5%)
- Excessive exclamations: 58 messages (10.4%)
- Excessive questions: 48 messages (8.6%)

#### c) Emoji & Non-ASCII Removal
```python
# Remove all non-ASCII characters
text = text.encode('ascii', 'ignore').decode('ascii').strip()
```

**Why:** Ensures consistent text representation; emojis can cause encoding issues

### 3. Length Filtering

**Thresholds:**
- **Minimum:** 20 characters
- **Maximum:** 300 characters

**Removed:** 8 messages (1.4%)

**Examples of filtered:**
```
Too short: "???" (3 chars)
Too short: "mau tanya dong" (14 chars)
```

**Why These Limits:**
- <20 chars: Insufficient context for meaningful labeling
- >300 chars: Unusual for customer messages (avg: 39 chars, std: 7.4)

### 4. Language Detection

**Method:** `langdetect` library with Indonesian keyword fallback

**Indonesian Keywords:**
```python
id_keywords = {
    'min', 'dong', 'banget', 'udh', 'ga', 'gw', 'sih',
    'nih', 'tapi', 'sama', 'nya', 'udah', 'gimana',
    'aja', 'bgt', 'kalo', 'mau', 'pake', 'bisa',
    'tolong', 'urgent', 'refund', 'akun', 'saldo'
}
```

**Detection Logic:**
1. If 2+ Indonesian keywords found → `id`
2. Else use `langdetect`
3. Treat Malay (`ms`) and Tagalog (`tl`) as Indonesian (similar languages)

**Results:**
- Indonesian: 132 messages (69.7% of deduplicated)
- Non-Indonesian: 20 messages removed (English, German, French, etc.)

**Examples of removed:**
```
[msg_378] (en): AKUN SUSPEND TANPA ALASAN JELAS TOLONG!!!
[msg_008] (en): GOBLOK LU APLIKASI BANGSATT!!!!!
```

**Note:** These were misclassified by langdetect due to ALL CAPS or slang

### Cleaning Pipeline Summary

| Stage | Input | Output | Removed | Removal Rate |
|-------|-------|--------|---------|--------------|
| Raw data | 555 | 555 | 0 | 0% |
| Deduplication | 555 | 160 | 395 | 71.2% |
| Normalization | 160 | 160 | 0 | 0% |
| Length filter | 160 | 152 | 8 | 5.0% |
| Language filter | 152 | 132 | 20 | 13.2% |
| **Total** | **555** | **132** | **423** | **76.2%** |

---

##  Labeling Guidelines

### Label Schema Overview

```yaml
labels:
  intent: [complaint, inquiry, urgent_request, feedback]
  sentiment: [positive, neutral, negative, very_negative]
  urgency: [low, medium, high, critical]
  safety: [safe, toxic, offensive]
```

All labels are **required** and **single-choice** (one per message).

---

### 1. INTENT Classification

**Purpose:** What is the customer trying to achieve?

#### complaint
**Definition:** Customer reports a problem or negative experience

**Keywords:** gagal, error, kepotong, ilang, refund, nyangkut, bermasalah

**Examples:**
```
✓ "transaksi gagal tapi duit udh kepotong bangsat"
✓ "top up gagal tapi rekening kepotong tai"
✓ "saldo ilang 500rb ga ada notif apa2 tolol!!!!!"
```

**Distribution:** 39 messages (29.5%)

#### inquiry
**Definition:** Customer asks for information or clarification

**Keywords:** berapa, gimana, bagaimana, apa, kenapa, cara, bisa, tanya

**Examples:**
```
✓ "limit transfer gopay berapa sih maksimal"
✓ "bisa ga top up pake virtual account"
✓ "cara cancel transaksi pending gimana"
```

**Distribution:** 47 messages (35.6%)

#### urgent_request
**Definition:** Customer needs immediate assistance or action

**Keywords:** urgent, tolong, bantu, cepat, segera, suspend, nyangkut

**Examples:**
```
✓ "URGENT BANGET NIH TRANSAKSI NYANGKUT 4JT"
✓ "tolong akun gw di banned ga bisa login urgent"
✓ "uang nyangkut 1.5jt transaksi gagal urgent min"
```

**Distribution:** 30 messages (22.7%)

#### feedback
**Definition:** Customer provides feedback, suggestions, or appreciation

**Keywords:** thanks, makasih, puas, bagus, request, lancar

**Examples:**
```
✓ "min request fitur split bill dong"
✓ "puas sih pake gopay selama ini lancar"
✓ "thanks min udh dibantu refund nya masuk"
```

**Distribution:** 16 messages (12.1%)

** Edge Case:** Positive feedback about resolved complaint → Still `complaint` intent
```
Example: "thanks min udh dibantu refund nya masuk"
→ Intent: complaint (about refund issue)
→ Sentiment: positive (grateful it was resolved)
```

---

### 2. SENTIMENT Classification

**Purpose:** What is the emotional tone?

#### positive
**Definition:** Satisfied, grateful, or happy tone

**Keywords:** thanks, makasih, puas, lancar, cepet, bagus

**Examples:**
```
✓ "puas sih pake gopay selama ini lancar"
✓ "thanks min udh dibantu refund nya masuk"
✓ "gopay sama ovo bagusan mana ya" (neutral-positive comparison)
```

**Distribution:** 7 messages (5.3%)

#### neutral
**Definition:** No clear emotional tone; factual or informational

**Examples:**
```
✓ "limit transfer gopay berapa sih maksimal"
✓ "bisa ga top up pake virtual account"
✓ "akun di suspend tiba2 padahal baru top up 1jt"
```

**Distribution:** 71 messages (53.8%)

#### negative
**Definition:** Disappointed, frustrated, or mildly upset

**Keywords:** gagal, error, kecewa, jelek, lambat, lama

**Examples:**
```
✓ "aplikasi sering error kecewa bgt"
✓ "uang nyangkut 1.5jt transaksi gagal urgent min"
✓ "transaksi 5jt pending udh 2 hari urgent banget"
```

**Distribution:** 18 messages (13.6%)

#### very_negative
**Definition:** Extremely angry, containing profanity or toxic language

**Toxic Keywords:** kontol, anjing, bangsat, tolol, brengsek, tai

**Examples:**
```
✓ "transaksi gagal tapi duit udh kepotong bangsat"
✓ "REFUND GW MANA KONTOL UDAH SEMINGGU"
✓ "SALDO GW KEPOTONG ANJING!!!! REFUND KAPAN???"
```

**Distribution:** 36 messages (27.3%)

** Imbalance Warning:** 10.1x imbalance (positive 5.3% vs neutral 53.8%)

---

### 3. URGENCY Classification

**Purpose:** How quickly does this need attention?

#### low
**Definition:** General inquiry, no time pressure

**Indicators:**
- No urgency keywords
- Informational questions
- Feedback/suggestions

**Examples:**
```
✓ "limit transfer gopay berapa sih maksimal"
✓ "min request fitur split bill dong"
✓ "gopay sama ovo bagusan mana ya"
```

**Distribution:** 63 messages (47.7%)

#### medium
**Definition:** Problem reported but not time-critical

**Indicators:**
- Complaint keywords (gagal, error, kepotong)
- No explicit urgency
- <3 exclamation marks

**Examples:**
```
✓ "transaksi gagal tapi duit udh kepotong bangsat"
✓ "aplikasi sering error kecewa bgt"
✓ "top up gagal tapi rekening kepotong tai"
```

**Distribution:** 27 messages (20.5%)

#### high
**Definition:** Urgent problem, needs attention soon

**Indicators:**
- "urgent" keyword OR
- 3+ exclamation marks OR
- Account issues (suspend, banned)

**Examples:**
```
✓ "AKUN GW SUSPEND PADAHAL GA NGAPA2IN!!!"
✓ "tolong akun gw di banned ga bisa login urgent"
✓ "saldo ilang 500rb ga ada notif apa2 tolol!!!!!"
```

**Distribution:** 27 messages (20.5%)

#### critical
**Definition:** Immediate action required, high-value or blocking issue

**Indicators:**
- "urgent" + (3+ exclamations OR large amount OR suspend/blocked)
- Money stuck (nyangkut) with large amount

**Examples:**
```
✓ "URGENT BANGET NIH TRANSAKSI NYANGKUT 4JT"
✓ "uang nyangkut 1.5jt transaksi gagal urgent min"
✓ "URGENT!!! saldo 3jt ga bisa dipake akun error"
```

**Distribution:** 15 messages (11.4%)

** Imbalance Warning:** 4.2x imbalance (low 47.7% vs critical 11.4%)

** Edge Case:** Toxic language doesn't automatically mean high urgency
```
Example: "transaksi pending terus uang nyangkut bangsat....."
→ Urgency: low (no urgency indicators despite toxic language)
→ Safety: toxic
```

---

### 4. SAFETY Classification

**Purpose:** Content moderation for customer-facing systems

#### safe
**Definition:** No offensive or toxic language; appropriate for all audiences

**Examples:**
```
✓ "limit transfer gopay berapa sih maksimal"
✓ "uang nyangkut 1.5jt transaksi gagal urgent min"
✓ "aplikasi sering error kecewa bgt"
```

**Distribution:** 91 messages (68.9%)

#### offensive
**Definition:** Mildly offensive language; not severely toxic

**Keywords:** goblok, tai, sampah, bodoh

**Examples:**
```
✓ "top up gagal tapi rekening kepotong tai"
✓ "saldo tiba2 berkurang sendiri aplikasi sampah"
```

**Distribution:** 10 messages (7.6%)

#### toxic
**Definition:** Severe profanity or highly offensive language

**Keywords:** kontol, anjing, bangsat, tolol, brengsek, memek, babi

**Examples:**
```
✓ "transaksi gagal tapi duit udh kepotong bangsat"
✓ "REFUND GW MANA KONTOL UDAH SEMINGGU"
✓ "SALDO GW KEPOTONG ANJING!!!! REFUND KAPAN???"
```

**Distribution:** 31 messages (23.5%)

** Imbalance Warning:** 9.1x imbalance (safe 68.9% vs offensive 7.6%)

---

## Quality Criteria

### Inter-Annotator Agreement (IAA)

**Method:** Cohen's Kappa (2 annotators, weak supervision)

**Thresholds:**
- **Excellent:** κ > 0.81
- **Good:** κ > 0.61
- **Moderate:** κ > 0.41
- **Fair:** κ > 0.21
- **Poor:** κ ≤ 0.21

**Results:**

| Label Type | Kappa Score | Agreement % | Quality |
|------------|-------------|-------------|---------|
| Intent | 0.9371 | 95.5% | Excellent ✓ |
| Sentiment | 0.9267 | 95.5% | Excellent ✓ |
| Urgency | 0.9331 | 95.5% | Excellent ✓ |
| Safety | 0.9053 | 95.5% | Excellent ✓ |
| **Average** | **0.9256** | **95.5%** | **Excellent ✓** |

**Status:** PASS (all labels > 0.81)

### Class Balance

**Imbalance Threshold:** Max class / Min class > 4.0x

**Results:**

| Label Type | Majority Class | Minority Class | Ratio | Status |
|------------|----------------|----------------|-------|--------|
| Intent | inquiry (35.6%) | feedback (12.1%) | 2.9x | ✓ OK |
| Sentiment | neutral (53.8%) | positive (5.3%) | 10.1x |  WARNING |
| Urgency | low (47.7%) | critical (11.4%) | 4.2x |  WARNING |
| Safety | safe (68.9%) | offensive (7.6%) | 9.1x |  WARNING |

**Recommendations:**
- **Sentiment:** Oversample positive class or collect more positive feedback
- **Urgency:** Acceptable for real-world distribution (most messages are low urgency)
- **Safety:** Acceptable for real-world distribution (most messages are safe)

### Outlier Detection

**Thresholds:**
- **Length outliers:** Z-score > 3.0 standard deviations
- **Label inconsistencies:** Logically conflicting labels
- **Statistical anomalies:** Classes with <5% representation

**Results:**

| Type | Count | Examples |
|------|-------|----------|
| Length outliers | 0 | None detected (all within 20-300 chars) |
| Label inconsistencies | 6 | See below |
| Statistical anomalies | 0 | No classes <5% |

**Detected Inconsistencies:**

1. **Positive + Complaint (3 cases)**
   ```json
   {
     "id": "msg_460",
     "text": "thanks min udh dibantu refund nya masuk",
     "labels": {"intent": "complaint", "sentiment": "positive"}
   }
   ```
   **Reasoning:** This is actually CORRECT - customer is grateful that their complaint was resolved. Intent reflects the original issue (refund), sentiment reflects current emotion (thankful).

2. **Toxic + Low Urgency (3 cases)**
   ```json
   {
     "id": "msg_110",
     "text": "transaksi pending terus uang nyangkut bangsat.....",
     "labels": {"safety": "toxic", "urgency": "low"}
   }
   ```
   **Reasoning:** Toxic language doesn't always mean high urgency. This message has no explicit urgency indicators (no "urgent", <3 exclamations).

### Cross-Label Correlations

**Strong Correlations (|r| > 0.3):**

| Pair | Correlation | Interpretation |
|------|-------------|----------------|
| intent ↔ sentiment | -0.634 | Complaints are more negative |
| intent ↔ urgency | -0.676 | Urgent requests have higher urgency |
| sentiment ↔ safety | 0.649 | Toxic language is very negative |
| sentiment ↔ urgency | 0.447 | Negative messages are more urgent |

**Expected:** These correlations make logical sense and validate labeling consistency.

---

##  Validation Rules

### Automated Validation Checks

**1. Schema Validation**
```python
required_columns = ['id', 'text', 'text_length', 'detected_lang']
# All columns must be present
# No missing columns allowed
```

**2. Null Value Check**
```python
# id and text columns must not contain null values
df[['id', 'text']].isnull().sum() == 0
```

**3. Length Constraints**
```python
min_length = 20
max_length = 300
# All messages must be within 20-300 characters
(df['text_length'] >= min_length) & (df['text_length'] <= max_length)
```

**4. Language Validation**
```python
target_language = 'id'
# All messages must be detected as Indonesian
df['detected_lang'] == 'id'
```

**5. Label Value Validation**
```python
# All labels must be from predefined schema
valid_intents = ['complaint', 'inquiry', 'urgent_request', 'feedback']
valid_sentiments = ['positive', 'neutral', 'negative', 'very_negative']
valid_urgency = ['low', 'medium', 'high', 'critical']
valid_safety = ['safe', 'toxic', 'offensive']

df['intent'].isin(valid_intents).all()
df['sentiment'].isin(valid_sentiments).all()
df['urgency'].isin(valid_urgency).all()
df['safety'].isin(valid_safety).all()
```

### Quality Thresholds

| Metric | Threshold | Current | Status |
|--------|-----------|---------|--------|
| Cohen's Kappa (avg) | ≥ 0.70 | 0.9256 | ✓ PASS |
| Retention rate | ≥ 15% | 23.8% | ✓ PASS |
| Outliers | < 10% | 4.5% | ✓ PASS |
| Null values | 0 | 0 | ✓ PASS |

**Overall Status:** ✓ PASS - Dataset ready for model training

---

##  Edge Cases & Troubleshooting

### 1. Positive Sentiment + Complaint Intent

**Case:** Customer thanks support for resolving their issue

**Example:**
```
Text: "thanks min udh dibantu refund nya masuk"
Intent: complaint (original issue was refund)
Sentiment: positive (grateful for resolution)
```

**Rule:** Intent reflects the original problem, sentiment reflects current emotion.

**Similar patterns:**
- "makasih min akun udh dibuka lagi" → complaint + positive
- "thanks udh dibantu transfer berhasil" → complaint + positive

### 2. Toxic Language + Low Urgency

**Case:** Customer uses profanity but doesn't need immediate action

**Example:**
```
Text: "transaksi pending terus uang nyangkut bangsat....."
Urgency: low (no urgency indicators)
Safety: toxic (profanity present)
```

**Rule:** Safety and urgency are independent. Don't assume toxic = urgent.

**Urgency indicators required:**
- Explicit "urgent" keyword
- 3+ exclamation marks
- Large monetary amount + "nyangkut"
- Account blocking (suspend, banned)

### 3. ALL CAPS Messages

**Case:** Message is in all caps but langdetect fails

**Example:**
```
Original: "AKUN SUSPEND TANPA ALASAN JELAS TOLONG!!!"
Detected: English (incorrect)
```

**Solution:** Indonesian keyword fallback catches these
- Keywords: "akun", "tolong" → Reclassified as Indonesian

### 4. Mixed Language Messages

**Case:** Indonesian with some English words

**Example:**
```
"disappointed with the service lately" → English (removed)
"tolong urgent banget nih" → Indonesian (kept)
```

**Rule:** Majority language wins. If 2+ Indonesian keywords present, classify as Indonesian.

### 5. Ambiguous Intent: Inquiry vs Urgent Request

**Case:** Question phrased as urgent

**Example:**
```
"gimana cara refund urgent banget!!!" 
Intent: urgent_request (has "urgent" keyword)

"gimana cara refund sih?"
Intent: inquiry (no urgency indicators)
```

**Rule:** Presence of urgency keywords/markers determines intent classification.

### 6. Duplicate-like Messages

**Case:** Very similar but not exact duplicates

**Example:**
```
"transaksi gagal tapi duit udh kepotong"
"transaksi gagal tapi duit udah kepotong"
(udh vs udah)
```

**Rule:** Only exact MD5 hash matches are removed. Similar messages are kept for linguistic variation.

### 7. Excessive Punctuation

**Case:** Long sequences of punctuation

**Example:**
```
Before: "REFUND GW MANA KONTOL UDAH SEMINGGU??????????????????????"
After:  "REFUND GW MANA KONTOL UDAH SEMINGGU???"
```

**Rule:** Normalize to max 5 dots/exclamations, max 3 questions. Preserves emphasis without excessive tokens.

---

##  Best Practices

### For Data Cleaning

1. **Always check duplicates first**
   - 84.5% of raw data were duplicates in this dataset
   - Use MD5 hash for exact matching

2. **Normalize before filtering**
   - Whitespace normalization can affect length calculations
   - Do normalization → then check length constraints

3. **Use keyword fallback for language detection**
   - `langdetect` fails on ALL CAPS or slang
   - Indonesian keywords: min, dong, banget, udh, ga, gw, sih, etc.

4. **Keep some punctuation**
   - Don't remove all exclamations/questions
   - They're useful for urgency/sentiment classification
   - Normalize excessive → preserve emotional indicators

5. **Document removed samples**
   - Save cleaning_log.csv for traceability
   - Track removal reasons (duplicates, length, language)

### For Labeling

1. **Intent is about purpose, not emotion**
   - "thanks but..." → Still a complaint if there's an issue
   - Focus on what customer wants to achieve

2. **Sentiment is independent of intent**
   - Can have positive sentiment + complaint intent
   - Can have neutral sentiment + urgent_request intent

3. **Urgency requires explicit indicators**
   - Don't assume toxic language = urgent
   - Look for: "urgent", exclamations, large amounts, account blocking

4. **Safety is about language, not issue severity**
   - "my account is blocked" → safe (serious issue, no profanity)
   - "transaksi bangsat" → toxic (minor issue, profanity present)

5. **When in doubt, use neutral/low**
   - Sentiment: neutral (if no clear positive/negative)
   - Urgency: low (if no explicit urgency indicators)

### For Quality Control

1. **Calculate Cohen's Kappa on sample**
   - Use 50-100 messages for IAA check
   - Target: κ > 0.70 (substantial agreement)

2. **Check class imbalance**
   - Alert if majority/minority > 4.0x
   - Consider oversampling minority classes

3. **Review outliers manually**
   - Label inconsistencies may reveal annotation errors
   - Or legitimate edge cases that need documentation

4. **Cross-label correlation analysis**
   - Expected: intent ↔ urgency, sentiment ↔ safety
   - Unexpected correlations may indicate systematic errors

5. **Save validation samples**
   - Keep examples of edge cases
   - Use for annotator training and consistency checks

### For Pipeline Maintenance

1. **Update keyword lists regularly**
   - Indonesian slang evolves (e.g., "udh" → "udah")
   - New fintech terms emerge

2. **Version your schemas**
   - Track changes to label_schema.json
   - Document rationale for changes

3. **Monitor retention rate**
   - This dataset: 23.8% retention is acceptable
   - Alert if drops below 15% (too aggressive filtering)

4. **Automate validation**
   - Run validation_report.json after each cleaning
   - Fail pipeline if validation status ≠ PASS

5. **Keep raw data immutable**
   - Never overwrite data/raw/
   - All transformations should create new files

---

##  References

### Label Schema
- **File:** `configs/label_schema.json`
- **Version:** 1.0
- **Last updated:** 2024-12-16

### Pipeline Configuration
- **File:** `configs/pipeline_config.yaml`
- **Parameters:**
  - `min_length`: 20
  - `max_length`: 300
  - `target_language`: id
  - `min_kappa`: 0.7

### Quality Metrics
- **File:** `data/labeled/quality_metrics.json`
- **Kappa scores:** 0.9256 average (Excellent)
- **Status:** PASS

### Output Files
```
data/
├── raw/
│   └── synthetic_generated.csv       # Original data (555 messages)
├── processed/
│   ├── cleaned_data.jsonl           # After cleaning (132 messages)
│   ├── validation_report.json       # Validation results
│   └── cleaning_log.csv             # Cleaning statistics
└── labeled/
    ├── labeled_data.jsonl           # Final labeled data
    ├── labeling_stats.json          # Label distribution
    ├── quality_metrics.json         # Quality metrics
    ├── label_distribution.json      # Detailed distribution
    ├── outliers_report.json         # Outlier analysis
    └── validation_samples.jsonl     # Edge cases for review
```

---

##  Support & Contribution

### Questions?
- Check notebooks in `notebooks/` for detailed examples
- Review visualizations in `outputs/visualizations/`

### Found an edge case?
- Document in `data/labeled/validation_samples.jsonl`
- Update this guidelines document
- Increment version number

### Reporting Issues
- Labeling disagreements → Check Inter-Annotator Agreement section
- Data quality problems → Run validation pipeline
- Pipeline errors → Check `data/processed/cleaning_log.csv`

---

**Last Updated:** December 19, 2025  
**Dataset Version:** 1.0 (132 messages)  
**Quality Status:** ✓ PASS (Kappa: 0.9256)