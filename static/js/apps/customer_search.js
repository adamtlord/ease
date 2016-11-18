$(function() {
    var customers = new Bloodhound({
        datumTokenizer: function(obj) {
            return obj.tokens
        },
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        identify: function(obj) {
            return obj.id
        },
        prefetch: {
            url: '/concierge/customers/search',
            cache: false
        }
    });

    $('#customer_search .typeahead').typeahead(null, {
        name: 'customers',
        display: function(obj) {
            return obj.display
        },
        source: customers
    });
});