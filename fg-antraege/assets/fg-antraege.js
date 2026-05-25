document.addEventListener('DOMContentLoaded', function(){

  // Accordion
  document.querySelectorAll('.fg-antrag-header').forEach(function(header){
    header.addEventListener('click', function(){
      var item = this.closest('.fg-antrag-item');
      item.classList.toggle('open');
    });
  });

  // Filter
  document.querySelectorAll('.fg-filter-btn').forEach(function(btn){
    btn.addEventListener('click', function(){
      document.querySelectorAll('.fg-filter-btn').forEach(function(b){ b.classList.remove('active'); });
      this.classList.add('active');
      var filter = this.getAttribute('data-filter');
      document.querySelectorAll('.fg-antrag-item').forEach(function(item){
        if(filter === 'alle' || item.getAttribute('data-status') === filter){
          item.style.display = '';
        } else {
          item.style.display = 'none';
        }
      });
    });
  });

});
