$(function() {
    function toggleCustomerRides(val, id) {
        $('input.customer_' + id).prop('checked', val);
    }

    function toggleAllRides(val) {
        $('input.customer, input[name="ride"]').prop('checked', val);
        toggleSubmit();
    }

    function toggleMaster() {
        var master = $('.master');
        if ($('input[class^="customer_"]:checked').length === $('input[class^="customer_"]').length) {
            master.prop('checked', true);
        } else {
            master.prop('checked', false);
        }
        toggleSubmit();
    }

    function toggleSubmit() {
        if ($('input[class^="customer_"]:checked').length > 0) {
            $('[type="submit"]').removeAttr('disabled');
        }else {
            $('[type="submit"]').attr('disabled', 'disabled');
        }
    }

    $('tr').on('click', function(e) {
        if (!$(e.target).is('input') && !$(e.target).is('.btn') && !$(e.target).is('a')) {
            $(this).find('input').click();
        }
    });

    $('input.customer').on('change', function() {
        toggleCustomerRides(this.checked, $(this).data('customer'));
        toggleMaster();
    });

    $('input[class^="customer_"]').on('change', function() {
        var inputclass = '.' + $(this).attr('class');
        var custid = $(this).data('parent');
        var customer = $("[data-customer='" + custid + "']");
        if ($(inputclass + ':checked').length === $(inputclass).length) {
            customer.prop('checked', true).trigger('change');
        } else if ($(inputclass + ':checked').length === 0) {
            customer.prop('checked', false).trigger('change');
        }
        toggleMaster();
    });

    $('.master').on('change', function() {
        toggleAllRides(this.checked);
    });

});