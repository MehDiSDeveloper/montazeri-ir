// Temporary fun test: a Persian compliment about Mysa pops up on every tap.
(function () {
  var words = [
    "میسا فوق‌العاده‌ست!", "میسا بی‌نظیره ✨", "میسا یه دونه‌ست 💖",
    "میسا خیلی باحاله!", "میسا محشره 🌟", "دنیا با میسا قشنگ‌تره",
    "میسا یه ستاره‌ست ⭐", "میسا همیشه می‌درخشه", "میسا بهترینه 👑",
    "میسا یعنی شادی 🎈", "میسا دوست‌داشتنیه 🌸", "میسا معرکه‌ست!"
  ];
  var colors = ["#8e2c48", "#a4343a", "#7b1e3a", "#2b2b2b", "#c08497",
    "#b56576", "#6d597a", "#e5989b", "#9d4b6b", "#5e3c58", "#d4a5a5", "#843b62"];
  var css = document.createElement("style");
  css.textContent = ".mysa-pop{position:fixed;z-index:99999;pointer-events:none;" +
    "padding:8px 14px;border-radius:18px;color:#fff;font-weight:700;font-size:16px;" +
    "white-space:nowrap;direction:rtl;box-shadow:0 4px 14px rgba(0,0,0,.2);" +
    "transform:translate(-50%,-50%);animation:mysa 3s ease-out forwards}" +
    "@keyframes mysa{0%{opacity:0;transform:translate(-50%,-30%) scale(.6)}" +
    "15%{opacity:1;transform:translate(-50%,-60%) scale(1.1)}" +
    "70%{opacity:1}100%{opacity:0;transform:translate(-50%,-220%) scale(1)}}";
  document.head.appendChild(css);
  document.addEventListener("pointerdown", function (e) {
    var el = document.createElement("div");
    el.className = "mysa-pop";
    el.textContent = words[Math.floor(Math.random() * words.length)];
    el.style.background = colors[Math.floor(Math.random() * colors.length)];
    el.style.left = Math.min(Math.max(e.clientX, 90), innerWidth - 90) + "px";
    el.style.top = e.clientY + "px";
    document.body.appendChild(el);
    setTimeout(function () { el.remove(); }, 3000);
  }, true);
})();
