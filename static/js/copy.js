// "Copier" / "Partager" buttons of the invitation page. No inline handler (strict CSP).
//   <button type="button" data-copy="#invite-link" data-copied="Copié ✅">Copier</button>
//   <button type="button" data-share="#invite-link" data-share-title="…" hidden>Partager</button>  (shown if supported)
(function () {
  "use strict";

  function flash(button, label) {
    var original = button.textContent;
    button.textContent = label;
    window.setTimeout(function () {
      button.textContent = original;
    }, 2000);
  }

  function legacyCopy(input) {
    input.focus();
    input.select();
    try {
      return document.execCommand("copy");
    } catch (error) {
      return false;
    }
  }

  document.addEventListener("click", function (event) {
    var copyButton = event.target.closest("[data-copy]");
    if (copyButton) {
      var input = document.querySelector(copyButton.getAttribute("data-copy"));
      if (!input) return;
      var done = function () {
        flash(copyButton, copyButton.getAttribute("data-copied") || "OK");
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(input.value).then(done, function () {
          if (legacyCopy(input)) done();
        });
      } else if (legacyCopy(input)) {
        done();
      }
      return;
    }
    var shareButton = event.target.closest("[data-share]");
    if (shareButton && navigator.share) {
      var source = document.querySelector(shareButton.getAttribute("data-share"));
      if (source) {
        navigator.share({ title: shareButton.getAttribute("data-share-title") || "", url: source.value }).catch(function () {});
      }
    }
  });

  var shareButtons = document.querySelectorAll("[data-share]");
  if (navigator.share) {
    Array.prototype.forEach.call(shareButtons, function (button) {
      button.hidden = false;
    });
  }
})();
