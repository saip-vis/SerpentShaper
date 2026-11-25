(() => {
  const desktopPointer = window.matchMedia('(hover: hover) and (pointer: fine)');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (!desktopPointer.matches || reducedMotion.matches) return;

  const glow = document.createElement('div');
  glow.className = 'cursor-glow';
  glow.setAttribute('aria-hidden', 'true');
  document.body.append(glow);

  let x = 0;
  let y = 0;
  let frame = 0;
  window.addEventListener('pointermove', (event) => {
    if (event.pointerType !== 'mouse' && event.pointerType !== 'pen') return;
    x = event.clientX;
    y = event.clientY;
    if (!frame) frame = requestAnimationFrame(() => {
      glow.style.transform = `translate3d(${x}px, ${y}px, 0) translate(-50%, -50%)`;
      glow.classList.add('is-visible');
      frame = 0;
    });
  }, {passive: true});
  document.addEventListener('pointerleave', () => glow.classList.remove('is-visible'));
  window.addEventListener('blur', () => glow.classList.remove('is-visible'));
})();
