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
        if($('fieldset.lovedone').is(':visible')){
            cloneMore('fieldset.lovedone:last', 'lovedone');
        }else {
            $('fieldset.lovedone').slideDown();
        }
    });
    $('#add_rider_fields').click(function(e) {
        e.preventDefault();
        if($('fieldset.rider').is(':visible')){
            cloneMore('fieldset.rider:last', 'rider');
        }else {
            $('fieldset.rider').slideDown();
        }
    });



    // On Load
    toggleOtherSource($('#id_reg-source option:selected').val());
    toggleSendUpdates($('#id_send_updates option:selected').val());

    // Input masking
    $('.phone-mask input').mask('000-000-0000');
    $('.zip-mask input').mask('00000-0000');

});