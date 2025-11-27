document.addEventListener("DOMContentLoaded", function(){

  // Customer Name Malayalam suggestions for Subscription Modal
  (function(){
    const input = document.querySelector("[name='customer_name']");
    if(!input) return;

    // Use the existing #suggestions style
    let box = document.getElementById("suggestions");
    if(!box){
      box = document.createElement("div");
      box.id = "suggestions"; // reuse base.html style
      box.className = "d-none"; // initially hidden
      input.parentElement.style.position = "relative";
      input.parentElement.appendChild(box);
    }

    let activeIndex = 0;
    let items = [];
    let debounceTimer = null;
    let abortController = null;
    const cache = new Map();
    const DEBOUNCE_MS = 120;
    const MAX_SUGGESTIONS = 6;

    const showBox = ()=>box.classList.remove("d-none");
    const hideBox = ()=>box.classList.add("d-none");
    const clearBox = ()=>{ box.innerHTML=""; items=[]; activeIndex=0; };

    function getLastWord(txt){
      if(!txt) return "";
      const parts = txt.trim().split(/\s+/);
      return parts.length ? parts[parts.length-1] : "";
    }

    function replaceLastWord(txt, replacement){
      const parts = (txt||"").trim().split(/\s+/);
      if(!parts.length) return (replacement||"")+" ";
      parts[parts.length-1] = replacement||"";
      return parts.join(" ")+" ";
    }

    function renderSuggestions(list){
      clearBox();
      if(!Array.isArray(list) || !list.length) return hideBox();
      const slice = list.slice(0, MAX_SUGGESTIONS);
      slice.forEach((s,i)=>{
        const div = document.createElement("div");
        div.className = "item"+(i===0?" active":"");
        div.textContent = s;
        div.addEventListener("mousedown",(evt)=>{
          evt.preventDefault();
          commitSuggestion(s);
        });
        box.appendChild(div);
      });
      items = Array.from(box.querySelectorAll(".item"));
      activeIndex=0;
      showBox();
    }

    function setActive(index){
      if(!items.length) return;
      items[activeIndex]?.classList.remove("active");
      activeIndex = ((index%items.length)+items.length)%items.length;
      items[activeIndex]?.classList.add("active");
      items[activeIndex]?.scrollIntoView({block:"nearest", inline:"nearest"});
    }

    function commitSuggestion(choice){
      if(!choice) return;
      input.value = replaceLastWord(input.value, choice);
      input.dispatchEvent(new Event("input",{bubbles:true}));
      clearBox();
      hideBox();
    }

    async function fetchSuggestionsFor(word){
      if(!word) return [];
      if(cache.has(word)) return cache.get(word);

      if(abortController){
        try{ abortController.abort(); }catch(e){}
      }
      abortController = new AbortController();
      try{
        const url = `/api/transliterate/?q=${encodeURIComponent(word)}`;
        const res = await fetch(url, {method:"GET", credentials:"same-origin", signal:abortController.signal});
        if(!res.ok) throw new Error("Network response not ok");
        const data = await res.json();
        const result = Array.isArray(data.suggestions) ? data.suggestions : [];
        cache.set(word,result);
        return result;
      }catch(err){
        if(err.name==="AbortError") return [];
        console.warn("Transliteration fetch error:", err);
        return [];
      }
    }

    async function handleInputEvent(){
      const last = getLastWord(input.value);
      if(!last){ clearBox(); hideBox(); return; }
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(async ()=>{
        const qAtCall = last;
        const suggestions = await fetchSuggestionsFor(qAtCall);
        if(getLastWord(input.value)!==qAtCall) return; // stale
        renderSuggestions(suggestions);
      }, DEBOUNCE_MS);
    }

    function handleKeyDown(e){
      if(box.classList.contains("d-none") || !items.length) return;

      if(e.key==="Enter"||e.key==="Tab"||e.key===" "){
        e.preventDefault();
        const choice = items[activeIndex]?.textContent || items[0]?.textContent;
        if(choice) commitSuggestion(choice);
      } else if(e.key==="ArrowDown"){
        e.preventDefault();
        setActive(activeIndex+1);
      } else if(e.key==="ArrowUp"){
        e.preventDefault();
        setActive(activeIndex-1);
      } else if(e.key==="Escape"){
        hideBox();
        clearBox();
      }
    }

    function handleBlur(){
      setTimeout(()=>{ hideBox(); clearBox(); },150);
    }

    input.addEventListener("input", handleInputEvent);
    input.addEventListener("keydown", handleKeyDown);
    input.addEventListener("blur", handleBlur);

    // Focus input when modal opens
    const modalEl = document.getElementById("subModal");
    if(modalEl){
      modalEl.addEventListener("shown.bs.modal", ()=>{
        try{ input.focus(); input.select(); }catch(e){}
      });
    }

  })();

});