import { graphicPlacement, SAFE_MARGIN } from './templates.mjs';

// Safe-area boxes for captions and graphics, as fractions of the canvas. Caption
// boxes mirror the compiled CSS (composition.mjs) instead of measuring pixels:
// text width is estimated per character (full-width CJK and
// symbols 1 em, other characters 0.55 em, spaces 0.3 em), so a box is an
// estimate, not a browser measurement.
export const textEm = value => Array.from(value).reduce((sum, ch) => sum + (ch === ' ' ? 0.3 : /[ᄀ-ᇿ⺀-꓏가-힯豈-﫿︰-﹏＀-￯\u{20000}-\u{3ffff}]/u.test(ch) ? 1 : 0.55), 0);
const round = v => Math.round(v * 1e4) / 1e4;

// Caption box: the .caption block spans 7%–93% of the width; lines wrap inside
// it. Styled captions centre on centerY with line-height 1.1 and a stroke;
// default captions sit on bottom 8% with line-height 1.35 and 8 px padding.
export function captionBox(canvas, caption) {
  const { width: W, height: H } = canvas, boxWidth = 0.86 * W;
  const styled = caption.style, font = styled ? H * styled.fontHeight : Math.round(H * 0.052);
  const stroke = styled ? H * styled.strokeWidth : 0, padding = styled ? 0 : 8;
  const widths = caption.text.split(/\r?\n/).map(line => textEm(line) * font + 2 * stroke);
  const lines = widths.reduce((n, w) => n + Math.max(1, Math.ceil(w / boxWidth)), 0);
  const height = lines * font * (styled ? 1.1 : 1.35) + 2 * (stroke + padding);
  const textWidth = Math.min(boxWidth, Math.max(...widths)) + 2 * padding;
  const top = styled ? styled.centerY * H - height / 2 : 0.92 * H - height;
  const left = styled ? (W - textWidth) / 2 : 0.07 * W;
  return { left: round(left / W), top: round(top / H), right: round((styled ? left + textWidth : 0.93 * W) / W), bottom: round((top + height) / H), lines };
}

// Graphic box: the box of the item's template placement (fractions),
// independent of the canvas. Every placement's position in the safe area is
// guaranteed when the template loads (templates.mjs validateTemplate); no
// text-fit estimate is made here.
export function graphicBox(item, templates) {
  const { box } = graphicPlacement(item, templates);
  return { left: box.left, top: box.top, right: round(box.left + box.width), bottom: round(box.top + box.height) };
}

export const insideSafeArea = b => b.left >= SAFE_MARGIN - 1e-9 && b.top >= SAFE_MARGIN - 1e-9 && b.right <= 1 - SAFE_MARGIN + 1e-9 && b.bottom <= 1 - SAFE_MARGIN + 1e-9;
