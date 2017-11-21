/* global Stripe */
$(function() {

    $("#payment_form").submit(function() {
        if ($("#add_card").is(":visible")) {
            var form = this;
            var card = {
                number: $("#credit_card_number").val(),
                expMonth: $("#expiry_month").val(),
                expYear: $("#expiry_year").val(),
                cvc: $("#CVV").val(),
                address_zip: $('#id_billing_zip').val()
            };

            Stripe.createToken(card, function(status, response) {
                if (status === 200) {
                    $("#credit-card-errors").hide();
                    $("#id_last_4_digits").val(response.card.last4);
                    $("#id_stripe_token").val(response.id);
                    form.submit();
                } else {
                    $("#stripe-error-message").text(response.error.message);
                    $("#credit-card-errors").show();
                    $("#user_submit").attr("disabled", false);
                }
            });

            return false;
        }

        return true;

    });

    $('.cc-mask input').mask('0000-0000-0000-0000');
    $('.zip-mask input').mask('00000-0000');

    $(".datepicker input").datetimepicker({
        autoclose: true,
        fontAwesome: true,
        format: "yyyy-mm-dd",
        startView: 2,
        minView: 2,
        todayHighlight: true,
        weekStart: 0,
    });

    $('#id_funds_source').on('change', function(){
        $('#add_card').collapse(this.value === 'new' ? 'show' : 'hide');
    });

    if ($('#credit-card-errors').is(':visible')) {
        $('html, body').animate({
            scrollTop: $("#credit-card-errors").offset().top - 40
        }, 500);
    }

    $('#add_card').collapse($('#id_funds_source').val() === 'new' ? 'show' : 'hide');

});