(function () {
  "use strict";

  const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;

  if (prefersReducedMotion) {
    document.documentElement.classList.add("reduced-motion");
    return;
  }

  document.documentElement.classList.add("motion-enabled");

  gsap.registerPlugin(ScrollTrigger);

  const lenis = new Lenis({
    duration: 1.1,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    smoothWheel: true,
  });

  lenis.on("scroll", ScrollTrigger.update);

  gsap.ticker.add((time) => {
    lenis.raf(time * 1000);
  });
  gsap.ticker.lagSmoothing(0);

  const heroTargets = [
    ".hero .wordmark",
    ".hero .hero__headline",
    ".hero .hero__support",
    ".hero .cta",
  ];

  gsap.set(heroTargets, { opacity: 0, y: 28 });

  gsap.to(heroTargets, {
    opacity: 1,
    y: 0,
    duration: 0.9,
    ease: "power3.out",
    stagger: 0.14,
    delay: 0.15,
  });

  const revealSections = document.querySelectorAll(".section .section__inner");

  revealSections.forEach((section) => {
    const children = section.children;

    gsap.set(children, { opacity: 0, y: 36 });

    gsap.to(children, {
      opacity: 1,
      y: 0,
      duration: 0.75,
      ease: "power2.out",
      stagger: 0.12,
      scrollTrigger: {
        trigger: section,
        start: "top 82%",
        once: true,
      },
    });
  });

  const demoSection = document.querySelector("#demo .section__inner");
  if (demoSection) {
    const pointer = document.createElement("div");
    pointer.className = "demo-pointer";
    pointer.setAttribute("aria-hidden", "true");
    pointer.innerHTML =
      '<span class="demo-pointer__line"></span><span class="demo-pointer__tip"></span>';
    demoSection.appendChild(pointer);

    gsap.set(pointer, { opacity: 0 });

    const line = pointer.querySelector(".demo-pointer__line");
    const tip = pointer.querySelector(".demo-pointer__tip");

    gsap.set(line, { scaleX: 0, transformOrigin: "left center" });
    gsap.set(tip, { opacity: 0, x: -8 });

    const pointingTimeline = gsap.timeline({
      scrollTrigger: {
        trigger: demoSection,
        start: "top 70%",
        once: true,
      },
      delay: 0.4,
    });

    pointingTimeline
      .to(pointer, { opacity: 1, duration: 0.2 })
      .to(line, { scaleX: 1, duration: 0.65, ease: "power2.inOut" }, 0)
      .to(tip, { opacity: 1, x: 0, duration: 0.35, ease: "power2.out" }, 0.45);
  }
})();
