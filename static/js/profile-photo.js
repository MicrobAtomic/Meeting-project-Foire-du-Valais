// The protected preview uses the same image decoder and crop as profile saving.
(function () {
  "use strict";
  var preview = document.querySelector("[data-photo-preview]");
  if (!preview || !window.fetch || !window.AbortController) return;
  var form = preview.closest("form");
  var input = form.querySelector('input[name="photo"]');
  var remove = form.querySelector('input[name="remove_photo"]');
  var image = preview.querySelector("[data-photo-image]");
  var placeholder = preview.querySelector("[data-photo-placeholder]");
  var status = preview.querySelector("[data-photo-status]");
  var save = form.querySelector("[data-photo-save]");
  var original = image.getAttribute("src") || "";
  var sequence = 0;
  var controller = null;
  var busy = false;

  function show(source) {
    image.hidden = !source;
    placeholder.hidden = Boolean(source);
    if (source) image.src = source;
    else image.removeAttribute("src");
  }

  function message(text, error) {
    status.textContent = text;
    status.classList.toggle("text-red-700", Boolean(error));
    status.classList.toggle("text-stone-600", !error);
  }

  function processing(value) {
    busy = value;
    preview.setAttribute("aria-busy", String(value));
    if (save) save.disabled = value;
  }

  function reset() {
    sequence += 1;
    if (controller) controller.abort();
    input.setCustomValidity("");
    input.removeAttribute("aria-invalid");
    processing(false);
  }

  function asDataUrl(blob) {
    return new Promise(function (resolve, reject) {
      var reader = new FileReader();
      reader.onload = function () { resolve(reader.result); };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  input.addEventListener("change", async function () {
    reset();
    show(original);
    message("");
    var file = input.files[0];
    if (!file) return;
    if (remove) remove.checked = false;
    if (file.size > 20 * 1024 * 1024) {
      input.setCustomValidity(preview.dataset.tooLarge);
      input.setAttribute("aria-invalid", "true");
      message(preview.dataset.tooLarge, true);
      return;
    }
    var current = sequence;
    controller = new AbortController();
    var body = new FormData();
    body.append("photo", file);
    processing(true);
    message(preview.dataset.loading);
    try {
      var response = await fetch(preview.dataset.previewUrl, {
        method: "POST", body: body, credentials: "same-origin", cache: "no-store",
        headers: { "X-CSRFToken": form.querySelector('input[name="csrfmiddlewaretoken"]').value },
        signal: controller.signal
      });
      if (current !== sequence) return;
      if (response.status === 400) {
        var invalid = await response.json();
        if (current !== sequence) return;
        input.setCustomValidity(invalid.error);
        input.setAttribute("aria-invalid", "true");
        message(invalid.error, true);
        return;
      }
      if (!response.ok || response.redirected || response.headers.get("Content-Type") !== "image/jpeg") {
        throw new Error("Preview unavailable");
      }
      var source = await asDataUrl(await response.blob());
      if (current !== sequence) return;
      show(source);
      message(preview.dataset.ready);
    } catch (error) {
      if (current === sequence && error.name !== "AbortError") message(preview.dataset.failed, true);
    } finally {
      if (current === sequence) processing(false);
    }
  });

  if (remove) remove.addEventListener("change", function () {
    reset();
    input.value = "";
    show(remove.checked ? preview.dataset.fallbackSrc : original);
    message(remove.checked ? preview.dataset.removed : "");
  });

  form.addEventListener("submit", function (event) {
    if (busy) {
      event.preventDefault();
      message(preview.dataset.loading);
    }
  });
})();
