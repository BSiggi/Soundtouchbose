<script>
function setupPrintButton(){
  if (!document.body.classList.contains('single-post')) return;

  var content = document.querySelector(
    '.single-post article .entry-content, article.type-post .entry-content, .entry-content, .post-entry, .post-content'
  );
  if (!content) return;

  if (document.querySelector('.post-action-buttons')) return;

  var wrap = document.createElement('div');
  wrap.className = 'post-action-buttons';
  wrap.style.textAlign = 'center';
  wrap.style.marginTop = '20px';
  wrap.style.marginBottom = '30px';
  content.insertAdjacentElement('afterend', wrap);

  var btn = document.createElement('button');
  btn.className = 'print-post-btn';
  btn.type = 'button';
  btn.setAttribute('aria-label','Beitrag drucken');
  btn.textContent = 'Beitrag drucken';

  var baseColor = '#F5A623';
  var hoverColor = '#d4891a';

  Object.assign(btn.style, {
    display: 'inline-block',
    padding: '10px 22px',
    fontSize: '15px',
    fontWeight: '700',
    fontFamily: getComputedStyle(document.body).fontFamily || 'inherit',
    background: baseColor,
    color: '#111111',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    lineHeight: '1.4',
    boxShadow: 'none',
    textTransform: 'uppercase',
    transition: 'background .2s ease, color .2s ease'
  });

  btn.addEventListener('mouseenter', function(){ btn.style.background = hoverColor; });
  btn.addEventListener('mouseleave', function(){ btn.style.background = baseColor; });
  btn.addEventListener('focus', function(){ btn.style.outline = '2px solid #000'; btn.style.outlineOffset = '2px'; });
  btn.addEventListener('blur',  function(){ btn.style.outline = 'none'; });
  btn.addEventListener('click', function(){ window.print(); });

  wrap.appendChild(btn);
}

function setupReadingProgress(){
  if (!document.body.classList.contains('single-post')) return;
  if (document.getElementById('fg-reading-progress')) return;

  var bar = document.createElement('div');
  bar.id = 'fg-reading-progress';
  bar.style.cssText = 'position:fixed;top:0px;left:0;width:0%;height:4px;background:#F5A623;z-index:999999;transition:width 0.15s ease;pointer-events:none;';
  document.body.appendChild(bar);

  function getHeaderBottom(){
    var header = document.querySelector('header.header-bar');
    if (!header) return 0;
    var rect = header.getBoundingClientRect();
    return rect.bottom > 0 ? rect.bottom : 0;
  }

  function updateBar(){
    bar.style.top = getHeaderBottom() + 'px';
    var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    var docHeight = document.documentElement.scrollHeight - window.innerHeight;
    var progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
    bar.style.width = progress + '%';
  }

  window.addEventListener('scroll', updateBar);
  window.addEventListener('resize', updateBar);
  updateBar();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function(){
    setupPrintButton();
    setupReadingProgress();
  });
} else {
  setupPrintButton();
  setupReadingProgress();
}
</script>
