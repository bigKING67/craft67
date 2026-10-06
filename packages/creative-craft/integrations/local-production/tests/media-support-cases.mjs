// Render-support matrix cases (pure data, no side effects on import). The
// runner is tests/media-support.matrix.mjs; results: README「素材兼容」.
// [label, kind ('video' | 'audio'), file name, synthVideo/synthAudio options]
export const CASES = Object.freeze([
  ['H.264 8-bit yuv420p / AAC', 'video', 'h264.mp4', { acodec: 'aac' }],
  ['H.264 8-bit yuv420p / AAC', 'video', 'h264.mov', { acodec: 'aac' }],
  ['H.264 10-bit (High 10) yuv420p10le', 'video', 'h264-10bit.mp4', { pix: 'yuv420p10le' }],
  ['H.264 yuv422p (High 4:2:2)', 'video', 'h264-422.mp4', { pix: 'yuv422p' }],
  ['H.264 yuv444p (High 4:4:4)', 'video', 'h264-444.mp4', { pix: 'yuv444p' }],
  ['HEVC 8-bit (hvc1)', 'video', 'hevc.mp4', { vcodec: 'hevc' }],
  ['HEVC 8-bit (hvc1) / AAC', 'video', 'hevc.mov', { vcodec: 'hevc', acodec: 'aac' }],
  ['HEVC 10-bit (hvc1)', 'video', 'hevc-10bit.mov', { vcodec: 'hevc', pix: 'yuv420p10le' }],
  ['VP9 / Opus', 'video', 'vp9.webm', { vcodec: 'vp9', acodec: 'opus' }],
  ['H.264 / AAC', 'video', 'h264.mkv', { acodec: 'aac' }],
  ['H.264 + MP3 track', 'video', 'h264-mp3.mp4', { acodec: 'mp3' }],
  ['H.264 + Opus track', 'video', 'h264-opus.mp4', { acodec: 'opus' }],
  ['H.264 + PCM s16le track', 'video', 'h264-pcm.mov', { acodec: 'pcm' }],
  ['H.264 + FLAC track', 'video', 'h264-flac.mp4', { acodec: 'flac' }],
  ['H.264 + ALAC track', 'video', 'h264-alac.mov', { acodec: 'alac' }],
  ['H.264 + ALAC track', 'video', 'h264-alac.mp4', { acodec: 'alac' }],
  ['HEVC 10-bit HLG (iPhone HDR)', 'video', 'hevc-hlg.mov', { vcodec: 'hevc', pix: 'yuv420p10le', acodec: 'aac',
    extra: ['-color_primaries', 'bt2020', '-color_trc', 'arib-std-b67', '-colorspace', 'bt2020nc'] }],
  ['HEVC 8-bit variable frame rate', 'video', 'hevc-vfr.mov', { vcodec: 'hevc', vfr: true, acodec: 'aac' }],
  ['H.264 variable frame rate', 'video', 'h264-vfr.mp4', { vfr: true }],
  ['HEVC 8-bit rotated 90°', 'video', 'hevc-rot.mov', { vcodec: 'hevc', rotate: 90 }],
  ['AAC', 'audio', 'aac.m4a', { acodec: 'aac' }],
  ['MP3', 'audio', 'mp3.mp3', { acodec: 'mp3' }],
  ['Opus in MP4', 'audio', 'opus.mp4', { acodec: 'opus' }],
  ['Opus in Ogg', 'audio', 'opus.ogg', { acodec: 'opus' }],
  ['PCM s16le WAV', 'audio', 'pcm.wav', { acodec: 'pcm' }],
  ['FLAC', 'audio', 'flac.flac', { acodec: 'flac' }],
  ['ALAC in M4A', 'audio', 'alac.m4a', { acodec: 'alac' }],
].map(c => Object.freeze(c)));

export const MATRIX_FPS = 30;

// The v2 create spec of one case: the source as a video item, or (audio
// cases) a background video item plus the source on an audio track.
export function caseSpec([label, kind], { source, background, width, height, sourceIn = 0, fps = MATRIX_FPS }) {
  const media = (id, track, asset) => ({ id, track_id: track, kind: 'media', asset_id: asset, start_frame: 0, frames: fps - 3,
    source_in_seconds: sourceIn, volume: 1 });
  const video = kind === 'video';
  return { project_id: 'matrix', title: label, canvas: { width, height, fps },
    assets: video ? [{ id: 'src', path: source }] : [{ id: 'bg', path: background }, { id: 'src', path: source }],
    tracks: [{ id: 'v', kind: 'video', locked: false }, ...(video ? [] : [{ id: 'a', kind: 'audio', locked: false }])],
    items: video ? [media('one', 'v', 'src')] : [media('pic', 'v', 'bg'), media('snd', 'a', 'src')] };
}
