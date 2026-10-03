// Onboarding "swipe tes affinités". Progressive enhancement: without JS the form
// stays a plain list of radio buttons that works on its own.
(function () {
  "use strict";
  var form = document.getElementById("swipe-form");
  if (!form) return;

  var cards = Array.prototype.slice.call(form.querySelectorAll(".swipe-card"));
  var controls = document.getElementById("swipe-controls");
  var progress = document.getElementById("swipe-progress");
  var THRESHOLD = 80;
  var index = 0;
  var drag = null;

  form.classList.add("js-swipe");
  if (controls) controls.hidden = false;

  function render() {
    cards.forEach(function (card, i) {
      card.hidden = i !== index;
    });
    if (progress) progress.textContent = Math.min(index + 1, cards.length) + " / " + cards.length;
    if (index >= cards.length) form.submit();
  }

  function answer(value) {
    var card = cards[index];
    if (!card) return;
    var input = card.querySelector('input[value="' + value + '"]');
    if (input) input.checked = true;
    card.style.transform = "";
    card.classList.add("swipe-out-" + value);
    window.setTimeout(function () {
      index += 1;
      render();
    }, 200);
  }

  if (controls) {
    controls.addEventListener("click", function (event) {
      var button = event.target.closest("[data-answer]");
      if (button) answer(button.dataset.answer);
    });
  }

  form.addEventListener("pointerdown", function (event) {
    var card = cards[index];
    if (!card || !card.contains(event.target)) return;
    drag = { x: event.clientX, y: event.clientY, card: card };
    card.classList.add("is-dragging");
    card.setPointerCapture(event.pointerId);
  });

  form.addEventListener("pointermove", function (event) {
    if (!drag) return;
    var dx = event.clientX - drag.x;
    drag.card.style.transform = "translateX(" + dx + "px) rotate(" + dx / 20 + "deg)";
  });

  function endDrag(event) {
    if (!drag) return;
    var dx = event.clientX - drag.x;
    var dy = event.clientY - drag.y;
    var card = drag.card;
    drag = null;
    card.classList.remove("is-dragging");
    if (event.type === "pointerup" && dx > THRESHOLD) answer("like");
    else if (event.type === "pointerup" && dx < -THRESHOLD) answer("dislike");
    else if (event.type === "pointerup" && dy > THRESHOLD) answer("neutral");
    else card.style.transform = "";
  }
  form.addEventListener("pointerup", endDrag);
  form.addEventListener("pointercancel", endDrag);

  document.addEventListener("keydown", function (event) {
    if (event.key === "ArrowRight") answer("like");
    else if (event.key === "ArrowLeft") answer("dislike");
    else if (event.key === "ArrowDown") answer("neutral");
  });

  render();
})();
