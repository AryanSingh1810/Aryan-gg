/**
 * DRAW & GUESS - Home Page Interactive Scripts
 * Mobile Navigation Drawer • Card Physics • Sound Integration
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Mobile Navigation Drawer Toggle
  const mobileToggleBtn = document.getElementById("mobileMenuToggle");
  const mobileDrawer = document.getElementById("mobileNavDrawer");
  const mobileBackdrop = document.getElementById("mobileNavBackdrop");
  const mobileCloseBtn = document.getElementById("mobileDrawerClose");

  const openDrawer = () => {
    if (!mobileDrawer || !mobileBackdrop) return;
    mobileDrawer.classList.add("open");
    mobileBackdrop.classList.add("open");
    mobileDrawer.setAttribute("aria-hidden", "false");
    if (mobileToggleBtn) {
      mobileToggleBtn.classList.add("active");
      mobileToggleBtn.setAttribute("aria-expanded", "true");
    }
    document.body.style.overflow = "hidden";
  };

  const closeDrawer = () => {
    if (!mobileDrawer || !mobileBackdrop) return;
    mobileDrawer.classList.remove("open");
    mobileBackdrop.classList.remove("open");
    mobileDrawer.setAttribute("aria-hidden", "true");
    if (mobileToggleBtn) {
      mobileToggleBtn.classList.remove("active");
      mobileToggleBtn.setAttribute("aria-expanded", "false");
    }
    document.body.style.overflow = "";
  };

  if (mobileToggleBtn) {
    mobileToggleBtn.addEventListener("click", () => {
      const isOpen = mobileDrawer && mobileDrawer.classList.contains("open");
      if (isOpen) {
        closeDrawer();
      } else {
        openDrawer();
      }
    });
  }

  if (mobileCloseBtn) {
    mobileCloseBtn.addEventListener("click", closeDrawer);
  }

  if (mobileBackdrop) {
    mobileBackdrop.addEventListener("click", closeDrawer);
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && mobileDrawer && mobileDrawer.classList.contains("open")) {
      closeDrawer();
    }
  });

  // 2. Hanging Polaroid Cards Interaction & Navigation
  const songCard = document.getElementById("songHangingCard");
  const movieCard = document.getElementById("movieHangingCard");

  if (songCard) {
    songCard.addEventListener("click", () => {
      if (window.soundEngine) window.soundEngine.playTone(587.33, 0.15, "sine", 0.18);
      window.location.href = "/create-room?mode=song";
    });
  }

  if (movieCard) {
    movieCard.addEventListener("click", () => {
      if (window.soundEngine) window.soundEngine.playTone(659.25, 0.15, "triangle", 0.18);
      window.location.href = "/create-room?mode=movie";
    });
  }

  // 3. Mode Action Button Sound Feedback
  const songBtn = document.getElementById("heroSongBtn");
  const movieBtn = document.getElementById("heroMovieBtn");

  if (songBtn) {
    songBtn.addEventListener("click", () => {
      localStorage.setItem("dng_selected_mode", "song");
      if (window.soundEngine) window.soundEngine.playTone(523.25, 0.18, "sine", 0.2);
    });
  }

  if (movieBtn) {
    movieBtn.addEventListener("click", () => {
      localStorage.setItem("dng_selected_mode", "movie");
      if (window.soundEngine) window.soundEngine.playTone(659.25, 0.18, "triangle", 0.2);
    });
  }

  // Secondary buttons click sounds
  const secondaryBtns = [
    document.getElementById("heroCreateRoomBtn"),
    document.getElementById("heroJoinRoomBtn"),
    document.getElementById("heroExploreModesBtn")
  ];

  secondaryBtns.forEach((btn) => {
    if (btn) {
      btn.addEventListener("click", () => {
        if (window.soundEngine) window.soundEngine.playTone(440, 0.1, "sine", 0.12);
      });
    }
  });

  // 4. 3D Card Tilt on Hover for Showcase Cards
  const modeCards = document.querySelectorAll(".mode-card");

  modeCards.forEach((card) => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      
      const rotateX = (-y / (rect.height / 2)) * 4;
      const rotateY = (x / (rect.width / 2)) * 4;

      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-8px)`;
    });

    card.addEventListener("mouseleave", () => {
      card.style.transform = "";
    });
  });
});

