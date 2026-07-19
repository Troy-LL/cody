#!/usr/bin/env bash
# Record Confetti Club demo on the cloud display, then wrap as macOS-style MP4.
set -euo pipefail

DEMO_DIR=/tmp/party-game-cloud/demo
OUT_DIR="$DEMO_DIR/video"
mkdir -p "$OUT_DIR"
RAW="$OUT_DIR/raw-capture.mp4"
FINAL="$OUT_DIR/confetti-club-macos-demo.mp4"
LOG="$OUT_DIR/record.log"

export DISPLAY=:1

# Start ffmpeg screen capture of the VNC desktop
# 1440x900 crop around a typical centered browser; full :1 screen as fallback
GEOM=$(xdpyinfo -display :1 2>/dev/null | awk '/dimensions/{print $2}')
echo "Display geometry: $GEOM" | tee "$LOG"
W=${GEOM%x*}
H=${GEOM#*x}

ffmpeg -y -f x11grab -video_size "${W}x${H}" -framerate 30 -i :1.0 \
  -c:v libx264 -pix_fmt yuv420p -preset ultrafast -crf 23 \
  "$RAW" >>"$LOG" 2>&1 &
FFPID=$!
echo "ffmpeg pid=$FFPID" | tee -a "$LOG"
sleep 2

# Run paced headful demo (Chrome visible on :1)
cd "$DEMO_DIR"
SLOWMO=80 PAUSE=900 HEADLESS=0 node record-demo.mjs >>"$LOG" 2>&1 || {
  echo "demo script failed; see $LOG" | tee -a "$LOG"
  kill "$FFPID" 2>/dev/null || true
  exit 1
}

sleep 2
kill -INT "$FFPID" 2>/dev/null || true
wait "$FFPID" 2>/dev/null || true

# If raw is tiny/empty, fall back to screenshot slideshow
if [[ ! -s "$RAW" ]] || [[ $(stat -c%s "$RAW") -lt 100000 ]]; then
  echo "Raw capture too small; building slideshow from shots/" | tee -a "$LOG"
  # Build concat list from screenshots
  LIST="$OUT_DIR/slides.txt"
  : > "$LIST"
  for f in "$DEMO_DIR"/shots/*.png; do
    printf "file '%s'\nduration 1.6\n" "$f" >> "$LIST"
  done
  # last frame needs a file line without duration for concat demuxer
  last=$(ls "$DEMO_DIR"/shots/*.png | tail -1)
  printf "file '%s'\n" "$last" >> "$LIST"
  ffmpeg -y -f concat -safe 0 -i "$LIST" -vf "scale=1440:900:force_original_aspect_ratio=decrease,pad=1440:900:(ow-iw)/2:(oh-ih)/2,format=yuv420p,fps=30" \
    -c:v libx264 -pix_fmt yuv420p "$RAW" >>"$LOG" 2>&1
fi

# Compose macOS window chrome: dark title bar + traffic lights + caption
# Draw overlay via ffmpeg filters
ffmpeg -y -i "$RAW" -vf "
scale=1400:820:force_original_aspect_ratio=decrease,
pad=1440:900:20:60:0x1c1c1e,
drawbox=x=0:y=0:w=1440:h=52:color=0x2c2c2e@1:t=fill,
drawbox=x=0:y=52:w=1440:h=1:color=0x3a3a3c@1:t=fill,
drawtext=text='●':fontcolor=0xff5f57:fontsize=22:x=18:y=14,
drawtext=text='●':fontcolor=0xffbd2e:fontsize=22:x=42:y=14,
drawtext=text='●':fontcolor=0x28c840:fontsize=22:x=66:y=14,
drawtext=text='Confetti Club — Safari':fontcolor=0xe5e5e7:fontsize=16:x=(w-text_w)/2:y=16:font='DejaVu Sans'
" -c:v libx264 -pix_fmt yuv420p -movflags +faststart "$FINAL" >>"$LOG" 2>&1

ls -lah "$RAW" "$FINAL" | tee -a "$LOG"
echo "DONE=$FINAL"
