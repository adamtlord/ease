$(function() {
    var customers = new Bloodhound({
        datumTokenizer: function(obj) {
            return obj.tokens;
        },
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        identify: function(obj) {
            return obj.id;
        },
        prefetch: {
            url: '/concierge/customers/search',
            cache: false,
            transform: function(response){
                return response.customers;
            },
        }
    });
    var options = {
        highlight: true,
        hint: true,
        minLength: 2
    }
    $('#customer_search .typeahead').typeahead(options, {
        display: function(obj) {
            return [obj.name, obj.home_phone, obj.mobile_phone].join(' ');
        },
        name: 'customers',
        source: customers
    }).on('typeahead:select', function(event, suggestion){
        location.href += 'customers/' + suggestion.id;
    });
});