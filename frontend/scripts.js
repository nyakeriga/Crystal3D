<script defer>
/* >>> change this if the backend URL/port is different in prod <<< */
const API_BASE = "http://localhost:8000";

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const $ = id => document.getElementById(id);
  const form          = $("uploadForm");
  const fileInput     = $("fileInput");
  const fmtSelect     = $("formatSelect");
  const bgSelect      = $("bgSelect");
  const depthInt      = $("depthIntensity");
  const bgThresh      = $("bgThreshold");
  const crystSize     = $("crystalSize");

  const msgBox   = $("responseContainer");
  const dlLink   = $("downloadLink");
  const btn      = form.querySelector("button[type='submit']");

  const gPrev    = $("grayscalePreview"), gWrap=$("grayscalePreviewContainer");
  const dPrev    = $("depthPreview"),     dWrap=$("depthPreviewContainer");

  // ─── helpers ────────────────────────────────────────────────
  const showMsg = (txt,col="blue")=>{
    msgBox.innerHTML=`<p class="text-${col}-600 font-semibold">${txt}</p>`;
    msgBox.classList.remove("hidden");
  };
  const hideMsg = ()=>msgBox.classList.add("hidden");
  const hidePrev = ()=>{gWrap.classList.add("hidden");dWrap.classList.add("hidden");};

  // ─── preview on image change ────────────────────────────────
  fileInput.addEventListener("change", async ()=>{
    const file=fileInput.files[0]; if(!file) return;
    const fd=new FormData(); fd.append("file",file);
    const url=`${API_BASE}/preview-depthmap?bg_color=${bgSelect.value}`;
    try{
      showMsg("Generating depth‑map preview…");
      const r=await fetch(url,{method:"POST",body:fd});
      if(!r.ok) throw new Error(await r.text());
      const j=await r.json();
      gPrev.src=`${API_BASE}${j.grayscale_url}`;
      dPrev.src=`${API_BASE}${j.depth_url}`;
      gWrap.classList.remove("hidden"); dWrap.classList.remove("hidden");
      hideMsg();
    }catch(e){console.error(e);showMsg(`Preview error: ${e.message}`,"red");hidePrev();}
  });

  // ─── upload & export ────────────────────────────────────────
  form.addEventListener("submit", async e=>{
    e.preventDefault();
    const file=fileInput.files[0]; if(!file) return showMsg("Choose an image","red");
    const fd=new FormData();
    fd.append("file",file);
    fd.append("depth_intensity",depthInt.value);
    fd.append("bg_threshold",bgThresh.value);
    fd.append("crystal_size",crystSize.value);

    const url=`${API_BASE}/upload-and-export/${fmtSelect.value}/`;
    try{
      btn.disabled=true; btn.textContent="Processing…"; showMsg("Exporting…");
      const r=await fetch(url,{method:"POST",body:fd});
      if(!r.ok) throw new Error(await r.text());
      const j=await r.json();
      dlLink.href   = `${API_BASE}${j.file}`;
      dlLink.classList.remove("hidden");
      showMsg(j.message || "3D model ready!","green");
    }catch(e){console.error(e);showMsg(`Export error: ${e.message}`,"red"); dlLink.classList.add("hidden");}
    finally{btn.disabled=false;btn.textContent="Generate 3D Model";}
  });
});
</script>

