# PBR Lookdev v4.2.1

A layered PBR material system for Blender 4.2+

## Features

* Layered PBR shader system — stack multiple shader layers with blend/mask controls
* Supports 5 shader types: Principled BSDF, Glass, Emission, Diffuse, Subsurface Scattering
* Auto folder scan — detects and assigns texture maps by filename keywords
* Smart part detection — automatically detects character/prop part names (Hair, Body, Face etc.) from mixed folders and filters scan per part
* Batch scan subfolders — creates one layer per texture set automatically
* ORM/ARM packed texture support with selectable channel layout (R/G/B mapping)
* Per-channel color space picker for every texture slot
* Procedural masks — Noise, Wave, Gradient, Voronoi per layer or overlay
* Image mask support with invert, min/max range, and independent tiling
* Per-channel image overlays with blend modes, strength, and stacked compositing
* Color correction per slot — Hue, Saturation, Value, Contrast, Gamma
* Per-channel override mapping — independent tiling/offset/rotation per texture
* Global layer mapping — tiling presets, offset, rotation with lock toggle
* Texture Coordinate and Image Projection controls per layer and per channel
* UDIM tile sequence support per texture slot
* Min/Max (Map Range) range controls for all grayscale channels
* Normal map and Bump map with strength controls
* Displacement map with scale and midlevel (Cycles)
* AO multiplied into base color with strength control
* Compact mode — hides advanced groups (Coat, Sheen, Thin Film)
* Detail view toggle — streamlines the UI
* Collapse All button — clears all expanded sections instantly

## Location

* Shader Editor > N-Panel > PBR Lookdev
* View3D > N-Panel > PBR Lookdev
* Properties > Material > PBR Lookdev

## Requirements

Blender 4.2 or newer

## Installation

1. Download the latest `.zip` from the [Releases](../../releases) page
2. In Blender: **Edit → Preferences → Add-ons → Install**
3. Select the downloaded `.zip`
4. Enable **PBR Lookdev** in the list

## Bug Reports

Found a bug? Open an issue on the [Issues](../../issues) page. Please include your Blender version and a short description of what went wrong.

## License

This add-on is free and open-source software licensed under the
GNU General Public License v3.0 or later (GPL-3.0-or-later).
See LICENSE.txt for full terms.

## Author

BHiMAX
