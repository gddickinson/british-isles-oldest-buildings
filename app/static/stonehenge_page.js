// Page /stonehenge: loads the 3D model (stonehenge_view.js) when the browser can draw WebGL, else says why not.
const gl = (() => { try { return document.createElement("canvas").getContext("webgl2"); } catch (e) { return null; } })();
if (gl) {
  import("./stonehenge_view.js");
} else {
  const msg = document.createElement("p");
  msg.className = "sh-nogl";
  msg.textContent = "The 3D model needs WebGL, which this browser has switched off or does not have.";
  document.querySelector("#sh_canvas").replaceWith(msg);
  document.querySelectorAll(".sh-panel, .sh-bar").forEach((el) => { el.hidden = true; });
}
