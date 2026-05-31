# Changelog

## v0.2.5 - Review fixes

This update addresses Blender Extensions review feedback while keeping the add-on behavior unchanged.

### Fixed

- Fixed add-on preferences registration to use `__package__`, as required for Blender extension add-ons.
- Fixed add-on preferences lookup to read from `bpy.context.preferences.addons[__package__]`.

### Changed

- Kept the extension version at `0.2.5` for the review resubmission.
- Added a public GitHub Issues support tracker:
  `https://github.com/OwOpq/timeline-audio-visualizer/issues`

### Notes

- No waveform display modes were removed.
- No timeline overlay controls were changed.
- The Blender Extensions platform support link should point to the public GitHub Issues page above.
