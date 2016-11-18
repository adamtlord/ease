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
            transform: function(response) {
                return response.customers;
            },
        }
    });
    var tt_options = {
        highlight: true,
        hint: true,
        minLength: 2
    };
    $('#customer_search .typeahead').typeahead(tt_options, {
        display: function(obj) {
            var mobile = obj.mobile_phone ? ' ' + obj.mobile_phone : '';
            return obj.name + ' ' + obj.home_phone + mobile;
        },
        name: 'customers',
        source: customers
    }).on('typeahead:select', function(event, suggestion) {
        goToCustomer(suggestion.id);
    }).on('keypress', function(e) {
        if (e.keyCode === 13) {
            $("#customer_search .tt-suggestion:first-child").trigger('click');
        }
    });

    function goToCustomer(id) {
        window.location.href = '/concierge/customers/' + id;
    }

});