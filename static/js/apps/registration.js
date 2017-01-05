$(function() {
    // Internal Functions
    function toggleOtherSource(val) {
        if (val === 'OTHER') {
            $('#source_other').slideDown();
        } else {
            $('#source_other').slideUp();
        }
    }

    function toggleSendUpdates(val) {
        if (val === '1' || val === '2') {
            $('#lovedone_fields').slideDown();
        } else {
            $('#lovedone_fields').slideUp();
        }
    }

    function toggleCopyCustomerInfo(checked) {
        var common_fields = {
            '#id_reg-email': '#id_cust-email',
            '#id_reg-first_name': '#id_cust-first_name',
            '#id_reg-last_name': '#id_cust-last_name',
        };

        if (checked) {
            for (var k1 in common_fields) {
                $(k1).val($(common_fields[k1]).val());
            }
            $('#id_reg-relationship').val('self');
        } else {
            for (var k2 in common_fields) {
                $(k2).val('');
            }
            $('#id_reg-relationship').val('');
        }
    }

    function cloneMore(selector, type) {
        var newElement = $(selector).clone(true);
        var total = $('#id_' + type + '-TOTAL_FORMS').val();
        newElement.find(':input').each(function() {
            var name = $(this).attr('name').replace('-' + (total - 1) + '-', '-' + total + '-');
            var id = 'id_' + name;
            $(this).attr({
                'name': name,
                'id': id
            }).val('').removeAttr('checked');
        });
        newElement.find('label').each(function() {
            var newFor = $(this).attr('for').replace('-' + (total - 1) + '-', '-' + total + '-');
            $(this).attr('for', newFor);
        });
        total++;
        $('#id_' + type + '-TOTAL_FORMS').val(total);
        $(selector).after(newElement);
    }

    function validate_pswd1(field) {

        var pswd = field.val();
        var container = field.parent();
        var length_message = $('#pswd_length');
        var dynamic_message = $('#pswd_dynamic');
        var valid_length = false;
        var validate_url = field.data('remote');

        var reset = function() {
            length_message.removeClass('invalid valid');
            container.removeClass('valid');
            dynamic_message.removeClass('invalid').html('');
        };

        if (pswd.length > 0) {
            if (pswd.length < 8) {
                length_message.removeClass('valid').addClass('invalid');
                container.removeClass('valid');
            } else {
                length_message.removeClass('invalid').addClass('valid');
                valid_length = true;
            }
            if (valid_length) {
                $.get(validate_url, {
                    pswd: pswd
                }, function(data) {
                    if (data.valid) {
                        dynamic_message.removeClass('invalid').html('');
                        container.addClass('valid');
                    } else {
                        dynamic_message.addClass('invalid').html(data.errors.join('<br>'));
                        container.removeClass('valid');
                    }
                });
            } else {
                dynamic_message.removeClass('invalid').html('');
            }
        } else {
            reset();
        }
    }

    function validate_pswd2(field) {
        var pswd = field.val();
        var container = field.parent();
        var error_message = $('#pswd_match_error');

        var valid = function(){
            container.removeClass('has-error').addClass('valid');
            error_message.removeClass('errorlist').text('');
        };
        var invalid = function(){
            container.removeClass('valid').addClass('has-error');
            error_message.addClass('errorlist').text('Passwords don\'t match');
        };
        var reset = function(){
            container.removeClass('valid has-error');
            error_message.removeClass('errorlist').text('');
        };

        if (pswd.length > 0){
            if (pswd === $('#id_reg-password1').val()) {
                valid();
            } else {
                invalid();
            }
        } else {
            reset();
        }
    }

    // Event Binding
    $('#id_reg-source').on('change', function() {
        toggleOtherSource(this.value);
    });
    $('#id_send_updates').on('change', function() {
        toggleSendUpdates(this.value);
    });
    $('#add_destination_fields').click(function(e) {
        e.preventDefault();
        cloneMore('fieldset.destination:last', 'destination');
    });
    $('#add_lovedone_fields').click(function(e) {
        e.preventDefault();
        if ($('fieldset.lovedone').is(':visible')) {
            cloneMore('fieldset.lovedone:last', 'lovedone');
        } else {
            $('fieldset.lovedone').slideDown();
        }
    });
    $('#add_rider_fields').click(function(e) {
        e.preventDefault();
        if ($('fieldset.rider').is(':visible')) {
            cloneMore('fieldset.rider:last', 'rider');
        } else {
            $('fieldset.rider').slideDown();
        }
    });
    $('#use_customer_info').change(function() {
        toggleCopyCustomerInfo($(this).is(':checked'));
    });
    $('#id_reg-password1').keyup(function() {
        validate_pswd1($(this));
    });
    $('#id_reg-password2').keyup(function() {
        validate_pswd2($(this));
    });

    // On Load
    toggleOtherSource($('#id_reg-source option:selected').val());
    toggleSendUpdates($('#id_send_updates option:selected').val());

    // Input masking
    $('.phone-mask input').mask('000-000-0000');
    $('.zip-mask input').mask('00000-0000');
    $('.date-mask input').mask('0000-00-00');

    $(".datepicker input").datetimepicker({
        autoclose: true,
        fontAwesome: true,
        format: "yyyy-mm-dd",
        startView: 2,
        minView: 2,
        todayHighlight: true,
        weekStart: 1,
    });

});