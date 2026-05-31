Timeline Audio Visualizer for Blender
Version: 0.2.5
Author: Maxim K. <Telegram: @qsOwOsp>
Copyright: 2026 Maxim K.
License: GPL-3.0-or-later
Support: https://github.com/OwOpq/timeline-audio-visualizer/issues

Install:
1. Open Blender 4.2 or newer.
2. Go to Edit > Preferences > Get Extensions.
3. Use Install from Disk and choose the extension ZIP file.
4. Enable Timeline Audio Visualizer.

Use:
1. Open an animation editor such as Dope Sheet, Graph Editor, or NLA Editor.
2. Press N to open the sidebar.
3. Open the Sound tab.
4. Use Timeline Audio Visualizer > On / Refresh.

Tip:
- In the Timeline header, use the TAV button to open the controls even when the sidebar is hidden.

Main controls:
- Waveform View:
  Peaks / Bars, Solid Mirror, Outline, RMS Envelope, Peak + RMS, Positive Fill.
- Height Offset:
  Scales waveform height.
- Vertical Anchor:
  Places the waveform at the center, bottom, or top of the editor.
- Source:
  Sequencer Only, Speaker Only, or All.
- Sequencer filters:
  Audible Strips, Selected Strips, or Sound In List.

Notes:
- Blender AUD is used first for decoding.
- WAV fallback is included for simple PCM WAV files.
- Most common WAV and many MP3 files should work through Blender's built-in audio support.
- The extension is meant for short animation/audio ranges, not very long full-track editing.

Report Issues:
- Use the public GitHub Issues page:
  https://github.com/OwOpq/timeline-audio-visualizer/issues
