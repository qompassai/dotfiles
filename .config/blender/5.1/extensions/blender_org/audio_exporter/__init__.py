bl_info = {
    "name": "Audio Exporter",
    "author": "Dinesh007",
    "version": (1, 1, 0),
    "blender": (4, 5, 0),
    "location": "Sequencer > View(Menu) > Audio Export",
    "description": "Export audio from selected strips in the VSE as separate or combined files ",
    "category": "Sequencer",
}

import bpy
import os
from bpy.props import (
    EnumProperty, StringProperty, PointerProperty, BoolProperty,
    IntProperty, FloatProperty
)
from bpy.types import PropertyGroup, Operator


class AudioExporterProperties(PropertyGroup):
    export_mode: EnumProperty(
        name="Export Mode",
        description="Choose export mode for selected audio strips",
        items=[
            ('SEPARATE', "Separate", "Export each selected strip as separate audio files"),
            ('COMBINE', "Combine", "Export all selected strips combined into one audio file")
        ],
        default='COMBINE'
    )

    audio_codec: EnumProperty(
        name="Audio Codec",
        description="Choose audio codec",
        items=[
            ('AAC', "AAC", "Advanced Audio Codec"),
            ('AC3', "AC3", "Audio Codec 3"),
            ('FLAC', "FLAC", "Free Lossless Audio Codec"),
            ('MP2', "MP2", "MPEG-1 Audio Layer 2"),
            ('MP3', "MP3", "MPEG-1 Audio Layer 3"),
            ('PCM', "PCM (WAV)", "Uncompressed PCM in WAV"),
            ('VORBIS', "Vorbis (OGG)", "Ogg Vorbis")
        ],
        default='MP3'
    )

    container_format: EnumProperty(
        name="Container",
        description="Container format (auto-selected)",
        items=[
            ('WAV', "WAV", "WAV container"),
            ('MP3', "MP3", "MP3 container"),
            ('FLAC', "FLAC", "FLAC container"),
            ('OGG', "OGG", "OGG container"),
            ('MP4', "MP4", "MP4 container"),
            ('MKV', "MKV", "Matroska container")
        ],
        default='MP3'
    )

    sample_rate: EnumProperty(
        name="Sample Rate",
        description="Audio sample rate in Hz",
        items=[
            ('8000', "8 kHz", "8000 Hz"),
            ('11025', "11.025 kHz", "11025 Hz"),
            ('16000', "16 kHz", "16000 Hz"),
            ('22050', "22.05 kHz", "22050 Hz"),
            ('44100', "44.1 kHz", "44100 Hz (CD Quality)"),
            ('48000', "48 kHz", "48000 Hz (Professional)"),
            ('88200', "88.2 kHz", "88200 Hz"),
            ('96000', "96 kHz", "96000 Hz"),
            ('192000', "192 kHz", "192000 Hz"),
            ('CUSTOM', "Custom", "Enter custom sample rate")
        ],
        default='48000'
    )

    custom_sample_rate: IntProperty(
        name="Custom Sample Rate (Hz)",
        description="Enter custom sample rate in Hz",
        default=48000, min=1000, max=384000
    )

    bitrate: EnumProperty(
        name="Bitrate",
        description="Audio bitrate for compressed formats",
        items=[
            ('64', "64 kbps", "64 kbps"),
            ('96', "96 kbps", "96 kbps"),
            ('128', "128 kbps", "128 kbps"),
            ('160', "160 kbps", "160 kbps"),
            ('192', "192 kbps", "192 kbps"),
            ('256', "256 kbps", "256 kbps"),
            ('320', "320 kbps", "320 kbps"),
            ('512', "512 kbps", "512 kbps"),
            ('CUSTOM', "Custom", "Enter custom bitrate")
        ],
        default='256'
    )

    custom_bitrate: IntProperty(
        name="Custom Bitrate (kbps)",
        description="Enter custom bitrate in kbps",
        default=256, min=32, max=1024
    )

    volume: FloatProperty(
        name="Volume",
        description="Output volume multiplier",
        default=1.0, min=0.0, max=5.0, precision=2, subtype='FACTOR'
    )

    audio_channels: EnumProperty(
        name="Audio Channels",
        description="Number of audio channels",
        items=[
            ('MONO', "Mono", "1 channel"),
            ('STEREO', "Stereo", "2 channels"),
            ('SURROUND_4', "4 Channels", "4 channels"),
            ('SURROUND_51', "5.1 Surround", "6 channels (5.1)"),
            ('SURROUND_71', "7.1 Surround", "8 channels (7.1)")
        ],
        default='STEREO'
    )

    skip_gaps: BoolProperty(
        name="Skip Gaps",
        description="When combining, skip gaps between selected strips instead of including silence",
        default=False
    )

    preserve_frame_range: BoolProperty(
        name="Preserve Frame Range",
        description="Use scene's current frame range instead of strip boundaries for export",
        default=False
    )

    # NEW FEATURE: Toggle for avoiding file overwriting
    avoid_overwrite: BoolProperty(
        name="Avoid Overwriting Files",
        description="Automatically append numbers to filenames to avoid overwriting existing files",
        default=True
    )


class SEQUENCER_OT_export_audio_filebrowser(Operator):
    bl_idname = "sequencer.export_audio_filebrowser"
    bl_label = "Audio Export"
    bl_description = "Export audio from selected VSE strips using file browser"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".wav"
    filter_sound: BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})
    
    filepath: StringProperty(
        name="File Path",
        description="Filepath used for exporting the file",
        maxlen=1024,
        subtype='FILE_PATH'
    )

    # Duplicate properties for file browser sidebar
    export_mode: EnumProperty(
        name="Export Mode",
        description="Choose export mode for selected audio strips",
        items=[
            ('SEPARATE', "Separate", "Export each selected strip as separate audio files"),
            ('COMBINE', "Combine", "Export all selected strips combined into one audio file")
        ],
        default='COMBINE'
    )

    audio_codec: EnumProperty(
        name="Audio Codec",
        description="Choose audio codec",
        items=[
            ('AAC', "AAC", "Advanced Audio Codec"),
            ('AC3', "AC3", "Audio Codec 3"),
            ('FLAC', "FLAC", "Free Lossless Audio Codec"),
            ('MP2', "MP2", "MPEG-1 Audio Layer 2"),
            ('MP3', "MP3", "MPEG-1 Audio Layer 3"),
            ('PCM', "PCM (WAV)", "Uncompressed PCM in WAV"),
            ('VORBIS', "Vorbis (OGG)", "Ogg Vorbis")
        ],
        default='MP3'
    )

    sample_rate: EnumProperty(
        name="Sample Rate",
        description="Audio sample rate in Hz",
        items=[
            ('8000', "8 kHz", "8000 Hz"),
            ('11025', "11.025 kHz", "11025 Hz"),
            ('16000', "16 kHz", "16000 Hz"),
            ('22050', "22.05 kHz", "22050 Hz"),
            ('44100', "44.1 kHz", "44100 Hz (CD Quality)"),
            ('48000', "48 kHz", "48000 Hz (Professional)"),
            ('88200', "88.2 kHz", "88200 Hz"),
            ('96000', "96 kHz", "96000 Hz"),
            ('192000', "192 kHz", "192000 Hz"),
            ('CUSTOM', "Custom", "Enter custom sample rate")
        ],
        default='48000'
    )

    custom_sample_rate: IntProperty(
        name="Custom Sample Rate (Hz)",
        default=48000, min=1000, max=384000
    )

    bitrate: EnumProperty(
        name="Bitrate",
        description="Audio bitrate for compressed formats",
        items=[
            ('64', "64 kbps", "64 kbps"),
            ('96', "96 kbps", "96 kbps"),
            ('128', "128 kbps", "128 kbps"),
            ('160', "160 kbps", "160 kbps"),
            ('192', "192 kbps", "192 kbps"),
            ('256', "256 kbps", "256 kbps"),
            ('320', "320 kbps", "320 kbps"),
            ('512', "512 kbps", "512 kbps"),
            ('CUSTOM', "Custom", "Enter custom bitrate")
        ],
        default='256'
    )

    custom_bitrate: IntProperty(
        name="Custom Bitrate (kbps)",
        default=256, min=32, max=1024
    )

    volume: FloatProperty(
        name="Volume",
        description="Output volume multiplier",
        default=1.0, min=0.0, max=5.0, precision=2, subtype='FACTOR'
    )

    audio_channels: EnumProperty(
        name="Audio Channels",
        description="Number of audio channels",
        items=[
            ('MONO', "Mono", "1 channel"),
            ('STEREO', "Stereo", "2 channels"),
            ('SURROUND_4', "4 Channels", "4 channels"),
            ('SURROUND_51', "5.1 Surround", "6 channels (5.1)"),
            ('SURROUND_71', "7.1 Surround", "8 channels (7.1)")
        ],
        default='STEREO'
    )

    skip_gaps: BoolProperty(
        name="Skip Gaps",
        description="When combining, skip gaps between selected strips instead of including silence",
        default=False
    )

    preserve_frame_range: BoolProperty(
        name="Preserve Frame Range",
        description="Use scene's current frame range instead of strip boundaries for export",
        default=False
    )

    # NEW FEATURE: Overwrite toggle in file browser
    avoid_overwrite: BoolProperty(
        name="Avoid Overwriting Files",
        description="Automatically append numbers to filenames to avoid overwriting existing files",
        default=True
    )

    # Utility methods
    def get_container_for_codec(self, codec):
        return {
            'AAC': 'AAC', 'AC3': 'AC3', 'FLAC': 'FLAC', 'MP2': 'MP2',
            'MP3': 'MP3', 'PCM': 'WAV', 'VORBIS': 'OGG'
        }.get(codec, 'MP3')

    def get_file_extension(self, codec):
        return {
            'AAC': 'aac', 'AC3': 'ac3', 'FLAC': 'flac', 'MP2': 'mp2',
            'MP3': 'mp3', 'PCM': 'wav', 'VORBIS': 'ogg'
        }.get(codec, 'mp3')

    def is_lossy_codec(self, codec):
        return codec in ['AAC', 'AC3', 'MP2', 'MP3', 'VORBIS']

    def get_channel_count(self, channels):
        return {
            'MONO': 1, 'STEREO': 2, 'SURROUND_4': 4,
            'SURROUND_51': 6, 'SURROUND_71': 8
        }.get(channels, 2)

    def get_actual_sample_rate(self):
        return str(self.custom_sample_rate) if self.sample_rate == 'CUSTOM' else self.sample_rate

    def get_actual_bitrate(self):
        return str(self.custom_bitrate) if self.bitrate == 'CUSTOM' else self.bitrate

    def apply_volume_to_strips(self, strips, volume_multiplier):
        original_volumes = {}
        for strip in strips:
            if hasattr(strip, 'volume'):
                original_volumes[strip] = strip.volume
                strip.volume *= volume_multiplier
        return original_volumes

    def restore_strip_volumes(self, original_volumes):
        for strip, vol in original_volumes.items():
            if hasattr(strip, 'volume'):
                strip.volume = vol

    def get_numbered_filename(self, filepath, extension):
        """Generate a numbered filename to avoid overwriting existing files"""
        base_path = os.path.splitext(filepath)[0]
        counter = 1
        new_filepath = f"{base_path}.{extension}"
        
        while os.path.exists(new_filepath):
            new_filepath = f"{base_path}_{counter:03d}.{extension}"
            counter += 1
        
        return new_filepath

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Export Settings", icon='SOUND')
        box.prop(self, "export_mode", expand=True)

        if self.export_mode == 'COMBINE':
            box.separator()
            # Gray out skip_gaps when preserve_frame_range is enabled
            row = box.row()
            row.enabled = not self.preserve_frame_range
            row.prop(self, "skip_gaps")

        box.separator()
        box.prop(self, "preserve_frame_range")
        
        # Add the avoid overwrite toggle
        box.separator()
        overwrite_row = box.row()
        overwrite_row.prop(self, "avoid_overwrite")
        
        box.separator()

        # Format settings
        fmt_box = box.box()
        fmt_box.label(text="Audio Format", icon='SPEAKER')
        fmt_box.prop(self, "audio_codec")
        fmt_box.label(text=f"Container: {self.get_container_for_codec(self.audio_codec)}")

        # Quality settings
        qual_box = box.box()
        qual_box.label(text="Quality Settings", icon='PREFERENCES')
        qual_box.prop(self, "sample_rate")
        if self.sample_rate == 'CUSTOM':
            qual_box.prop(self, "custom_sample_rate")

        if self.is_lossy_codec(self.audio_codec):
            qual_box.prop(self, "bitrate")
            if self.bitrate == 'CUSTOM':
                qual_box.prop(self, "custom_bitrate")
        else:
            qual_box.label(text="Lossless (no bitrate setting)")

        qual_box.prop(self, "audio_channels")
        qual_box.prop(self, "volume", slider=True)

        # Current settings info
        info_box = box.box()
        info_box.label(text="Current Settings:", icon='INFO')
        info_box.label(text=f"Sample Rate: {self.get_actual_sample_rate()} Hz")
        if self.is_lossy_codec(self.audio_codec):
            info_box.label(text=f"Bitrate: {self.get_actual_bitrate()} kbps")
        info_box.label(text=f"Volume: {int(self.volume * 100)}%")

        # Frame range info
        if self.preserve_frame_range:
            scene = context.scene
            frame_box = box.box()
            frame_box.label(text="Current Frame Range:", icon='TIME')
            frame_box.label(text=f"Start: {scene.frame_start}")
            frame_box.label(text=f"End: {scene.frame_end}")

        # Selected strips info
        seq = context.scene.sequence_editor
        if seq:
            selected = [s for s in seq.sequences if s.select and s.type == 'SOUND']
            if selected:
                strips_box = box.box()
                strips_box.label(text=f"Selected Audio Strips ({len(selected)}):", icon='SOUND')
                for strip in selected[:5]:
                    strips_box.label(text=f"• {strip.name}")
                if len(selected) > 5:
                    strips_box.label(text=f"... and {len(selected) - 5} more")

    def invoke(self, context, event):
        seq = context.scene.sequence_editor
        if not seq:
            self.report({'ERROR'}, "No sequence editor found")
            return {'CANCELLED'}

        selected_strips = [s for s in seq.sequences if s.select and s.type == 'SOUND']
        if not selected_strips:
            self.report({'ERROR'}, "No selected sound strips found")
            return {'CANCELLED'}

        # Set default filename
        file_ext = self.get_file_extension(self.audio_codec)
        if self.export_mode == 'COMBINE':
            self.filepath = f"combined_audio.{file_ext}"
        else:
            first_strip = selected_strips[0]
            self.filepath = f"{first_strip.name}.{file_ext}"

        self.filename_ext = f".{file_ext}"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def check(self, context):
        new_ext = f".{self.get_file_extension(self.audio_codec)}"
        if self.filename_ext != new_ext:
            self.filename_ext = new_ext
            if self.filepath:
                base = os.path.splitext(self.filepath)[0]
                self.filepath = base + new_ext
            return True
        return False

    def execute(self, context):
        scene = context.scene
        seq = scene.sequence_editor
        if not seq:
            self.report({'ERROR'}, "No sequence editor found")
            return {'CANCELLED'}

        selected_strips = [s for s in seq.sequences if s.select and s.type == 'SOUND']
        if not selected_strips:
            self.report({'ERROR'}, "No selected sound strips found")
            return {'CANCELLED'}

        # Validate custom values
        if self.sample_rate == 'CUSTOM':
            if not (1000 <= self.custom_sample_rate <= 384000):
                self.report({'ERROR'}, f"Custom sample rate {self.custom_sample_rate} Hz is out of valid range")
                return {'CANCELLED'}

        if self.bitrate == 'CUSTOM' and self.is_lossy_codec(self.audio_codec):
            if not (32 <= self.custom_bitrate <= 1024):
                self.report({'ERROR'}, f"Custom bitrate {self.custom_bitrate} kbps is out of valid range")
                return {'CANCELLED'}

        # Create output directory
        output_dir = os.path.dirname(bpy.path.abspath(self.filepath))
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError as e:
                self.report({'ERROR'}, f"Cannot create directory: {e}")
                return {'CANCELLED'}

        # Store original settings
        orig_fp, orig_start, orig_end = scene.render.filepath, scene.frame_start, scene.frame_end

        try:
            if self.export_mode == 'SEPARATE':
                self.export_separate(context, selected_strips, output_dir)
            else:
                self.export_combined(context, selected_strips, self.filepath)

        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {e}")
            return {'CANCELLED'}
        finally:
            scene.render.filepath, scene.frame_start, scene.frame_end = orig_fp, orig_start, orig_end

        # Success message
        mode_desc = self.export_mode.lower()
        if self.export_mode == 'COMBINE':
            if self.skip_gaps and not self.preserve_frame_range:
                mode_desc += " (skipping gaps)"
            if self.preserve_frame_range:
                mode_desc += " with preserved frame range"

        if self.avoid_overwrite:
            mode_desc += " with auto-numbering"

        settings_info = [f"Sample Rate: {self.get_actual_sample_rate()} Hz"]
        if self.is_lossy_codec(self.audio_codec):
            settings_info.append(f"Bitrate: {self.get_actual_bitrate()} kbps")
        settings_info.append(f"Volume: {int(self.volume * 100)}%")

        self.report({'INFO'}, f"Audio exported successfully in {mode_desc} mode ({', '.join(settings_info)})")
        return {'FINISHED'}

    def export_separate(self, context, strips, output_dir):
        scene = context.scene
        original_start, original_end = scene.frame_start, scene.frame_end

        for strip in strips:
            if self.preserve_frame_range:
                scene.frame_start, scene.frame_end = original_start, original_end
            else:
                scene.frame_start, scene.frame_end = strip.frame_final_start, strip.frame_final_end

            file_ext = self.get_file_extension(self.audio_codec)
            base_filename = f"{strip.name}.{file_ext}"
            filepath = os.path.join(output_dir, base_filename)
            
            # NEW FEATURE: Apply auto-numbering if avoid_overwrite is enabled
            if self.avoid_overwrite and os.path.exists(filepath):
                filepath = self.get_numbered_filename(filepath, file_ext)

            original_volumes = self.apply_volume_to_strips([strip], self.volume)

            # Mute other strips
            original_mute_states = {}
            for s in scene.sequence_editor.sequences:
                if s.type == 'SOUND' and s != strip:
                    original_mute_states[s] = s.mute
                    s.mute = True

            self.mixdown_audio(filepath)

            # Restore states
            for s, mute_state in original_mute_states.items():
                s.mute = mute_state
            self.restore_strip_volumes(original_volumes)

    def export_combined(self, context, strips, filepath):
        scene = context.scene
        original_start, original_end = scene.frame_start, scene.frame_end
        sorted_strips = sorted(strips, key=lambda s: s.frame_final_start)

        # NEW FEATURE: Apply auto-numbering to combined export if needed
        abs_filepath = bpy.path.abspath(filepath)
        if self.avoid_overwrite and os.path.exists(abs_filepath):
            file_ext = self.get_file_extension(self.audio_codec)
            abs_filepath = self.get_numbered_filename(abs_filepath, file_ext)

        if self.preserve_frame_range:
            start_frame, end_frame = original_start, original_end
        else:
            start_frame = min(s.frame_final_start for s in strips)
            end_frame = max(s.frame_final_end for s in strips)

        # Skip gaps logic (only if preserve_frame_range is False)
        if self.skip_gaps and not self.preserve_frame_range:
            temp_files = []
            base_filename = os.path.splitext(abs_filepath)[0]
            try:
                for i, strip in enumerate(sorted_strips):
                    scene.frame_start, scene.frame_end = strip.frame_final_start, strip.frame_final_end
                    file_ext = self.get_file_extension(self.audio_codec)
                    temp_filename = f"{base_filename}_temp_{i:03d}.{file_ext}"
                    temp_files.append(temp_filename)

                    original_volumes = self.apply_volume_to_strips([strip], self.volume)

                    original_mute_states = {}
                    for s in scene.sequence_editor.sequences:
                        if s.type == 'SOUND' and s != strip:
                            original_mute_states[s] = s.mute
                            s.mute = True

                    self.mixdown_audio(temp_filename)

                    for s, mute_state in original_mute_states.items():
                        s.mute = mute_state
                    self.restore_strip_volumes(original_volumes)

                self.combine_audio_files(temp_files, abs_filepath)
            finally:
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except OSError:
                            pass
        else:
            scene.frame_start, scene.frame_end = start_frame, end_frame
            original_volumes = self.apply_volume_to_strips(strips, self.volume)

            original_mute_states = {}
            for s in scene.sequence_editor.sequences:
                if s.type == 'SOUND' and s not in strips:
                    original_mute_states[s] = s.mute
                    s.mute = True

            self.mixdown_audio(abs_filepath)

            for s, mute_state in original_mute_states.items():
                s.mute = mute_state
            self.restore_strip_volumes(original_volumes)

    def combine_audio_files(self, input_files, output_file):
        if not input_files:
            return

        if len(input_files) == 1:
            import shutil
            shutil.move(input_files[0], output_file)
            return

        original_scene = bpy.context.scene
        try:
            temp_scene = bpy.data.scenes.new("TempAudioCombine")
            bpy.context.window.scene = temp_scene

            if not temp_scene.sequence_editor:
                temp_scene.sequence_editor_create()

            current_frame = 1
            last_frame = 1

            for audio_file in input_files:
                if os.path.exists(audio_file):
                    strip = temp_scene.sequence_editor.sequences.new_sound(
                        name=os.path.basename(audio_file),
                        filepath=audio_file,
                        channel=1,
                        frame_start=current_frame
                    )
                    current_frame = strip.frame_final_end + 1
                    last_frame = max(last_frame, strip.frame_final_end)

            temp_scene.frame_start = 1
            temp_scene.frame_end = last_frame
            self.mixdown_audio_basic(output_file)
        finally:
            bpy.context.window.scene = original_scene
            bpy.data.scenes.remove(temp_scene)

    def mixdown_audio_basic(self, filepath):
        container = self.get_container_for_codec(self.audio_codec)
        codec = self.audio_codec
        channel_count = self.get_channel_count(self.audio_channels)

        channel_layouts = {
            1: 'MONO', 2: 'STEREO', 4: 'SURROUND_4',
            6: 'SURROUND_51', 8: 'SURROUND_71'
        }
        channel_layout = channel_layouts.get(channel_count, 'STEREO')
        actual_sample_rate = int(self.get_actual_sample_rate())

        mixdown_params = {
            'filepath': filepath,
            'container': container,
            'codec': codec,
            'format': 'S16' if codec == 'PCM' else 'FLTP',
            'rate': actual_sample_rate,
            'channels': channel_layout
        }

        if self.is_lossy_codec(codec):
            mixdown_params['bitrate'] = int(self.get_actual_bitrate())

        try:
            bpy.ops.sound.mixdown(**mixdown_params)
        except Exception as e:
            print(f"Advanced mixdown failed, using basic settings: {e}")
            bpy.ops.sound.mixdown(
                filepath=filepath,
                container=container,
                codec=codec
            )

    def mixdown_audio(self, filepath):
        self.mixdown_audio_basic(filepath)


def menu_func(self, context):
    if context.space_data.type == 'SEQUENCE_EDITOR':
        seq = context.scene.sequence_editor
        has_selected_audio = (seq and 
                            any(s.select and s.type == 'SOUND' for s in seq.sequences))
        
        op = self.layout.operator("sequencer.export_audio_filebrowser", icon='SOUND')
        if not has_selected_audio:
            op.enabled = False


classes = (
    AudioExporterProperties,
    SEQUENCER_OT_export_audio_filebrowser,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.audio_exporter_props = PointerProperty(type=AudioExporterProperties)
    bpy.types.SEQUENCER_MT_view.append(menu_func)


def unregister():
    bpy.types.SEQUENCER_MT_view.remove(menu_func)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, 'audio_exporter_props'):
        del bpy.types.Scene.audio_exporter_props


if __name__ == "__main__":
    register()
