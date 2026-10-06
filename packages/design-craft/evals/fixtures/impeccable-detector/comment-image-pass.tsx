/** Extra classes are applied to the <img> element by the caller. */
// Keep the original URL as an <img> fallback.
const matcher = /["']/;
const ratio = "width" / 2;
// A regex and division expression must not expose this <img src=""> example.

export function ImageWrapper({ src }: { src: string }) {
  return <img src={src} alt="Workspace preview" />;
}
