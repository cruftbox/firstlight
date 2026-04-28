document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('input[type="time"][step="900"]').forEach(function (input) {
    input.addEventListener('wheel', function (e) {
      e.preventDefault();
      var parts = (this.value || '00:00').split(':');
      var minutes = parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
      minutes += e.deltaY < 0 ? 15 : -15;
      minutes = ((minutes % 1440) + 1440) % 1440;
      var h = String(Math.floor(minutes / 60)).padStart(2, '0');
      var m = String(minutes % 60).padStart(2, '0');
      this.value = h + ':' + m;
    }, { passive: false });
  });
});
