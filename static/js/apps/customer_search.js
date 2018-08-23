/* global Bloodhound */

$(function() {
  var bloodhound_sources = {

    customers: new Bloodhound({
      datumTokenizer: function(obj) {
        return obj.tokens;
      },
      queryTokenizer: function(query) {
        return query.split(/[-\s]/);
      },
      identify: function(obj) {
        return obj.id;
      },
      prefetch: {
        url: '/concierge/customers/search',
        cache: false,
        transform: function(response) {
          return response.customers;
        },
      }
    }),

    group_memberships: new Bloodhound({
      datumTokenizer: function(obj) {
        return obj.display_name.split(' ');
      },
      queryTokenizer: Bloodhound.tokenizers.whitespace,
      identify: function(obj) {
        return obj.display_name;
      },
      prefetch: {
        url: '/api/group-memberships/?active=true&limit=999',
        cache: false,
        transform: function(response) {
          return response.results;
        },
      }
    })

  };

  $('#customer_search #search_input').typeahead({
    hint: true,
    minLength: 0,
  }, {
    name: 'customers',
    source: bloodhound_sources.customers,
    limit: 10,
    display: function(obj) {
      return obj.display;
    },
  }, {
    name: 'group-memberships',
    source: bloodhound_sources.group_memberships,
    limit: 10,
    display: 'display_name',
    templates: {
      suggestion: function(value) {
        return '<div><i class="fa fa-group"></i> ' + value.display_name + '</div>';
      }
    },
  }).on('typeahead:select', function(e, suggestion) {
    window.location = suggestion.url;
  }).on('typeahead:autocomplete', function(e, suggestion) {
    $('#object_url').val(suggestion.url);
  });

  $('#customer_search').on('submit', function(e) {
    e.preventDefault();
    if ($('#object_url').val()) {
      window.location = $('#object_url').val();
    }
    return false;
  });
});