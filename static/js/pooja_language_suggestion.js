/* Robust Manglish→Malayalam suggestions (uses /api/transliterate/ proxy) */
document.addEventListener("DOMContentLoaded", function () {
  const input = document.getElementById("pooja-name");
  const box = document.getElementById("suggestions");
  const modalEl = document.getElementById("poojaModal");

  if (!input || !box) {
    console.warn("Transliteration: missing #pooja-name or #suggestions element - aborting.");
    return;
  }

  // initial state (keep bootstrap's d-none on the element initially)
  let activeIndex = 0;
  let items = [];
  let debounceTimer = null;
  let abortController = null;
  const cache = new Map(); // simple in-memory cache: word -> suggestions array
  const DEBOUNCE_MS = 120;
  const MAX_SUGGESTIONS = 6;

  // helpers to show/hide using d-none class (Bootstrap uses !important)
  const showBox = () => box.classList.remove("d-none");
  const hideBox = () => box.classList.add("d-none");
  const clearBox = () => { box.innerHTML = ""; items = []; activeIndex = 0; };

  function getLastWord(txt) {
    if (!txt) return "";
    const parts = txt.trim().split(/\s+/);
    return parts.length ? parts[parts.length - 1] : "";
  }

  function replaceLastWord(txt, replacement) {
    const parts = (txt || "").trim().split(/\s+/);
    if (!parts.length) return (replacement || "") + " ";
    parts[parts.length - 1] = (replacement || "");
    return parts.join(" ") + " ";
  }

  function renderSuggestions(list) {
    clearBox();
    if (!Array.isArray(list) || list.length === 0) return hideBox();
    const slice = list.slice(0, MAX_SUGGESTIONS);
    slice.forEach((s, i) => {
      const div = document.createElement("div");
      div.className = "item" + (i === 0 ? " active" : "");
      div.setAttribute("role", "option");
      div.textContent = s;
      // mousedown prevents blur before click handler (keeps focus)
      div.addEventListener("mousedown", (evt) => {
        evt.preventDefault();
        commitSuggestion(s);
      });
      box.appendChild(div);
    });
    items = Array.from(box.querySelectorAll(".item"));
    activeIndex = 0;
    showBox();
  }

  function setActive(index) {
    if (!items.length) return;
    items[activeIndex]?.classList.remove("active");
    activeIndex = ((index % items.length) + items.length) % items.length;
    items[activeIndex]?.classList.add("active");
    // ensure visible
    items[activeIndex]?.scrollIntoView({ block: "nearest", inline: "nearest" });
  }

  function commitSuggestion(choice) {
    if (!choice) return;
    input.value = replaceLastWord(input.value, choice);
    // notify other listeners that input changed (so validation/other code runs)
    input.dispatchEvent(new Event("input", { bubbles: true }));
    clearBox();
    hideBox();
  }

  async function fetchSuggestionsFor(word) {
    if (!word) return [];
    if (cache.has(word)) return cache.get(word);

    // cancel previous
    if (abortController) {
      try { abortController.abort(); } catch (e) {}
    }
    abortController = new AbortController();
    try {
      const url = `/api/transliterate/?q=${encodeURIComponent(word)}`;
      const res = await fetch(url, { method: "GET", credentials: "same-origin", signal: abortController.signal });
      if (!res.ok) throw new Error("Network response not ok");
      const data = await res.json();
      const result = Array.isArray(data.suggestions) ? data.suggestions : [];
      cache.set(word, result);
      return result;
    } catch (err) {
      if (err.name === "AbortError") {
        // aborted — not an error we should report
        return [];
      }
      console.warn("Transliteration fetch error:", err);
      return [];
    }
  }

  async function handleInputEvent() {
    const last = getLastWord(input.value);
    if (!last) { clearBox(); hideBox(); return; }

    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
      const qAtCall = last;
      const suggestions = await fetchSuggestionsFor(qAtCall);
      // discard results if user typed further
      const currentLast = getLastWord(input.value);
      if (currentLast !== qAtCall) {
        // stale result — ignore
        return;
      }
      renderSuggestions(suggestions);
    }, DEBOUNCE_MS);
  }

  function handleKeyDown(e) {
    if (box.classList.contains("d-none") || !items.length) return;

    if (e.key === "Enter") {
      e.preventDefault();
      const choice = items[activeIndex]?.textContent || items[0]?.textContent;
      if (choice) commitSuggestion(choice);
    } else if (e.key === "Tab") {
      const choice = items[activeIndex]?.textContent || items[0]?.textContent;
      if (choice) commitSuggestion(choice);
      // allow default tab to move focus
    } else if (e.key === " ") {   // <<==== SPACE KEY HANDLING
      e.preventDefault();
      const choice = items[activeIndex]?.textContent || items[0]?.textContent;
      if (choice) commitSuggestion(choice);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive(activeIndex + 1);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive(activeIndex - 1);
    } else if (e.key === "Escape") {
      hideBox();
      clearBox();
    }
  }


  // Hide suggestions shortly after losing focus (allow click)
  function handleBlur() {
    setTimeout(() => {
      hideBox();
      clearBox();
    }, 150);
  }

  // wire events
  input.addEventListener("input", handleInputEvent);
  input.addEventListener("keydown", handleKeyDown);
  input.addEventListener("blur", handleBlur);

  // when modal shown, focus and select input
  if (modalEl) {
    modalEl.addEventListener("shown.bs.modal", () => {
      try { input.focus(); input.select(); } catch (e) {}
    });
  }
});