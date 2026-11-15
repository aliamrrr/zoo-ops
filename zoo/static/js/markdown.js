/**
 * Renders the small Markdown subset the tickets use: headings, paragraphs, quotes, lists,
 * **bold**, `code` and [links](https://...). It builds DOM nodes, never HTML strings.
 */
const INLINE = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)\s]+\))/g;

function inline(text) {
  const fragment = document.createDocumentFragment();
  for (const part of text.split(INLINE)) {
    if (!part) continue;
    if (part.startsWith("**")) {
      const node = document.createElement("strong");
      node.textContent = part.slice(2, -2);
      fragment.append(node);
    } else if (part.startsWith("`")) {
      const node = document.createElement("code");
      node.textContent = part.slice(1, -1);
      fragment.append(node);
    } else if (part.startsWith("[")) {
      const [, label, href] = part.match(/^\[([^\]]+)\]\(([^)\s]+)\)$/);
      const node = document.createElement("a");
      node.textContent = label;
      if (/^https:\/\//.test(href)) {
        node.href = href;
        node.target = "_blank";
        node.rel = "noopener noreferrer";
      }
      fragment.append(node);
    } else {
      fragment.append(part);
    }
  }
  return fragment;
}

function block(tag, text, className) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  node.append(inline(text));
  return node;
}

export function renderMarkdown(source) {
  const root = document.createDocumentFragment();
  let paragraph = [];
  let list = null;
  let quote = null;

  const flush = () => {
    if (paragraph.length) root.append(block("p", paragraph.join(" ")));
    paragraph = [];
    list = null;
    quote = null;
  };

  for (const raw of source.split("\n")) {
    const line = raw.trimEnd();
    const heading = line.match(/^(#{1,3})\s+(.*)$/);
    const ordered = line.match(/^\d+\.\s+(.*)$/);
    const bullet = line.match(/^[-*]\s+(.*)$/);
    const quoted = line.match(/^>\s?(.*)$/);
    if (!line.trim()) {
      flush();
    } else if (/^\*\*[^*]+:\*\*/.test(line)) {
      flush();
      root.append(block("p", line, "md-meta"));
    } else if (heading) {
      flush();
      root.append(block(heading[1].length === 1 ? "h3" : "h4", heading[2], "md-heading"));
    } else if (ordered || bullet) {
      if (paragraph.length) flush();
      const tag = ordered ? "ol" : "ul";
      if (!list || list.tagName.toLowerCase() !== tag) {
        list = document.createElement(tag);
        root.append(list);
      }
      list.append(block("li", (ordered || bullet)[1]));
    } else if (quoted) {
      if (!quote) {
        if (paragraph.length) flush();
        quote = document.createElement("blockquote");
        root.append(quote);
      }
      quote.append(inline(`${quoted[1]} `));
    } else if (list && /^\s+/.test(raw)) {
      list.lastElementChild.append(" ", inline(line.trim()));
    } else {
      paragraph.push(line.trim());
    }
  }
  flush();
  return root;
}
