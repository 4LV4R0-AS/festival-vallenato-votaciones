// Menú desplegable para pantallas pequeñas.
(function () {
  var boton = document.querySelector(".menu-boton");
  var menu = document.getElementById("menu-principal");
  if (!boton || !menu) return;
  boton.addEventListener("click", function () {
    var abierto = menu.classList.toggle("menu-abierto");
    boton.setAttribute("aria-expanded", abierto ? "true" : "false");
  });
})();
