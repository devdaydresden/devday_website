$(document).ready(function() {
  $('.qrcode').each(function(i,elem) {
    var qrcode = new QRCode($(elem).attr('data-src'));
    var svg = qrcode.svg();
    elem.innerHTML = svg;
  })
});
