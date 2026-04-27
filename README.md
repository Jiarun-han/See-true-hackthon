# GazeBridge 👁️🌉

> **Turning "looking at something" into a silent understanding.**

🏆 **1st Place Winner** at the Frontier Interfaces Hackathon (2026), hosted by Thinkin' Rocks at Startup Sauna, Otaniemi.

---

## 🌟 Overview

**GazeBridge** is an AR accessibility assistant that removes the need for active interaction—like speaking, typing, or clicking—by using eye-tracking technology. It is designed to be a bridge between the user and the world, helping the environment explain itself to the user through intuitive, gaze-based AR overlays.

Our mission is to provide **dignity, autonomy, and independence** to users facing information barriers, especially those for whom the eyes are the most reliable channel of expression.

## ⚠️ The Problem

Information is not equally accessible to everyone. About **1.3 billion people** worldwide (1 in 6) experience significant disability. For many, traditional interfaces (speech, touch, manual aiming) are themselves barriers. [cite_start]People can often "see" information but may not be able to understand or act on it due to cognitive, motor, or language barriers [cite: 11-16, 30].

## ✅ The Solution: GazeBridge

GazeBridge differentiates itself from existing tools (like Google Lens or Microsoft Seeing AI) by focusing on **implicit interaction**:
* [cite_start]**No manual aiming**: No need to hold a phone or click a button[cite: 45].
* [cite_start]**Gaze-based intent**: Uses stable gaze (dwell time) to trigger AI analysis[cite: 77].
* [cite_start]**Real-world understanding**: Explains the specific part of the world the user is looking at[cite: 109].

## 🛠️ Technical Flow

Developed using **SeeTrue** eye-tracking glasses, the GazeBridge pipeline follows a low-interruption, ROI-focused design:

1.  [cite_start]**Multimodal Input**: Real-time streaming of gaze data and scene video from SeeTrue glasses[cite: 74].
2.  [cite_start]**Stable Gaze Detection**: Triggers only when the gaze dwells within a 35px radius for ≥ 1.5 seconds to confirm intent[cite: 77, 102].
3.  [cite_start]**Mode Selection**: Supports Visual, Simplify, Elderly, and Language Bridge modes[cite: 80].
4.  [cite_start]**ROI Crop**: Automatically crops a ~320×320 region around the gaze point to focus AI processing[cite: 84].
5.  [cite_start]**Local AI Analysis**: Processes the crop to return contextual text (primary and secondary explanations)[cite: 87].
6.  [cite_start]**Minimal AR Display**: A 5s popup overlay followed by a 3s cooldown to prevent information overload[cite: 90].

## 👥 Target Users

* [cite_start]**Accessibility**: Individuals with ALS, post-stroke aphasia, or motor impairments [cite: 116-118].
* [cite_start]**Cognitive Support**: People with ADHD, Dyslexia, or high cognitive load[cite: 139].
* [cite_start]**Universal Design**: Older adults navigating new kiosks and immigrants/tourists needing language support[cite: 145, 151].

## 🚀 Future Work: Fatigue-Awareness

We are developing a system that knows when to stay quiet. By detecting visual fatigue patterns from eye activity, GazeBridge will automatically:
* Reduce information density.
* Increase font sizes.
* [cite_start]Shorten explanations or provide gentle rest reminders [cite: 182-195].

## 👥 The Team

Created with ❤️ at the Frontier Interfaces Hackathon 2026.
* Jiacheng Wei
* Huatai Pan
* Miao Liu
* Xinge Wang
---
*GazeBridge does not only help the world explain itself. It also knows when to stay quiet.* [cite: 198]
