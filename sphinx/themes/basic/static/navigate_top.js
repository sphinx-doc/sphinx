/* Add Navigate to Top Functionality */
// inspired from https://github.com/pradyunsg/furo

"use strict";

// fetch the pixels scrolled vertically from origin
var lastScrollTop = document.documentElement.scrollTop;
const GO_TO_TOP_OFFSET = 64;

const _scrollToTop = (positionY) => {
  const navigateToTopButtom = document.getElementById("navigate-to-top");
  // position not yet crossed of offset
  if (positionY < GO_TO_TOP_OFFSET) {
    navigateToTopButtom.classList.add("hide-navigate-to-top");
    navigateToTopButtom.classList.remove("show-navigate-to-top");
  } else {
    if (positionY > lastScrollTop) {
      // scrolling down
      navigateToTopButtom.classList.add("hide-navigate-to-top");
      navigateToTopButtom.classList.remove("show-navigate-to-top");
    } else if (positionY < lastScrollTop) {
      // scrolling up
      navigateToTopButtom.classList.add("show-navigate-to-top");
      navigateToTopButtom.classList.remove("hide-navigate-to-top");
    }
  }
  // update the position for next scroll event
  lastScrollTop = positionY;
};

const _setupScrollHandler = () => {
  let lastKnownScrollPosition = 0;
  // help to keep track if requestAnimationFrame is scheduled
  let ticking = false;

  document.addEventListener("scroll", (event) => {
    lastKnownScrollPosition = window.scrollY;

    if (!ticking) {
      window.requestAnimationFrame(() => {
        _scrollToTop(lastKnownScrollPosition)
        // animation is complete (so now be called again)
        ticking = false;
      });

      // it's scheduled so don't call back the requestAnimationFrame
      ticking = true;
    }
  });
};

document.addEventListener("DOMContentLoaded", _setupScrollHandler);
