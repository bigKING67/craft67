(() => {
  const allowedVariants = new Set(["baseline", "reference-assisted"]);
  const requestedVariant = new URLSearchParams(window.location.search).get("variant");
  const variant = allowedVariants.has(requestedVariant) ? requestedVariant : "baseline";

  document.documentElement.dataset.variant = variant;

  const dialog = document.querySelector(".report-dialog");
  let reportTrigger = null;

  document.querySelectorAll("[data-open-report]").forEach((trigger) => {
    trigger.addEventListener("click", () => {
      reportTrigger = trigger;
      dialog.showModal();
    });
  });

  const restoreReportFocus = () => {
    window.setTimeout(() => reportTrigger?.focus({ preventScroll: true }), 50);
  };

  dialog.querySelector("form").addEventListener("submit", restoreReportFocus);
  dialog.addEventListener("cancel", restoreReportFocus);
  dialog.addEventListener("close", restoreReportFocus);

  const startButton = document.querySelector("[data-start-review]");
  const startStatus = document.querySelector("[data-start-status]");

  startButton.addEventListener("click", () => {
    startButton.disabled = true;
    startButton.textContent = "RC-18 review started";
    startStatus.textContent =
      "Local sample started. No data was uploaded and no account was created.";
  });

  const reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.12 },
    );
    reveals.forEach((element) => observer.observe(element));
  } else {
    reveals.forEach((element) => element.classList.add("is-visible"));
  }

  const collectMetrics = () => ({
    variant,
    viewport: { width: window.innerWidth, height: window.innerHeight },
    document: {
      scrollWidth: document.documentElement.scrollWidth,
      scrollHeight: document.documentElement.scrollHeight,
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
    },
    semantics: {
      h1Count: document.querySelectorAll("h1").length,
      dialogCount: document.querySelectorAll("dialog").length,
      primaryActionCount: document.querySelectorAll(".button--primary").length,
    },
  });

  window.__REVIEWLANE_METRICS__ = collectMetrics();
  window.addEventListener("resize", () => {
    window.__REVIEWLANE_METRICS__ = collectMetrics();
  });
})();
