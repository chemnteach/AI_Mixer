# Advanced Mashup Types - Implementation Roadmap

**Created:** 2026-01-19
**Status:** Vision Documented - Implementation Pending
**Owner:** The Mixer Project

---

## Vision

Build an AI-powered mashup system that goes beyond "vocal over instrumental" to create **genuinely novel** musical combinations using semantic understanding, emotional reasoning, and dynamic vocal interaction.

### Key Principle

Move from **mechanical mashups** (just tempo/key alignment) to **intelligent mashups** (AI reasons about structure, meaning, and interaction).

---

## The 8 Mashup Types

### Phase 3B: Simple Types (Foundation)

#### 1. Classic
- **What:** Vocal A + Instrumental B (traditional mashup)
- **Already spec'd:** PRD.md lines 670-826
- **Complexity:** Low
- **Test goal:** Prove core audio engineering works

#### 2. Stem Role Swapping
- **What:** Mix drums/bass/vocals from 3+ songs
- **Innovation:** Compose from a stem palette
- **Example:** Beyoncé vocals + Daft Punk drums + Beatles bass
- **Complexity:** Low
- **Test goal:** Prove multi-song coordination works

---

### Phase 3C: Energy-Based Types

#### 3. Energy Curve Matching
- **What:** Align sections by energy level, not just tempo
- **Innovation:** Structure follows emotional intensity
- **Algorithm:** Extract RMS energy per section → match high-energy chorus to high-energy drop
- **Complexity:** Medium
- **Test goal:** Prove section metadata is useful

#### 4. Adaptive Harmony
- **What:** Auto-fix key clashes via pitch-shifting
- **Innovation:** AI decides which track to shift to preserve vocal character
- **Algorithm:** Detect key clash → calculate semitone shift → LLM decides vocal vs instrumental shift
- **Complexity:** Medium
- **Test goal:** Prove pitch manipulation quality

---

### Phase 3D: Semantic Types

#### 5. Lyrical Theme Fusion
- **What:** Filter lyrics to only include lines matching a theme
- **Innovation:** Creates thematic coherence from disparate songs
- **Example:** Target theme = "heartbreak" → only keep heartbreak-related lyrics
- **Algorithm:** LLM classifies each section → keep matches (with vocals) → replace non-matches (instrumental)
- **Complexity:** Medium
- **Test goal:** Prove LLM theme classification works

#### 6. Semantic-Aligned Mashups
- **What:** AI designs emotional arc, selecting sections based on meaning
- **Innovation:** Meaning-driven structure, not tempo-driven
- **Example:** "Build journey from hope → doubt → defiance"
- **Algorithm:** Extract emotional tone per section → LLM designs arc → select sections non-linearly
- **Complexity:** Medium-High
- **Test goal:** Prove AI can create musically valid structures

---

### Phase 3E: Interactive Types (Most Advanced)

#### 7. Role-Aware Vocal Recomposition
- **What:** Vocals dynamically shift between lead, harmony, call, response, texture
- **Innovation:** Vocals interact instead of just overlaying
- **Example:** Sparse vocals become harmony, dense vocals become lead
- **Algorithm:** Analyze vocal density/intensity → LLM assigns roles → mix with role-specific processing
- **Complexity:** High
- **Test goal:** Prove role assignments sound natural

#### 8. Conversational Mashups
- **What:** Lyrics respond to each other like a dialogue
- **Innovation:** Creates duets that were never recorded
- **Example:**
  ```
  A: "Do you believe in love?"
  (silence)
  B: "I used to, yeah"
  ```
- **Algorithm:** LLM detects Q&A patterns → pair lines → extract vocal snippets → arrange with silence gaps
- **Complexity:** High
- **Test goal:** Prove lyric-level vocal extraction works

---

## Critical Foundation: Phase 3A

**Enhanced Analyst Agent** - Extract section-level metadata

### Why Critical
All 7 advanced types depend on this. If section detection fails, advanced mashups fail.

### Deliverables

#### 1. Section Detection
- Use `librosa.segment.agglomerative` or `madmom.features.downbeats`
- Identify boundaries: intro, verse, chorus, bridge, outro
- **Validation:** Manually review 20 songs, verify boundaries make sense

#### 2. Energy Analysis
- Per-section RMS energy (0.0-1.0)
- Spectral centroid (brightness)
- Tempo stability (beat consistency)
- **Validation:** Energy curves show choruses > verses

#### 3. Vocal Analysis
- Vocal density: sparse/medium/dense (based on vocal stem amplitude)
- Vocal intensity: 0.0-1.0 (loudness + energy)
- Lyrical content: extract lyrics per section
- **Validation:** Density matches human perception

#### 4. Semantic Analysis (LLM)
- Emotional tone: hopeful, melancholic, defiant, etc.
- Lyrical function: narrative, hook, question, answer, reflection
- Themes: love, loss, rebellion, etc.
- **Validation:** Classifications feel accurate to humans

### New Schema

```python
class SectionMetadata(TypedDict):
    # Structural
    section_type: str              # "intro" | "verse" | "chorus" | "bridge" | "outro"
    start_sec: float
    end_sec: float
    duration_sec: float

    # Energy (librosa)
    energy_level: float            # 0.0-1.0
    spectral_centroid: float
    tempo_stability: float

    # Vocal (stem analysis)
    vocal_density: str             # "sparse" | "medium" | "dense"
    vocal_intensity: float
    lyrical_content: str

    # Semantic (LLM)
    emotional_tone: str
    lyrical_function: str
    themes: List[str]
```

### Add to SongMetadata
```python
sections: List[SectionMetadata]
emotional_arc: str  # "intro:hopeful → verse:doubt → chorus:defiant"
```

---

## Dependencies

### New Libraries Required

```txt
# Phase 3A: Section detection
madmom>=0.16.1           # Onset/beat tracking

# Already have (Phase 1-2)
chromadb==0.4.22
sentence-transformers>=2.2.0
librosa>=0.10.0
openai-whisper>=20230314
demucs>=4.0.0
pyrubberband>=0.3.0
anthropic>=0.18.0
openai>=1.0.0
```

**No exotic models needed.** Everything uses current open-source libraries.

---

## Implementation Phases

### Phase 2: Ingestion Agent ⏳ (In Progress)
- **Duration:** 1-2 weeks
- **Goal:** Get real audio into the system
- **Deliverables:** Local + YouTube ingestion, format conversion, caching
- **Test:** Ingest 10 songs successfully

### Phase 3A: Enhanced Analyst Agent ⏸️ (Next)
- **Duration:** 2-3 weeks (most critical - test thoroughly)
- **Goal:** Section-level metadata extraction
- **Deliverables:** Section detection, energy/vocal/semantic analysis
- **Test:** Run on 50+ songs, manually verify quality

### Phase 3B: Simple Mashup Types ⏸️
- **Duration:** 1 week
- **Goal:** Validate core audio architecture
- **Implement:** Classic, Stem Role Swapping
- **Test:** Create 5 mashups of each type, verify sound quality

### Phase 3C: Energy-Based Types ⏸️
- **Duration:** 1 week
- **Goal:** Prove section metadata works
- **Implement:** Energy Curve Matching, Adaptive Harmony
- **Test:** Energy-matched mashups feel climactic, pitch-shift quality acceptable

### Phase 3D: Semantic Types ⏸️
- **Duration:** 1-2 weeks
- **Goal:** Prove AI reasoning works
- **Implement:** Lyrical Theme Fusion, Semantic-Aligned
- **Test:** Theme filtering creates coherence, AI structure choices make sense

### Phase 3E: Interactive Types ⏸️
- **Duration:** 2 weeks
- **Goal:** Achieve genuinely novel results
- **Implement:** Role-Aware Recomposition, Conversational
- **Test:** Role assignments sound natural, conversations feel genuine

---

## Testing Strategy

### Test Library (6 Representative Songs)

Use real songs across these categories:
1. **Simple pop** - 4/4 time, clear sections (e.g., Taylor Swift)
2. **Complex arrangement** - Odd time signatures, irregular structure (e.g., Radiohead)
3. **A cappella** - Test vocal detection (e.g., Pentatonix)
4. **Instrumental** - Test "no vocals" detection (e.g., Explosions in the Sky)
5. **Rap** - Dense lyrics, test lyric extraction (e.g., Kendrick Lamar)
6. **Ballad** - Sparse, emotional, test semantic analysis (e.g., Adele)

### Validation at Each Phase

**Phase 3A (Section Detection):**
- ✅ Run on 50+ songs
- ✅ Manually inspect section boundaries (should match human perception)
- ✅ Energy curves make sense (choruses are higher energy)
- ✅ Emotional tone classifications feel accurate

**Phase 3B (Simple Mashups):**
- ✅ Create 5 classic mashups - sound quality is good
- ✅ Time-stretching doesn't create artifacts
- ✅ Beat alignment is tight (downbeats sync)
- ✅ Stem swapping produces coherent multi-song mashups

**Phase 3C (Energy Types):**
- ✅ Energy-matched mashups feel more climactic
- ✅ Pitch-shifting quality acceptable (within ±3 semitones)
- ✅ Key clash detection works correctly

**Phase 3D (Semantic Types):**
- ✅ Theme filtering creates coherent narratives
- ✅ LLM section ordering choices make musical sense
- ✅ Crossfades between sections sound smooth

**Phase 3E (Interactive Types):**
- ✅ Role assignments sound natural (not forced)
- ✅ Conversational mashups feel like genuine dialogue
- ✅ Vocal extraction at lyric-level works cleanly

---

## Success Criteria

### Minimum Viable Product (MVP)
- Phases 0, 1, 2, 3A, 3B complete
- Can create classic mashups with solid audio quality
- Section-level metadata extraction works reliably

### Full Advanced System
- All phases through 3E complete
- All 8 mashup types implemented and tested
- User can choose mashup type via CLI
- Results sound genuinely novel (not just "cleaner automation")

---

## Risk Assessment

### High Risk (Phase 3A - Section Detection)
**Risk:** Section boundaries don't align with human perception
**Mitigation:** Test on 50+ songs, iterate on algorithm parameters
**Fallback:** Use fixed-length sections (e.g., every 16 bars)

### Medium Risk (Phase 3E - Lyric-Level Extraction)
**Risk:** Extracting individual lyric lines cleanly is hard
**Mitigation:** Use forced alignment (Montreal Forced Aligner)
**Fallback:** Use full section vocals instead of line-by-line

### Low Risk (Audio Quality)
**Risk:** Pitch-shifting or time-stretching degrades quality
**Mitigation:** Use high-quality libraries (pyrubberband, Demucs)
**Fallback:** Warn user if stretch ratio > 1.2 or pitch shift > ±3

---

## Future Enhancements (Post Phase 3E)

### 9. Ghost Harmonies
- Extract melody of Song A's vocal → layer as faint synthesized harmony under Song B
- Creates uncanny familiarity
- Requires: `basic-pitch` for melody extraction

### 10. Dynamic EQ and Sidechain
- Apply frequency-aware mixing (EQ vocals to sit in instrumental)
- Sidechain compression (duck instrumental when vocals present)
- Requires: Advanced DSP (pydub filters, librosa effects)

### 11. Multi-Song Medleys
- Extend beyond 2-song mashups to N-song medleys
- AI designs 5-song journey with emotional arc
- Requires: Scalable section selection algorithm

---

## Documentation

**Primary References:**
- PRD.md lines 828-1070 (Advanced Mashup Types spec)
- mixer/types.py (MashupType enum, SectionMetadata)
- CONTINUITY.md (Project state, architecture decisions)

**This Document:**
- Location: `thoughts/shared/plans/advanced-mashup-types-roadmap.md`
- Purpose: Capture full vision and phased implementation strategy
- Audience: Future sessions, contributors, maintainers

---

## Timeline Summary

**Total Duration:** ~2-3 months (not including Phase 0-2)

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 0 | Complete | ✅ |
| Phase 1 | Complete | ✅ |
| Phase 2 | 1-2 weeks | ⏳ In Progress |
| Phase 3A | 2-3 weeks | ⏸️ Pending |
| Phase 3B | 1 week | ⏸️ Pending |
| Phase 3C | 1 week | ⏸️ Pending |
| Phase 3D | 1-2 weeks | ⏸️ Pending |
| Phase 3E | 2 weeks | ⏸️ Pending |

**Note:** Timeline is a rough estimate. Since time is not a constraint, prioritize quality validation at each phase over speed.

---

*This roadmap locks in the vision while allowing flexible, incremental implementation. Each phase validates the pieces needed for the next.*
