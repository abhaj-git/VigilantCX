const menuButton = document.querySelector("[data-menu-toggle]");
const mobileMenu = document.querySelector("[data-mobile-menu]");

if (menuButton && mobileMenu) {
  menuButton.addEventListener("click", () => {
    const isOpen = menuButton.getAttribute("aria-expanded") === "true";
    menuButton.setAttribute("aria-expanded", String(!isOpen));
    mobileMenu.hidden = isOpen;
  });
}

document.querySelectorAll("[data-gallery]").forEach((gallery) => {
  const slides = [...gallery.querySelectorAll("[data-gallery-slide]")];
  const thumbnails = [...gallery.querySelectorAll("[data-gallery-thumb]")];
  const currentLabel = gallery.querySelector("[data-gallery-current]");
  const viewport = gallery.querySelector(".product-gallery-viewport");
  let currentIndex = 0;
  let touchStartX = 0;

  if (slides.length < 2) return;

  const showSlide = (requestedIndex) => {
    currentIndex = (requestedIndex + slides.length) % slides.length;

    slides.forEach((slide, index) => {
      slide.hidden = index !== currentIndex;
    });

    thumbnails.forEach((thumbnail, index) => {
      const isActive = index === currentIndex;
      thumbnail.classList.toggle("is-active", isActive);
      thumbnail.setAttribute("aria-selected", String(isActive));
    });

    currentLabel.textContent = String(currentIndex + 1);
  };

  gallery.querySelector("[data-gallery-prev]")?.addEventListener("click", () => {
    showSlide(currentIndex - 1);
  });

  gallery.querySelector("[data-gallery-next]")?.addEventListener("click", () => {
    showSlide(currentIndex + 1);
  });

  thumbnails.forEach((thumbnail) => {
    thumbnail.addEventListener("click", () => {
      showSlide(Number(thumbnail.dataset.index));
    });
  });

  viewport?.addEventListener("touchstart", (event) => {
    touchStartX = event.changedTouches[0].clientX;
  }, { passive: true });

  viewport?.addEventListener("touchend", (event) => {
    const distance = event.changedTouches[0].clientX - touchStartX;
    if (Math.abs(distance) < 45) return;
    showSlide(currentIndex + (distance < 0 ? 1 : -1));
  }, { passive: true });
});
