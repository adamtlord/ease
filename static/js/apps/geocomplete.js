// This example displays an address form, using the autocomplete feature
// of the Google Places API to help users fill in the information.

// This example requires the Places library. Include the libraries=places
// parameter when you first load the API. For example:
// <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&libraries=places">

var placeSearch, autocomplete;
var componentForm = {
  street_number: 'short_name',
  route: 'long_name',
  locality: 'long_name',
  administrative_area_level_1: 'short_name',
  postal_code: 'short_name'
};
var componentMap = {
  street_number: 'street1',
  route: 'street1',
  locality: 'city',
  administrative_area_level_1: 'state',
  postal_code: 'zip_code'
};

function initAutocomplete() {

  var acs = [];
  $('.autocomplete').each(function(){
    autocomplete = new google.maps.places.Autocomplete(
      this, {
        country: 'us'
      });
    autocomplete.prefix = $(this).data('prefix');
    acs.push(autocomplete);
  });
  for(var i = 0; i < acs.length; i++){
    console.log(acs);
    acs[i].addListener('place_changed', fillInAddress);
  };
}

function fillInAddress() {

  $('.destination .form-control').val('').removeAttr('disabled');

  var place = this.getPlace();
  var prefix = this.prefix;
  for (var i = 0; i < place.address_components.length; i++) {
    var addressType = place.address_components[i].types[0];
    if (componentForm[addressType]) {
      var val = place.address_components[i][componentForm[addressType]];
      if(addressType == 'street_number'){
        val = val + ' ';
      }
      var input = $('#id_' + prefix + componentMap[addressType]);

      input.val(input.val() + val);
    }
  }
  if(place.name){
    $('#id_' + prefix + 'name').val(place.name);
  }
}

function geolocate() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(function(position) {
      var geolocation = {
        lat: position.coords.latitude,
        lng: position.coords.longitude
      };
      var circle = new google.maps.Circle({
        center: geolocation,
        radius: position.coords.accuracy
      });
      autocomplete.setBounds(circle.getBounds());
    });
  }
}