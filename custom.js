// Lesefortschritt
window.addEventListener('scroll', function() {
	var el = document.getElementById('fg-reading-progress');
	if (!el) return;
	var scrollTop = window.scrollY;
	var docHeight = document.documentElement.scrollHeight - window.innerHeight;
	var progress = 0;
	if (docHeight !== 0) { progress = (scrollTop / docHeight) * 100; }
	el.style.width = progress + '%';
});
