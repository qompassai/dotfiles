#!/usr/bin/env bash
set -euo pipefail
usage()
{
    cat << 'USAGE'
Usage:
  loop_media.sh -v input_video -a input_audio -o output.mp4 [options]
Purpose:
  Loops a video so it matches the audio duration, then muxes them into a final MP4.
  This recreates the neutral technical effect of a repeating visual synced to a longer audio track.
Required:
  -v FILE   Input video or animated GIF/webm/mp4
  -a FILE   Input audio file
  -o FILE   Output MP4 file
Options:
  -f FPS        Output frame rate for GIF/image inputs or re-encoding (default: 30)
  -c CRF        Video quality for x264 encode, lower is higher quality (default: 20)
  -p PRESET     x264 preset: ultrafast..veryslow (default: medium)
  -w            Re-encode video even if input is already H.264
  -n            Trim audio/video to the shorter stream instead of forcing video to audio length
  -h            Show this help
Examples:
  loop_media.sh -v loop.mp4 -a narration.wav -o final.mp4
  loop_media.sh -v anim.gif -a track.flac -o final.mp4 -f 24 -c 18
USAGE
}
require_cmd()
{
    command -v "$1" > /dev/null 2>&1 || {
        echo "Missing required command: $1" >&2
        exit 1
    }
}
video=""
audio=""
out=""
fps="30"
crf="20"
preset="medium"
force_reencode=0
shortest=0
while getopts ":v:a:o:f:c:p:wnh" opt; do
    case "$opt" in
        v) video="$OPTARG" ;;
        a) audio="$OPTARG" ;;
        o) out="$OPTARG" ;;
        f) fps="$OPTARG" ;;
        c) crf="$OPTARG" ;;
        p) preset="$OPTARG" ;;
        w) force_reencode=1 ;;
        n) shortest=1 ;;
        h)
            usage
            exit 0
            ;;
        :)
            echo "Option -$OPTARG requires an argument" >&2
            usage
            exit 1
            ;;
        \?)
            echo "Unknown option: -$OPTARG" >&2
            usage
            exit 1
            ;;
    esac
done
[[ -n $video && -n $audio && -n $out ]] || {
    usage
    exit 1
}
require_cmd ffmpeg
require_cmd ffprobe
[[ -f $video ]] || {
    echo "Video not found: $video" >&2
    exit 1
}
[[ -f $audio ]] || {
    echo "Audio not found: $audio" >&2
    exit 1
}
get_duration()
{
    ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$1"
}
audio_dur=$(get_duration "$audio")
video_dur=$(get_duration "$video")
[[ -n $audio_dur && -n $video_dur ]] || {
    echo "Could not read media durations" >&2
    exit 1
}
workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT
video_codec=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of csv=p=0 "$video" || true)
video_ext="${video##*.}"
video_ext_lc=$(printf '%s' "$video_ext" | tr '[:upper:]' '[:lower:]')
need_intermediate=0
case "$video_ext_lc" in
    gif | png | jpg | jpeg | webp) need_intermediate=1 ;;
esac
if [[ $video_codec != "h264" ]]; then
    need_intermediate=1
fi
if [[ $force_reencode -eq 1 ]]; then
    need_intermediate=1
fi

loop_source="$video"

if [[ $need_intermediate -eq 1 ]]; then
    loop_source="$workdir/loopable.mp4"
    ffmpeg -y \
        -stream_loop -1 -i "$video" \
        -t "$audio_dur" \
        -r "$fps" \
        -an \
        -c:v libx264 -pix_fmt yuv420p -preset "$preset" -crf "$crf" \
        "$loop_source"
fi
ffmpeg_cmd=(ffmpeg -y -stream_loop -1 -i "$loop_source" -i "$audio")
if [[ $shortest -eq 1 ]]; then
    ffmpeg_cmd+=(-map 0:v:0 -map 1:a:0 -c:v libx264 -preset "$preset" -crf "$crf" -pix_fmt yuv420p -c:a aac -b:a 192k -shortest "$out")
else
    ffmpeg_cmd+=(-map 0:v:0 -map 1:a:0 -t "$audio_dur" -c:v libx264 -preset "$preset" -crf "$crf" -pix_fmt yuv420p -c:a aac -b:a 192k "$out")
fi
"${ffmpeg_cmd[@]}"
echo "Created: $out"
echo "Audio duration: $audio_dur seconds"
echo "Source video duration: $video_dur seconds"
