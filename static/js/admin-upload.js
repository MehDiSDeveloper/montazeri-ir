/* The admin's file inputs, made to say what they are doing (UploadWidget in
   apps/content/admin.py). A chosen file travels only when the form is saved,
   so: a preview of the file waiting, an undo for the choice, and a bar that
   stays on screen with the save button until it is pressed. Listeners are
   delegated, so a post image row added with "add another" works too.
   Admin only; the public pages never load this. */
(() => {
  "use strict";

  const size = (n) => (n < 1048576 ? `${Math.max(1, Math.round(n / 1024))} KB` : `${(n / 1048576).toFixed(1)} MB`);
  const fa = (n) => String(n).replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]);
  const urls = new WeakMap();
  let bar = null;
  let sending = false;

  const fileOf = (box) => box.querySelector('input[type="file"]');
  const clearOf = (box) => box.querySelector('input[type="checkbox"]');
  const waiting = () =>
    [...document.querySelectorAll("[data-upload]")].filter((box) => fileOf(box)?.files.length || clearOf(box)?.checked);

  function paint(box) {
    const input = fileOf(box);
    const clear = clearOf(box);
    const file = input?.files[0];
    const card = box.querySelector(".upload-new");
    const img = card.querySelector("img");

    if (urls.has(input)) URL.revokeObjectURL(urls.get(input));
    urls.delete(input);
    if (file && file.type.startsWith("image/")) {
      urls.set(input, URL.createObjectURL(file));
      img.src = urls.get(input);
      img.hidden = false;
    } else {
      img.removeAttribute("src");
      img.hidden = true;
    }
    card.querySelector(".upload-name").textContent = file ? `${file.name} · ${size(file.size)}` : "";
    card.hidden = !file;
    box.querySelector(".upload-gone").hidden = !clear?.checked;
    box.classList.toggle("is-new", Boolean(file));
    box.classList.toggle("is-gone", Boolean(clear?.checked));
    status();
  }

  function status() {
    const n = waiting().length;
    if (!bar) {
      if (!n) return;
      bar = document.createElement("div");
      bar.className = "upload-bar";
      bar.setAttribute("role", "status");
      bar.innerHTML = '<span></span><button type="button" class="button default">ذخیره</button>';
      bar.querySelector("button").addEventListener("click", save);
      document.body.append(bar);
    }
    bar.hidden = !n;
    if (!sending) {
      bar.querySelector("span").textContent = `${fa(n)} تغییر در عکس‌ها و فایل‌ها ذخیره نشده؛ تا «ذخیره» را نزنید روی سایت اعمال نمی‌شود.`;
    }
  }

  // «ذخیره» from the bar is «ذخیره و ادامه ویرایش»: the page comes back with
  // the file that is now live under each field, which is the proof it worked.
  function save() {
    const form = waiting()[0]?.closest("form");
    if (!form) return;
    const button = form.querySelector('[name="_continue"]') || form.querySelector('[type="submit"]');
    form.requestSubmit ? form.requestSubmit(button) : button.click();
  }

  document.addEventListener("change", (e) => {
    const box = e.target.closest?.("[data-upload]");
    if (!box) return;
    // Django refuses a new file and "clear" together, so one undoes the other.
    if (e.target.type === "file" && e.target.files.length && clearOf(box)) clearOf(box).checked = false;
    if (e.target.type === "checkbox" && e.target.checked) fileOf(box).value = "";
    paint(box);
  });

  document.addEventListener("click", (e) => {
    const undo = e.target.closest?.("[data-upload-undo]");
    if (!undo) return;
    const box = undo.closest("[data-upload]");
    fileOf(box).value = "";
    paint(box);
  });

  document.addEventListener("submit", () => {
    sending = true;
    if (bar && !bar.hidden) {
      bar.querySelector("span").textContent = "در حال فرستادن… صفحه را نبندید.";
      bar.querySelector("button").disabled = true;
    }
  });

  // Leaving with a file chosen and not saved would lose it without a word.
  window.addEventListener("beforeunload", (e) => {
    if (sending || !waiting().length) return;
    e.preventDefault();
    e.returnValue = "";
  });

  // A back/forward restore can bring a chosen file back with the page.
  window.addEventListener("pageshow", () => {
    sending = false;
    if (bar) bar.querySelector("button").disabled = false;
    document.querySelectorAll("[data-upload]").forEach(paint);
  });
})();
