$(function() {
    var customers = new Bloodhound({
        datumTokenizer: function(obj) {
            return obj.tokens;
        },
        queryTokenizer: function(query){
            return query.split(/[-\s]/);
        },
        identify: function(obj) {
            return obj.id;
        },
        prefetch: {
            url: '/concierge/customers/search',
            ttl: 900000,
            transform: function(response) {
                return response.customers;
            },
        }
    });
    var tt_options = {
        hint: true,
        minLength: 2
    };
    $('#customer_search .typeahead').typeahead(tt_options, {
        display: function(obj) {
            return obj.display;
        },
        name: 'customers',
        source: customers
    }).on('typeahead:select typeahead:autocomplete', function(event, suggestion) {
        $('#customer_id').val(suggestion.id);
    });
});