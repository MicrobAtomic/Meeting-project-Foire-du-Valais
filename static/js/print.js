// "Imprimer" buttons: <button type="button" data-print>. No inline handler (strict CSP).
document.addEventListener("click", function (event) {
  if (event.target.closest("[data-print]")) window.print();
});
