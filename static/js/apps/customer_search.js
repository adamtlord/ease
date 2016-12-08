$(function() {
    var customers = new Bloodhound({
        datumTokenizer: function(obj) {
            var tokenlist = obj.tokens;
            var tokens = [];
            for(var t=0;t<tokenlist.length;t++){
                if(/[-\s]/.test(tokenlist[t])){
                    tokens.push(tokenlist[t]);
                    if(/-/.test(tokenlist[t])){
                        tokens.push(tokenlist[t].replace(/[-]/g, ''));
                    }
                    var subtokens = tokenlist[t].split(/[-\s]/);
                    for(var s=0; s<subtokens.length; s++){
                        tokens.push(subtokens[s]);
                    }
                }else {
                    tokens.push(tokenlist[t]);
                }
            }
            return tokens;
        },
        queryTokenizer: function(query){
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
    });
    var tt_options = {
        hint: true,
        minLength: 2
    };
    $('#customer_search .typeahead').typeahead(tt_options, {
        display: function(obj) {
            var mobile = obj.mobile_phone ? ' ' + obj.mobile_phone + ' (M) ' : '';
            var user = obj.user ? ' | Account: ' + obj.user : '';
            var riders = obj.riders.length ? ' | Riders: ' + obj.riders.join(', ') : '';
            return obj.name + ' ' + obj.home_phone + ' (H) ' + mobile + user + riders;
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