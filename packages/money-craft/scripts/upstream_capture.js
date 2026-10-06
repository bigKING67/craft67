// Run through browser67 in a task-owned public documentation tab.
// The caller supplies the fully expanded catalog; this helper does not discover it.
function upstreamStructureTokens(article) {
  const tokens = [];
  const structural = new Set(["table", "tr", "td", "th", "pre"]);
  function walk(node, inside = false) {
    if (node.nodeType === 3 && inside) {
      const last = tokens[tokens.length - 1];
      if (last && last[0] === "text") last[1] += node.data;
      else tokens.push(["text", node.data]);
      return;
    }
    if (node.nodeType !== 1) return;
    const tag = node.tagName.toLowerCase();
    if (tag === "script" || tag === "style") return;
    if (structural.has(tag)) tokens.push(["open", tag, node.getAttribute("rowspan") || "", node.getAttribute("colspan") || ""]);
    for (const child of node.childNodes) walk(child, inside || tag === "table" || tag === "pre");
    if (structural.has(tag)) tokens.push(["close", tag]);
  }
  walk(article);
  return tokens;
}

async function upstreamStructureHash(article) {
  const bytes = new TextEncoder().encode(JSON.stringify(upstreamStructureTokens(article)));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, "0")).join("");
}

async function captureUpstreamPages(catalog, { includeText = true } = {}) {
  return Promise.all(catalog.map(async item => {
    const url = new URL(item.url);
    if (url.origin !== location.origin || !/^\/docs(?:\/|$)/.test(url.pathname) || url.search || url.hash || url.username || url.password) {
      throw new Error("capture only accepts public same-origin documentation URLs");
    }
    const response = await fetch(url, { credentials: "omit" });
    const document = new DOMParser().parseFromString(await response.text(), "text/html");
    const articles = [...document.querySelectorAll("article")].filter(node => !node.parentElement.closest("article"));
    const page = { url: item.url, title: item.title, final_url: response.url, status: response.status };
    if (articles.length !== 1) return { ...page, status: 0 };
    const article = articles[0];
    page.structure_sha256 = await upstreamStructureHash(article);
    if (includeText) page.text = article.textContent;
    return page;
  }));
}
