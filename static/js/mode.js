/**
 * DRAW & GUESS (D&G) - Mode Selection Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  const cards = document.querySelectorAll(".mode-select-card");

  cards.forEach((card) => {
    const mode = card.getAttribute("data-mode");

    // 3D tilt interaction
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      
      const rotateX = (-y / (rect.height / 2)) * 6;
      const rotateY = (x / (rect.width / 2)) * 6;

      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-8px)`;
    });

    card.addEventListener("mouseleave", () => {
      card.style.transform = "";
    });

    // Clicking mode buttons saves selection
    const actionBtns = card.querySelectorAll("a");
    actionBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        if (mode) {
          localStorage.setItem("dng_selected_mode", mode);
        }
        if (window.soundManager) {
          window.soundManager.play("click");
        }
      });
    });
  });
});
