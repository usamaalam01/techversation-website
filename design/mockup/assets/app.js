/* Techversation mockup behavior. Everything reads assets/data.js (real course data); nothing is sent anywhere. */
(function () {
  "use strict";
  var TV = window.TV;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var qs = new URLSearchParams(location.search);
  var page = document.body.getAttribute("data-page");

  /* ---------- storage (every access guarded) ---------- */
  function load(k, fb) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : fb; } catch (e) { return fb; } }
  function save(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* private mode */ } }
  function getDone(slug) { return load("tv-done-" + slug, slug === "csm" ? ["00", "01", "02", "03"] : []); }
  function setDone(slug, list) { save("tv-done-" + slug, list); }

  /* ---------- icons ---------- */
  var I = {
    search: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    play: '<svg width="30" height="30" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5.5v13a1 1 0 0 0 1.5.86l10.5-6.5a1 1 0 0 0 0-1.72L9.5 4.64A1 1 0 0 0 8 5.5Z"/></svg>',
    check: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>',
    sun: '<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
    moon: '<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a7 7 0 0 0 11 11Z"/></svg>',
    menu: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
    arrow: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    video: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="3"/><path d="m10.5 9.5 4 2.5-4 2.5Z" fill="currentColor"/></svg>',
    doc: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/></svg>',
    cal: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="5" width="16" height="15" rx="3"/><path d="M8 3v4M16 3v4M4 10h16M8 14h3"/></svg>',
    yt: '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M21.6 7.2a2.5 2.5 0 0 0-1.76-1.77C18.3 5 12 5 12 5s-6.3 0-7.84.43A2.5 2.5 0 0 0 2.4 7.2 26 26 0 0 0 2 12a26 26 0 0 0 .4 4.8 2.5 2.5 0 0 0 1.76 1.77C5.7 19 12 19 12 19s6.3 0 7.84-.43a2.5 2.5 0 0 0 1.76-1.77A26 26 0 0 0 22 12a26 26 0 0 0-.4-4.8ZM10 15V9l5.2 3Z"/></svg>',
    dl: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v11M7 11l5 5 5-5M5 20h14"/></svg>',
    chat: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16v11H9l-5 4Z"/></svg>'
  };

  /* ---------- lookups ---------- */
  var courses = TV.courses;
  var courseList = Object.keys(courses).map(function (k) { return courses[k]; });
  var inst = {}; TV.institutes.forEach(function (i) { inst[i.id] = i; });
  function dur(min) { if (min == null) return ""; var h = Math.floor(min / 60), m = min % 60; return h ? h + " h " + (m ? m + " min" : "") : m + " min"; }
  function modMinutes(m) { var s = 0, ok = true; m.parts.forEach(function (p) { if (!p.len) { ok = false; return; } var a = p.len.split(":"); s += +a[0] * 60 + +a[1]; }); return ok ? s : null; }
  function mmss(s) { s = Math.round(s); var m = Math.floor(s / 60), x = s % 60; return m + ":" + (x < 10 ? "0" : "") + x; }
  function url(path, params) { var u = new URLSearchParams(params || {}); var s = u.toString(); return path + (s ? "?" + s : ""); }
  function ring(pct, size) {
    var r = (size - 8) / 2, c = 2 * Math.PI * r, id = "g" + Math.random().toString(36).slice(2, 7);
    return '<svg width="' + size + '" height="' + size + '" viewBox="0 0 ' + size + " " + size + '" aria-hidden="true"><defs><linearGradient id="' + id + '" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4fd1e6"/><stop offset=".4" stop-color="#5b86ff"/><stop offset=".75" stop-color="#9370ff"/><stop offset="1" stop-color="#e353c8"/></linearGradient></defs><circle cx="' + size / 2 + '" cy="' + size / 2 + '" r="' + r + '" fill="none" stroke="var(--surface-3)" stroke-width="5"/><circle cx="' + size / 2 + '" cy="' + size / 2 + '" r="' + r + '" fill="none" stroke="url(#' + id + ')" stroke-width="5" stroke-linecap="round" stroke-dasharray="' + (c * pct).toFixed(1) + " " + c.toFixed(1) + '" transform="rotate(-90 ' + size / 2 + " " + size / 2 + ')"/></svg>';
  }
  function toast(msg) {
    var t = $("#toast"); if (!t) return;
    t.textContent = msg; t.classList.add("show");
    clearTimeout(toast.h); toast.h = setTimeout(function () { t.classList.remove("show"); }, 3200);
  }

  /* ---------- theme ---------- */
  var root = document.documentElement;
  function applyTheme(t) { if (t) root.setAttribute("data-theme", t); else root.removeAttribute("data-theme"); }
  applyTheme(qs.get("theme") === "light" || qs.get("theme") === "dark" ? qs.get("theme") : load("tv-theme", null));   // ?theme=light for a quick look

  /* ---------- shared chrome ---------- */
  function chrome() {
    var top = $("#top");
    if (top) {
      var nav = [["index.html#certs", "Certifications", "home"], ["index.html#training", "Training", ""], ["study-plan.html", "Study plan", "plan"], ["search.html", "Search", "search"]];
      top.innerHTML =
        '<div class="mock-banner"><div class="wrap"><b>Design mockup</b><span>Sample data from the real CSM, PMP, KCNA, AIGP and CDMP courses. Links open sample pages. Nothing is sent anywhere.</span></div></div>' +
        '<header class="site-header"><div class="wrap bar">' +
        '<a class="brand" href="index.html"><img src="assets/logo.jpg" alt="" width="38" height="38"><span>Tech<b>versation</b></span></a>' +
        '<nav class="nav" id="nav" aria-label="Main">' + nav.map(function (n) { return '<a href="' + n[0] + '"' + (page === n[2] ? ' aria-current="page"' : "") + ">" + n[1] + "</a>"; }).join("") + "</nav>" +
        '<span class="spacer"></span>' +
        '<form class="mini-search" action="search.html" role="search">' + I.search + '<input name="q" type="search" placeholder="Search courses, modules, terms" aria-label="Search the site"></form>' +
        '<button class="icon-btn" id="theme" type="button" aria-label="Switch between dark and light theme"></button>' +
        '<a class="btn btn-yt" href="#" id="sub" title="Channel link is added at launch">' + I.yt + "<span>Subscribe</span></a>" +
        '<button class="icon-btn menu-btn" id="menu" type="button" aria-label="Open the menu" aria-expanded="false">' + I.menu + "</button>" +
        "</div></header>";
      var tb = $("#theme");
      var paint = function () { tb.innerHTML = root.getAttribute("data-theme") === "light" ? I.moon : I.sun; };
      paint();
      tb.addEventListener("click", function () { var n = root.getAttribute("data-theme") === "light" ? "dark" : "light"; applyTheme(n); save("tv-theme", n); paint(); });
      $("#menu").addEventListener("click", function (e) { var o = $("#nav").classList.toggle("open"); e.currentTarget.setAttribute("aria-expanded", o); });
      $("#sub").addEventListener("click", function (e) { e.preventDefault(); toast("The channel link is added when the site is built."); });
    }
    var foot = $("#foot");
    if (foot) {
      foot.innerHTML =
        '<footer class="site-footer"><div class="wrap"><div class="foot">' +
        '<div><a class="brand" href="index.html"><img src="assets/logo.jpg" alt="" width="38" height="38"><span>Tech<b>versation</b></span></a><p class="muted" style="margin-top:.9rem;max-width:34ch">Free video lectures and study notes for certification exams. Data, AI, insights, future.</p></div>' +
        "<div><h4>Certifications</h4><ul>" + courseList.map(function (c) { return '<li><a href="' + url("certification.html", { c: c.slug }) + '">' + c.short + "</a></li>"; }).join("") + "</ul></div>" +
        '<div><h4>Learn</h4><ul><li><a href="study-plan.html">Study plan</a></li><li><a href="search.html">Search</a></li><li><a href="index.html#request">Request a course</a></li></ul></div>' +
        '<div><h4>Techversation</h4><ul><li><a href="#">YouTube channel</a></li><li><a href="#">About</a></li><li><a href="#">Disclaimer</a></li><li><a href="#">Privacy</a></li></ul></div>' +
        '</div><p class="legal">Techversation is an independent learning site. It is not affiliated with, endorsed by or sponsored by PMI, Scrum Alliance, IAPP, The Linux Foundation, the CNCF, DAMA International or The Open Group. Their names are used only to say which exam a course prepares for, and all trademarks belong to their owners. Exam details change, so check the official site before you book.</p></div></footer>' +
        '<div class="toast" id="toast" role="status" aria-live="polite"></div>';
    }
  }

  /* ---------- shared renderers ---------- */
  function courseCard(c, opts) {
    opts = opts || {};
    var i = inst[c.institute];
    var haveNotes = !!TV.notes[c.slug];
    var done = getDone(c.slug).length, pct = done / c.modules.length;
    var thumb = c.hero || c.modules[opts.thumbIdx != null ? opts.thumbIdx : 0].img;
    var m = [c.modules.length + " modules", c.videos + " videos"]; if (c.minutes) m.push(dur(c.minutes));
    return '<a class="card ' + c.accent + (opts.wide ? " wide" : "") + '" href="' + url("certification.html", { c: c.slug }) + '">' +
      '<div class="thumb"><img src="' + thumb + '" alt="" loading="lazy"></div>' +
      '<div class="body"><div class="kicker">' + esc(i.name) + "</div><h3>" + esc(c.title) + '</h3><p class="desc">' + esc(c.desc) + "</p>" +
      '<div class="badges"><span class="badge accent">Video course</span>' + (haveNotes ? '<span class="badge">Study notes</span>' : '<span class="badge">Notes later</span>') + "</div>" +
      '<div class="meta">' + m.map(function (x) { return "<span>" + x + "</span>"; }).join("") + "</div>" +
      (opts.wide && c.slug === "csm" ? '<div class="resume">' + ring(pct, 34) + "<span>Example progress: " + done + " of " + c.modules.length + " modules done. Continue with Module " + c.modules[Math.min(done, c.modules.length - 1)].num + ".</span></div>" : "") +
      "</div></a>";
  }
  function soonCard(s) {
    return '<div class="card soon c-soon"><div class="thumb"><span>Coming soon</span></div><div class="body"><div class="kicker">' + esc(s.institute ? inst[s.institute].name : "Training") + "</div><h3>" + esc(s.short) + '</h3><p class="desc">' + esc(s.desc) + "</p></div></div>";
  }

  /* ---------- pages ---------- */
  var P = {};

  P.home = function () {
    var csm = courses.csm, kcna = courses.kcna, pmp = courses.pmp;
    $("#shots").innerHTML =
      '<div class="orb"></div><div class="ringline"></div>' +
      '<div class="shot s1"><img src="' + pmp.modules[7].img + '" alt=""></div>' +
      '<div class="shot s2"><img src="' + kcna.modules[2].img + '" alt=""></div>' +
      '<div class="shot s3"><img src="' + csm.modules[7].img + '" alt=""></div>';
    var mods = 0, vids = 0; courseList.forEach(function (c) { mods += c.modules.length; vids += c.videos; });
    $("#strip").innerHTML = "<span><b>" + courseList.length + "</b> courses</span><span><b>" + mods + "</b> modules</span><span><b>" + vids + "</b> video lectures</span><span><b>Free</b>, no sign-up</span><span>Study notes for <b>" + Object.keys(TV.notes).length + "</b> courses, more on the way</span>";
    $("#featured").innerHTML = courseCard(csm, { wide: true, thumbIdx: 7 }) + courseCard(courses.pmp, { thumbIdx: 7 }) + courseCard(courses.kcna, { thumbIdx: 2 }) + courseCard(courses.aigp) + courseCard(courses.cdmp);
    $("#institutes").innerHTML = TV.institutes.map(function (i) {
      var n = i.certs.length, soon = (i.soon || []).length;
      var c = n ? courses[i.certs[0]] : null;
      var label = n ? n + " certification" + (n > 1 ? "s" : "") + " · " + c.short : "Coming soon · " + TV.soon.filter(function (s) { return s.institute === i.id; }).map(function (s) { return s.short; }).join(", ");
      return '<a class="inst ' + (c ? c.accent : "c-soon") + '" href="' + (c ? url("certification.html", { c: c.slug }) : "#") + '"><span class="mono-tile">' + i.mono + "</span><span><b>" + esc(i.name) + "</b><small>" + esc(label) + "</small></span></a>";
    }).join("");
    $("#soon").innerHTML = TV.soon.filter(function (s) { return !s.institute; }).map(soonCard).join("");

    // institute -> certification picker
    var fi = $("#f-inst"), fc = $("#f-cert");
    fi.innerHTML = '<option value="">Choose an institute</option>' + TV.institutes.map(function (i) { return '<option value="' + i.id + '">' + esc(i.name) + "</option>"; }).join("");
    fi.addEventListener("change", function () {
      var i = inst[fi.value];
      if (!i) { fc.disabled = true; fc.innerHTML = '<option value="">Pick an institute first</option>'; return; }
      var opts = i.certs.map(function (s) { return '<option value="' + s + '">' + courses[s].short + " · " + esc(courses[s].name) + "</option>"; })
        .concat((i.soon || []).map(function (s) { return '<option value="" disabled>' + s.toUpperCase() + " · coming soon</option>"; }));
      fc.disabled = false; fc.innerHTML = opts.join("");
    });
    fc.innerHTML = '<option value="">Pick an institute first</option>';
    $("#f-go").addEventListener("click", function () {
      if (fc.value) location.href = url("certification.html", { c: fc.value }); else toast("Choose an institute and a certification first.");
    });
    $("#finder").addEventListener("submit", function (e) { e.preventDefault(); location.href = url("search.html", { q: $("#hero-q").value }); });
    $$(".chips .chip").forEach(function (b) { b.addEventListener("click", function () { location.href = url("search.html", { q: b.textContent }); }); });
    $("#req").addEventListener("submit", function (e) {
      e.preventDefault(); e.target.reset(); toast("Thanks. In the live site this goes to the channel owner's inbox.");
    });
  };

  P.cert = function () {
    var slug = qs.get("c") && courses[qs.get("c")] ? qs.get("c") : "csm";
    var c = courses[slug], i = inst[c.institute];
    document.body.classList.add(c.accent);
    document.title = c.title + " | Techversation";
    var done = getDone(slug);
    function paintHead() {
      done = getDone(slug);
      var next = c.modules.filter(function (m) { return done.indexOf(m.num) < 0; })[0] || c.modules[0];
      var pct = done.length / c.modules.length;
      $("#bar").style.width = (pct * 100).toFixed(0) + "%";
      $("#pcount").textContent = done.length + " of " + c.modules.length + " modules done";
      $("#go").href = url("module.html", { c: slug, m: next.num });
      $("#go").innerHTML = (done.length ? "Continue with Module " : "Start with Module ") + next.num + " " + I.arrow;
    }
    $("#crumbs").innerHTML = '<a href="index.html">Home</a><i>/</i><a href="index.html#certs">Certifications</a><i>/</i><a href="#">' + esc(i.name) + "</a><i>/</i><span>" + c.short + "</span>";
    $("#ey").textContent = i.full;
    $("#h1").textContent = c.title;
    $("#lede").textContent = c.desc;
    $("#badges").innerHTML = '<span class="badge accent">Free</span><span class="badge">' + c.modules.length + " modules</span><span class=\"badge\">" + c.videos + " videos</span>" + (c.minutes ? '<span class="badge">' + dur(c.minutes) + "</span>" : "") + (TV.notes[slug] ? '<span class="badge">Study notes</span>' : "");
    $("#yt").href = "https://www.youtube.com/playlist?list=" + c.playlist;
    var f = TV.facts[slug];
    $("#ticket").innerHTML = '<div class="ticket-top"><b>Exam facts</b><span class="badge accent">' + c.short + "</span></div>" +
      (f ? '<dl class="ticket-rows"><div><dt>Questions</dt><dd class="mono">' + f.questions + '</dd></div><div><dt>Time</dt><dd class="mono">' + f.time + '</dd></div><div><dt>Passing score</dt><dd class="mono">' + f.pass_ + '</dd></div><div><dt>Before the exam</dt><dd>' + esc(f.prereq) + '</dd></div><div><dt>Fee</dt><dd>' + esc(f.fee) + "</dd></div></dl>" +
        '<div class="ticket-foot">Source: ' + esc(f.source) + ". Each fact carries its source and the date it was checked; the date is added at launch. Always confirm on the official site.</div>"
        : '<dl class="ticket-rows"><div><dt>Questions</dt><dd class="mono">—</dd></div><div><dt>Time</dt><dd class="mono">—</dd></div><div><dt>Passing score</dt><dd class="mono">—</dd></div></dl><div class="ticket-foot">Exam facts for ' + c.short + " are added before launch, each with its official source and the date it was checked.</div>");

    // video tab
    function paintVideo() {
      done = getDone(slug);
      $("#p-video").innerHTML = '<div class="mods">' + c.modules.map(function (m) {
        var mins = modMinutes(m), isDone = done.indexOf(m.num) >= 0;
        var d = m.parts[0].title || (m.parts.length + " video part" + (m.parts.length > 1 ? "s" : ""));
        return '<a class="mod" href="' + url("module.html", { c: slug, m: m.num }) + '"><div class="t">' + (m.img ? '<img src="' + m.img + '" alt="" loading="lazy">' : '<span class="num">' + m.num + "</span>") + "</div>" +
          '<div><div class="n">Module ' + m.num + "</div><h3>" + esc(m.title) + "</h3><p>" + esc(d) + '</p><div class="meta" style="margin-top:.5rem"><span>' + m.parts.length + " part" + (m.parts.length > 1 ? "s" : "") + "</span>" + (mins ? "<span>" + mmss(mins) + "</span>" : "") + "</div></div>" +
          '<div class="st">' + (isDone ? '<span class="done-mark" title="Done">' + I.check + "</span>" : '<span class="todo-mark" title="Not done yet"></span>') + "</div></a>";
      }).join("") + "</div>";
    }
    // notes tab
    function paintNotes() {
      var n = TV.notes[slug];
      if (!n) { $("#p-notes").innerHTML = '<div class="empty"><b>Study notes for ' + c.short + " come later</b><span>The video course covers every topic in the meantime, and each video has a full transcript.</span></div>"; return; }
      var groups = {}, order = [];
      n.forEach(function (t) { if (!groups[t.group]) { groups[t.group] = []; order.push(t.group); } groups[t.group].push(t); });
      $("#p-notes").innerHTML = '<p class="note" style="margin-bottom:1.2rem">Every summary opens with the same at-a-glance block and the same section order. This list is the standard layout; the sample note is Topic 07.</p>' +
        order.map(function (g) {
          return '<div class="group-title">' + esc(g) + "</div>" + groups[g].map(function (t) {
            return '<a class="note-row" href="' + url("notes.html", { c: slug, t: t.num }) + '"><span class="tn">' + (slug === "cdmp" ? "Ch " : "Topic ") + t.num + "</span><div><h3>" + esc(t.title) + "</h3>" + (t.los.length ? '<div class="los">' + t.los.join(" · ") + "</div>" : "") + '</div><span class="rt">' + t.mins + " min read</span></a>";
          }).join("");
        }).join("");
    }
    // glossary tab
    function paintGloss() {
      var g = TV.glossary[slug];
      if (!g) { $("#p-gloss").innerHTML = '<div class="empty"><b>The ' + c.short + " glossary is added with the course</b><span>Each term links to the module that teaches it.</span></div>"; return; }
      $("#p-gloss").innerHTML = '<div class="search-box" style="max-width:460px;margin-bottom:1.1rem">' + I.search + '<input id="gq" type="search" placeholder="Filter ' + g.length + ' sample terms" aria-label="Filter glossary"></div><dl class="gloss" id="gl"></dl>';
      var draw = function (q) {
        $("#gl").innerHTML = g.filter(function (x) { return !q || (x[0] + " " + x[1]).toLowerCase().indexOf(q) >= 0; }).map(function (x) {
          return '<div class="gloss-item"><dt>' + esc(x[0]) + "</dt><dd>" + esc(x[1]) + '</dd><a href="' + url("module.html", { c: slug, m: x[2] }) + '">Module ' + x[2] + "</a></div>";
        }).join("") || '<div class="empty">No term matches.</div>';
      };
      draw(""); $("#gq").addEventListener("input", function (e) { draw(e.target.value.trim().toLowerCase()); });
    }
    function paintDl() {
      var haveDecks = true;
      $("#p-dl").innerHTML = '<div class="dl-list">' +
        '<div class="dl"><div class="ft">PPTX</div><div><b>Slide decks, all ' + c.modules.length + " modules</b><small>One deck per module, the same slides as the video.</small></div><span class=\"badge\">At launch</span></div>" +
        '<div class="dl"><div class="ft">PDF</div><div><b>Quick-reference sheet</b><small>The key facts of the course on a few printable pages.</small></div><span class="badge">At launch</span></div>' +
        (TV.glossary[slug] ? '<div class="dl"><div class="ft">PDF</div><div><b>Glossary</b><small>' + TV.glossary[slug].length + " sample terms here; the full list at launch.</small></div><span class=\"badge\">At launch</span></div>" : "") + "</div>";
    }
    function paintPlan() {
      var ok = c.minutes != null;
      $("#p-plan").innerHTML = '<div class="panel ring" style="max-width:640px"><h3>Plan the weeks until your exam</h3><p class="muted">Enter your exam date and the hours you have each week. You get a week-by-week schedule across the modules' + (TV.notes[slug] ? " and the study notes" : "") + ", with a review week at the end. It runs in your browser and nothing is stored on a server.</p><div class=\"actions\"><a class=\"btn btn-primary\" href=\"" + url("study-plan.html", { c: slug }) + '">' + (ok ? "Build my plan" : "Open the planner (sample)") + " " + I.arrow + "</a></div></div>";
    }
    paintHead(); paintVideo(); paintNotes(); paintGloss(); paintDl(); paintPlan();
    $$("#tabs .tab").forEach(function (t) { t.querySelector(".count") && (t.querySelector(".count").textContent = { video: c.modules.length, notes: TV.notes[slug] ? TV.notes[slug].length : "", gloss: TV.glossary[slug] ? TV.glossary[slug].length : "" }[t.dataset.tab] || ""); });
    function show(tab) {
      $$("#tabs .tab").forEach(function (t) { t.setAttribute("aria-selected", t.dataset.tab === tab); });
      $$(".tabpanel").forEach(function (p) { p.hidden = p.id !== "p-" + tab; });
    }
    $$("#tabs .tab").forEach(function (t) { t.addEventListener("click", function () { show(t.dataset.tab); history.replaceState(null, "", "#" + t.dataset.tab); }); });
    show(["video", "notes", "gloss", "dl", "plan"].indexOf(location.hash.slice(1)) >= 0 ? location.hash.slice(1) : "video");
  };

  P.module = function () {
    var slug = qs.get("c") && courses[qs.get("c")] ? qs.get("c") : "csm";
    var c = courses[slug], i = inst[c.institute];
    var num = qs.get("m") || (slug === "csm" ? "05" : "01");
    var idx = c.modules.map(function (m) { return m.num; }).indexOf(num); if (idx < 0) idx = 0;
    var m = c.modules[idx];
    document.body.classList.add(c.accent);
    document.title = "Module " + m.num + " " + m.title + " | " + c.short + " | Techversation";
    var partNo = Math.min(+(qs.get("p") || 1), m.parts.length);
    $("#crumbs").innerHTML = '<a href="index.html">Home</a><i>/</i><a href="' + url("certification.html", { c: slug }) + '">' + c.short + '</a><i>/</i><a href="' + url("certification.html", { c: slug }) + '#video">Video course</a><i>/</i><span>Module ' + m.num + "</span>";
    $("#ey").textContent = c.short + " · Module " + m.num;
    $("#h1").textContent = m.title;
    var tr = TV.transcripts[slug + "-" + m.num];

    function paintPlayer() {
      var p = m.parts[partNo - 1];
      $("#player").innerHTML = '<img src="' + (p.img || m.img || "assets/logo.jpg") + '" alt="Video thumbnail for ' + esc(m.title) + '"><a class="play" href="https://www.youtube.com/watch?v=' + p.id + '" target="_blank" rel="noopener" aria-label="Play the video on YouTube"><span class="pbtn">' + I.play + '</span></a><div class="cap"><span class="dur">' + (p.len || "") + "</span></div>";
      $("#pnote").textContent = "On the live site the player loads here when you press play (privacy-friendly YouTube embed). In this mockup it opens the video on YouTube.";
      $("#parts").innerHTML = m.parts.length > 1 ? m.parts.map(function (q) { return '<button class="part" type="button" role="tab" data-p="' + q.part + '" aria-selected="' + (q.part === partNo) + '"><b>Part ' + q.part + "</b><span>" + (q.len || "") + (q.title ? " · " + esc(q.title).slice(0, 34) + (q.title.length > 34 ? "…" : "") : "") + "</span></button>"; }).join("") : "";
      $$("#parts .part").forEach(function (b) { b.addEventListener("click", function () { partNo = +b.dataset.p; paintPlayer(); paintTabs(); }); });
    }
    function paintTabs() {
      var list = tr ? tr[String(partNo)] : null;
      $("#p-chap").innerHTML = list ? '<div class="chapters">' + list.map(function (s) { return '<div class="chap"><time>' + mmss(s.at) + "</time><span>" + esc(s.title) + "</span></div>"; }).join("") + '</div><p class="note" style="margin-top:.8rem">Chapters come from the slide titles. Timestamps are approximate in this mockup.</p>' : '<p class="muted">Chapters appear here, taken from the slide titles of the video.</p>';
      $("#p-tr").innerHTML = list ? '<div class="transcript">' + list.map(function (s) { return "<div><h4><time>" + mmss(s.at) + "</time>" + esc(s.title) + "</h4><p>" + esc(s.text) + "</p></div>"; }).join("") + "</div>" : '<p class="muted">The transcript is the narration script of this video, shown here in full. It helps search engines find the page and helps anyone who prefers reading. The mockup has the real transcript for CSM Module 05; open that module to see it.</p>';
    }
    $("#meta").innerHTML = "<span>" + m.parts.length + " part" + (m.parts.length > 1 ? "s" : "") + "</span>" + (modMinutes(m) ? "<span>" + mmss(modMinutes(m)) + " total</span>" : "") + "<span>Transcript</span><span>Slide deck</span>";
    paintPlayer(); paintTabs();

    // done toggle
    var btn = $("#done");
    function paintDone() { var d = getDone(slug).indexOf(m.num) >= 0; btn.setAttribute("aria-pressed", d); btn.innerHTML = d ? I.check + " Done" : "Mark as done"; btn.className = "btn " + (d ? "btn-primary" : "btn-ghost"); paintSide(); }
    btn.addEventListener("click", function () { var d = getDone(slug), k = d.indexOf(m.num); if (k >= 0) d.splice(k, 1); else d.push(m.num); setDone(slug, d); paintDone(); toast(k >= 0 ? "Marked as not done." : "Marked as done. Progress is saved in this browser."); });
    function paintSide() {
      var d = getDone(slug);
      $("#side-count").textContent = d.length + " / " + c.modules.length;
      $("#side-list").innerHTML = c.modules.map(function (x) { var on = d.indexOf(x.num) >= 0; return '<a class="side-item" href="' + url("module.html", { c: slug, m: x.num }) + '"' + (x.num === m.num ? ' aria-current="page"' : "") + '><span class="sn">' + x.num + "</span><span>" + esc(x.title) + '</span><span class="ck' + (on ? " on" : "") + '">' + (on ? I.check.replace('width="18" height="18"', 'width="11" height="11"') : "") + "</span></a>"; }).join("");
      var cur = $('#side-list [aria-current="page"]'); if (cur) $("#side-list").scrollTop = Math.max(0, cur.offsetTop - 120);
    }
    paintDone();

    // related notes + prev/next
    var hasNotes = TV.notes[slug] && TV.notes[slug].filter(function (t) { return t.num === m.num; })[0];
    $("#related").innerHTML = hasNotes ? '<a class="related" href="' + url("notes.html", { c: slug, t: m.num }) + '"><span class="ic">' + I.doc + '</span><span><b>Read the study notes for this topic</b><br><span class="muted">Topic ' + hasNotes.num + ": " + esc(hasNotes.title) + " · " + hasNotes.mins + ' min read</span></span><span style="margin-left:auto;color:var(--accent-ink)">' + I.arrow + "</span></a>" : "";
    var pv = c.modules[idx - 1], nx = c.modules[idx + 1];
    $("#pn").innerHTML = (pv ? '<a href="' + url("module.html", { c: slug, m: pv.num }) + '"><small>Previous</small><b>Module ' + pv.num + ": " + esc(pv.title) + "</b></a>" : "<span></span>") + (nx ? '<a class="next" href="' + url("module.html", { c: slug, m: nx.num }) + '"><small>Next</small><b>Module ' + nx.num + ": " + esc(nx.title) + "</b></a>" : "<span></span>");
    $("#yt-disc").href = "https://www.youtube.com/watch?v=" + m.parts[0].id;

    $$("#mtabs .tab").forEach(function (t) { t.addEventListener("click", function () { showM(t.dataset.tab); }); });
    function showM(tab) { $$("#mtabs .tab").forEach(function (t) { t.setAttribute("aria-selected", t.dataset.tab === tab); }); $$(".tabpanel").forEach(function (p) { p.hidden = p.id !== "p-" + tab; }); }
    showM("tr");
  };

  P.notes = function () {
    var slug = qs.get("c") || "csm"; document.body.classList.add(courses[slug] ? courses[slug].accent : "c-csm");
    var heads = $$(".prose h2"), links = $$(".toc a");
    $("#toc").innerHTML = heads.map(function (h) { return '<a href="#' + h.id + '">' + h.textContent.replace(/^\s*\d+\s*/, "") + "</a>"; }).join("");
    links = $$("#toc a");
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { links.forEach(function (a) { a.classList.toggle("on", a.getAttribute("href") === "#" + e.target.id); }); } }); }, { rootMargin: "-20% 0px -70% 0px" });
    heads.forEach(function (h) { io.observe(h); });
  };

  P.search = function () {
    var items = [];
    courseList.forEach(function (c) {
      items.push({ type: "Course", title: c.title, snippet: c.desc, c: c.slug, href: url("certification.html", { c: c.slug }), img: c.modules[0].img });
      c.modules.forEach(function (m) { items.push({ type: "Video module", title: "Module " + m.num + ": " + m.title, snippet: m.parts[0].title || (m.parts.length + " video part" + (m.parts.length > 1 ? "s" : "") + " with transcript"), c: c.slug, href: url("module.html", { c: c.slug, m: m.num }), img: m.img }); });
      (TV.notes[c.slug] || []).forEach(function (t) { items.push({ type: "Study note", title: (c.slug === "cdmp" ? "Chapter " : "Topic ") + t.num + ": " + t.title, snippet: t.group + (t.los.length ? " · " + t.los.join(", ") : "") + " · " + t.mins + " min read", c: c.slug, href: url("notes.html", { c: c.slug, t: t.num }), img: null }); });
      (TV.glossary[c.slug] || []).forEach(function (g) { items.push({ type: "Glossary", title: g[0], snippet: g[1], c: c.slug, href: url("module.html", { c: c.slug, m: g[2] }), img: null }); });
    });
    var types = ["Course", "Video module", "Study note", "Glossary"];
    var state = { q: (qs.get("q") || "sprint").trim(), inst: {}, type: {} };
    var q = $("#q"); q.value = state.q;
    $("#f-inst").innerHTML = TV.institutes.filter(function (i) { return i.certs.length; }).map(function (i) { return '<label class="check"><input type="checkbox" data-inst="' + i.id + '" checked> ' + esc(i.name) + "<em></em></label>"; }).join("");
    $("#f-type").innerHTML = types.map(function (t) { return '<label class="check"><input type="checkbox" data-type="' + t + '" checked> ' + t + "<em></em></label>"; }).join("");
    function hl(text, toks) { var s = esc(text); toks.forEach(function (t) { if (t) s = s.replace(new RegExp("(" + t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig"), "<mark>$1</mark>"); }); return s; }
    function run() {
      var toks = state.q.toLowerCase().split(/\s+/).filter(Boolean);
      var instOn = {}; $$("#f-inst input").forEach(function (b) { instOn[b.dataset.inst] = b.checked; });
      var typeOn = {}; $$("#f-type input").forEach(function (b) { typeOn[b.dataset.type] = b.checked; });
      var base = items.filter(function (it) { var hay = (it.title + " " + it.snippet).toLowerCase(); return toks.every(function (t) { return hay.indexOf(t) >= 0; }); });
      var shown = base.filter(function (it) { return instOn[courses[it.c].institute] && typeOn[it.type]; });
      shown.sort(function (a, b) { var s = function (it) { return (toks.some(function (t) { return it.title.toLowerCase().indexOf(t) >= 0; }) ? 2 : 0) + (it.type === "Course" ? 1 : 0); }; return s(b) - s(a); });
      $$("#f-inst label").forEach(function (l) { var id = l.querySelector("input").dataset.inst; l.querySelector("em").textContent = base.filter(function (it) { return courses[it.c].institute === id; }).length; });
      $$("#f-type label").forEach(function (l) { var t = l.querySelector("input").dataset.type; l.querySelector("em").textContent = base.filter(function (it) { return it.type === t; }).length; });
      $("#count").textContent = shown.length + " result" + (shown.length === 1 ? "" : "s") + (state.q ? ' for "' + state.q + '"' : "");
      $("#results").innerHTML = shown.slice(0, 40).map(function (it) {
        var c = courses[it.c];
        return '<a class="result ' + c.accent + '" href="' + it.href + '"><div class="rt">' + (it.img ? '<img src="' + it.img + '" alt="" loading="lazy">' : (it.type === "Glossary" ? I.chat : I.doc)) + '</div><div><div class="where"><span class="badge accent">' + it.type + "</span><span>" + esc(inst[c.institute].name) + " › " + c.short + "</span></div><h3>" + hl(it.title, toks) + "</h3><p>" + hl(it.snippet, toks) + "</p></div></a>";
      }).join("") || '<div class="empty"><b>No results</b><span>Try a shorter word, or clear a filter. You can also <a href="index.html#request">request a course</a>.</span></div>';
    }
    q.addEventListener("input", function () { state.q = q.value.trim(); run(); });
    $("#sform").addEventListener("submit", function (e) { e.preventDefault(); state.q = q.value.trim(); run(); });
    $$(".filters input").forEach(function (b) { b.addEventListener("change", run); });
    run();
  };

  P.plan = function () {
    var ok = courseList.filter(function (c) { return c.minutes != null; });
    var sel = $("#pc"); sel.innerHTML = ok.map(function (c) { return '<option value="' + c.slug + '">' + c.short + " · " + esc(c.name) + "</option>"; }).join("");
    if (qs.get("c") && courses[qs.get("c")] && courses[qs.get("c")].minutes != null) sel.value = qs.get("c");
    var d = new Date(); d.setHours(0, 0, 0, 0);
    var def = new Date(d.getTime() + 42 * 864e5);
    var iso = function (x) { return x.getFullYear() + "-" + String(x.getMonth() + 1).padStart(2, "0") + "-" + String(x.getDate()).padStart(2, "0"); };
    $("#pd").value = iso(def); $("#pd").min = iso(new Date(d.getTime() + 864e5));
    var fmt = function (x) { return x.toLocaleDateString("en-US", { month: "short", day: "numeric" }); };
    function plan() {
      var c = courses[sel.value], hrs = +$("#ph").value, withNotes = $("#pn").checked && !!TV.notes[c.slug];
      $("#ph-out").textContent = hrs + " h per week";
      var today = new Date(); today.setHours(0, 0, 0, 0);
      var exam = new Date($("#pd").value + "T00:00:00");
      var days = Math.max(1, Math.round((exam - today) / 864e5)), weeks = Math.max(1, Math.ceil(days / 7));
      var notesAvg = TV.notes[c.slug] ? TV.notes[c.slug].reduce(function (a, t) { return a + t.mins; }, 0) / c.modules.length : 0;
      var units = c.modules.map(function (m) {
        var notes = 0;
        var tn = (TV.notes[c.slug] || []).filter(function (t) { return t.num === m.num; })[0];
        if (withNotes) notes = tn ? tn.mins : (c.slug === "csm" ? 0 : Math.round(notesAvg));
        return { title: "Module " + m.num + ": " + m.title, mins: Math.round(modMinutes(m) / 60) + notes + 10, v: Math.round(modMinutes(m) / 60), n: notes };
      });
      var total = units.reduce(function (a, u) { return a + u.mins; }, 0);
      var studyWeeks = weeks > 1 ? weeks - 1 : 1, cap = hrs * 60, rows = [], k = 0;
      var per = Math.min(cap, total / studyWeeks);   // spread the work evenly instead of front-loading it
      for (var w = 0; w < studyWeeks; w++) {
        var used = 0, items = [], last = w === studyWeeks - 1;
        while (k < units.length && (items.length === 0 || (last ? used + units[k].mins <= cap : used + units[k].mins <= cap && used + units[k].mins / 2 <= per))) { items.push(units[k]); used += units[k].mins; k++; }
        rows.push({ w: w, items: items, used: used });
      }
      var left = units.slice(k), need = Math.ceil(total / studyWeeks / 6) / 10;
      var h = '';
      if (left.length) h += '<div class="alert"><b>This is tight.</b> At ' + hrs + " hours a week, " + left.length + " module" + (left.length > 1 ? "s do" : " does") + " not fit before the exam. You need about " + need + " hours a week, or a later exam date.</div>";
      h += '<div class="sum"><div><small>Total study time</small><b>' + (total / 60).toFixed(1) + ' h</b></div><div><small>Weeks to exam</small><b>' + weeks + '</b></div><div><small>Hours per week</small><b>' + hrs + ' h</b></div><div><small>Modules</small><b>' + c.modules.length + "</b></div></div><div class=\"weeks\">";
      rows.forEach(function (r) {
        var s = new Date(today.getTime() + r.w * 7 * 864e5), e = new Date(Math.min(s.getTime() + 6 * 864e5, exam.getTime()));
        h += '<div class="week"><div class="wk"><b>Week ' + (r.w + 1) + "</b><small>" + fmt(s) + " to " + fmt(e) + "</small></div><ul>" +
          (r.items.length ? r.items.map(function (u) { return "<li><span style=\"color:var(--fg-2);font-family:var(--font-body)\">" + esc(u.title) + "</span><span>" + (u.v ? u.v + " min video" : "") + (u.n ? " + " + u.n + " min notes" : "") + "</span></li>"; }).join("") : "<li>Buffer week: rewatch the modules you found hardest</li>") + '</ul><div class="hrs">' + (r.items.length ? (r.used / 60).toFixed(1) + " h" : "Buffer") + "</div></div>";
      });
      if (weeks > 1) {
        var s2 = new Date(today.getTime() + studyWeeks * 7 * 864e5);
        h += '<div class="week final"><div class="wk"><b>Final week</b><small>' + fmt(s2) + " to " + fmt(exam) + "</small></div><ul><li>Rewatch your weakest modules</li><li>Work through the quick-reference recap and the final check</li><li>Rest the day before the exam</li></ul><div class=\"hrs\">Review</div></div>";
      }
      h += "</div>";
      $("#plan-out").innerHTML = h;
      $("#plan-note").textContent = "Estimates use each video's real length, " + (withNotes ? "the reading time of each study note and " : "") + "10 minutes of review per module.";
    }
    $$(".plan-form input, .plan-form select").forEach(function (el) { el.addEventListener("input", plan); el.addEventListener("change", plan); });
    $("#print").addEventListener("click", function () { window.print(); });
    plan();
  };

  chrome();
  if (P[page]) P[page]();
})();
