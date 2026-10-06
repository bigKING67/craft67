(() => {
  const variants = new Set(["baseline", "reference-assisted"]);
  const states = new Set(["default", "loading", "empty", "error", "success", "long"]);
  const query = new URLSearchParams(window.location.search);
  const requestedVariant = query.get("variant");
  const requestedState = query.get("state");
  const variant = variants.has(requestedVariant) ? requestedVariant : "baseline";
  let currentState = states.has(requestedState) ? requestedState : "default";

  document.documentElement.classList.add("js");
  document.documentElement.dataset.variant = variant;

  const stateModels = {
    default: {
      posture: "Ready with 3 open calls",
      postureStatus: ["!", "Open", "open"],
      banner: "Demonstration dossier loaded from four bounded evidence dimensions.",
      metrics: ["14 / 14", "37 / 40", "3", "18 min"],
      source: "Controlled demonstration data / no customer or production claim",
      busy: false,
      recovery: false,
    },
    loading: {
      posture: "Refreshing attributable evidence",
      postureStatus: ["...", "Loading", "neutral"],
      banner: "Refreshing evidence sources. Existing values are temporarily withheld.",
      metrics: ["Pending", "Pending", "Pending", "Pending"],
      source: "Evidence refresh in progress / no new result claimed",
      busy: true,
      recovery: false,
    },
    empty: {
      posture: "No evidence package attached",
      postureStatus: ["-", "Empty", "neutral"],
      banner: "No evidence package is attached. No metrics have been invented.",
      metrics: ["None", "None", "None", "None"],
      source: "Empty demonstration state / attach a bounded source before deciding",
      busy: false,
      recovery: false,
    },
    error: {
      posture: "Source refresh needs attention",
      postureStatus: ["!", "Error", "open"],
      banner: "The evidence source did not respond. Retry without discarding the last context.",
      metrics: ["14 / 14", "37 / 40", "3", "18 min"],
      source: "Last observed demonstration packet / refresh failed",
      busy: false,
      recovery: true,
    },
    success: {
      posture: "Decision packet approved",
      postureStatus: ["+", "Approved", "verified"],
      banner: "The demonstration packet is approved. Its three exception records remain visible.",
      metrics: ["14 / 14", "40 / 40", "0", "4 min"],
      source: "Approved demonstration packet / not a production certification",
      busy: false,
      recovery: false,
    },
    long: {
      posture: "Ready with a deliberately long exception review label",
      postureStatus: ["!", "Open", "open"],
      banner: "Long-label test: attributable evidence remains readable without truncation or overflow.",
      metrics: ["14 / 14", "37 / 40", "3", "18 min"],
      source: "Controlled long-content fixture / source attribution must remain fully readable",
      busy: false,
      recovery: false,
    },
  };

  const defaultRows = {
    coverage: {
      title: "Coverage map",
      source: "Release manifest / observed 18 minutes ago",
      result: "14 of 14 services",
      status: ["+", "Ready", "verified"],
    },
    impact: {
      title: "Change impact",
      source: "Release diff / owner confirmed",
      result: "3 changes / 2 customer workflows",
      status: ["+", "Verified", "verified"],
    },
    exceptions: {
      title: "Exception ownership",
      source: "Decision log / due 21 August",
      result: "3 open / 2 owners confirmed",
      status: ["!", "Decide", "open"],
    },
  };

  const longRows = {
    coverage: {
      title: "Customer-facing identity and authorization boundary coverage map",
      source: "Release manifest / entitlement service inventory / observed 18 minutes ago",
      result: "14 of 14 customer-facing and internal dependency services",
      status: ["+", "Ready", "verified"],
    },
    impact: {
      title: "Cross-workflow change impact and recovery ownership",
      source: "Release diff / account recovery and organization provisioning owners confirmed",
      result: "3 release changes across 2 customer-critical workflows",
      status: ["+", "Verified", "verified"],
    },
    exceptions: {
      title: "Unresolved exception ownership and time-bound decision record",
      source: "Decision log / final infrastructure and product review due 21 August",
      result: "3 open exceptions / 2 named owners / 1 decision pending",
      status: ["!", "Decide", "open"],
    },
  };

  const metricKeys = ["scope", "controls", "exceptions", "freshness"];
  const ledger = document.querySelector("[data-ledger]");
  const recovery = document.querySelector("[data-recovery]");
  const stateBanner = document.querySelector("[data-state-banner]");

  const setStatus = (element, [symbol, label, kind]) => {
    element.className = `status-mark status-mark--${kind}`;
    element.innerHTML = `<span aria-hidden="true">${symbol}</span>${label}`;
  };

  const applyState = (state) => {
    const model = stateModels[state];
    const rows = state === "long" ? longRows : defaultRows;
    currentState = state;
    document.documentElement.dataset.state = state;
    document.querySelector("[data-posture]").textContent = model.posture;
    setStatus(document.querySelector("[data-posture-status]"), model.postureStatus);
    stateBanner.textContent = model.banner;
    metricKeys.forEach((key, index) => {
      document.querySelector(`[data-metric="${key}"]`).textContent = model.metrics[index];
    });
    document.querySelector("[data-source-note]").textContent = model.source;
    ledger.setAttribute("aria-busy", String(model.busy));
    recovery.hidden = !model.recovery;

    Object.entries(rows).forEach(([key, row]) => {
      const element = document.querySelector(`[data-row="${key}"]`);
      element.querySelector("[data-row-title]").textContent = row.title;
      element.querySelector("[data-row-source]").textContent = row.source;
      element.querySelector("[data-row-result]").textContent = row.result;
      setStatus(element.querySelector("[data-row-status]"), row.status);
    });

    window.__CAIRN_METRICS__ = collectMetrics();
  };

  const dialog = document.querySelector(".dossier-dialog");
  const dialogClose = dialog.querySelector("[data-dialog-close]");
  let dossierTrigger = null;

  document.querySelectorAll("[data-open-dossier]").forEach((trigger) => {
    trigger.addEventListener("click", () => {
      dossierTrigger = trigger;
      dialog.showModal();
      window.requestAnimationFrame(() => dialogClose.focus({ preventScroll: true }));
    });
  });

  const restoreDossierFocus = () => dossierTrigger?.focus({ preventScroll: true });

  dialog.querySelectorAll('[value="close"]').forEach((control) => {
    control.addEventListener("click", (event) => {
      event.preventDefault();
      dialog.close(control.value);
      restoreDossierFocus();
    });
  });

  dialog.addEventListener("cancel", () => window.setTimeout(restoreDossierFocus, 0));

  document.querySelector("[data-retry]").addEventListener("click", () => {
    applyState("loading");
    window.setTimeout(() => {
      applyState("default");
      stateBanner.textContent = "Evidence refresh restored the controlled demonstration packet.";
    }, 180);
  });

  const pilotButton = document.querySelector("[data-request-pilot]");
  const pilotStatus = document.querySelector("[data-pilot-status]");
  pilotButton.addEventListener("click", () => {
    pilotButton.disabled = true;
    pilotButton.textContent = "Pilot request staged";
    pilotStatus.textContent =
      "Local demonstration acknowledged. No account, upload, or message was created.";
  });

  const reveals = document.querySelectorAll(".reveal");
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    reveals.forEach((element) => element.classList.add("is-visible"));
  } else if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.08 },
    );
    reveals.forEach((element) => observer.observe(element));
  } else {
    reveals.forEach((element) => element.classList.add("is-visible"));
  }

  let cumulativeLayoutShift = 0;
  let largestContentfulPaint = null;
  const longTasks = [];

  if ("PerformanceObserver" in window) {
    try {
      new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          if (!entry.hadRecentInput) cumulativeLayoutShift += entry.value;
        });
      }).observe({ type: "layout-shift", buffered: true });
    } catch (_error) {
      cumulativeLayoutShift = null;
    }
    try {
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        largestContentfulPaint = entries.at(-1)?.startTime ?? largestContentfulPaint;
      }).observe({ type: "largest-contentful-paint", buffered: true });
    } catch (_error) {
      largestContentfulPaint = null;
    }
    try {
      new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => longTasks.push(entry.duration));
      }).observe({ type: "longtask", buffered: true });
    } catch (_error) {
      longTasks.length = 0;
    }
  }

  function collectMetrics() {
    const root = document.documentElement;
    const navigation = performance.getEntriesByType("navigation")[0];
    const resources = performance.getEntriesByType("resource");
    const paints = Object.fromEntries(
      performance.getEntriesByType("paint").map((entry) => [entry.name, entry.startTime]),
    );
    const rect = (selector) => {
      const element = document.querySelector(selector);
      if (!element) return { found: false };
      const box = element.getBoundingClientRect();
      return {
        found: true,
        rect: {
          x: box.x,
          y: box.y,
          width: box.width,
          height: box.height,
          bottom: box.bottom,
        },
      };
    };

    return {
      variant,
      state: currentState,
      viewport: { width: window.innerWidth, height: window.innerHeight, dpr: window.devicePixelRatio },
      document: {
        scrollWidth: root.scrollWidth,
        scrollHeight: root.scrollHeight,
        horizontalOverflow: root.scrollWidth > window.innerWidth,
        nodeCount: document.querySelectorAll("*").length,
      },
      semantics: {
        h1Count: document.querySelectorAll("h1").length,
        mainCount: document.querySelectorAll("main").length,
        dialogCount: document.querySelectorAll("dialog").length,
        detailsCount: document.querySelectorAll("details").length,
      },
      layout: {
        headline: rect("#hero-title"),
        posture: rect(".hero-proof__heading"),
        proof: rect(".hero-proof"),
        support: rect(".hero__support"),
        primaryAction: rect("[data-open-dossier]"),
      },
      performance: {
        domContentLoaded: navigation?.domContentLoadedEventEnd ?? null,
        load: navigation?.loadEventEnd ?? null,
        firstContentfulPaint: paints["first-contentful-paint"] ?? null,
        largestContentfulPaint,
        cumulativeLayoutShift,
        resourceCount: resources.length,
        transferBytes: resources.reduce((total, entry) => total + (entry.transferSize || 0), 0),
        longTaskCount: longTasks.length,
        longestTask: longTasks.length ? Math.max(...longTasks) : 0,
      },
    };
  }

  window.__CAIRN_A11Y_AUDIT__ = () => {
    const duplicateIds = [...document.querySelectorAll("[id]")]
      .map((element) => element.id)
      .filter((id, index, all) => all.indexOf(id) !== index);
    const unnamedControls = [...document.querySelectorAll("a[href], button, summary")]
      .filter((element) => !(element.getAttribute("aria-label") || element.textContent.trim()))
      .map((element) => element.outerHTML.slice(0, 120));
    const focusTargets = [...document.querySelectorAll("a[href], button:not([disabled]), summary")]
      .map((element) => ({ element, box: element.getBoundingClientRect() }))
      .filter(({ element, box }) => {
        const style = window.getComputedStyle(element);
        return box.width > 0 && box.height > 0 && style.visibility !== "hidden";
      })
      .map(({ element, box }) => {
        return {
          text: (element.getAttribute("aria-label") || element.textContent).trim().slice(0, 80),
          width: box.width,
          height: box.height,
        };
      });
    return {
      duplicateIds,
      unnamedControls,
      h1Count: document.querySelectorAll("h1").length,
      landmarks: {
        header: document.querySelectorAll("header.site-header").length,
        nav: document.querySelectorAll("nav").length,
        main: document.querySelectorAll("main").length,
        footer: document.querySelectorAll("body > footer").length,
      },
      dialog: {
        native: dialog instanceof HTMLDialogElement,
        labelledBy: dialog.getAttribute("aria-labelledby"),
        closeName: dialogClose.getAttribute("aria-label"),
      },
      liveRegions: document.querySelectorAll('[aria-live="polite"]').length,
      focusTargets,
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
    };
  };

  applyState(currentState);
  window.addEventListener("load", () => {
    window.requestAnimationFrame(() => {
      window.__CAIRN_METRICS__ = collectMetrics();
    });
  });
  window.addEventListener("resize", () => {
    window.__CAIRN_METRICS__ = collectMetrics();
  });
})();
