$(function() {
    $("#user_form").submit(function() {

        if ( $("#add_card").is(":visible")) {
            var form = this;
            var card = {
                number: $("#credit_card_number").val(),
                expMonth: $("#expiry_month").val(),
                expYear: $("#expiry_year").val(),
                cvc: $("#cvv").val(),
                address_zip: $('#id_billing_zip').val()
            };

            Stripe.createToken(card, function(status, response) {
                if (status === 200) {
                    console.log(response);
                    $("#credit-card-errors").hide();
                    $("#id_last_4_digits").val(response.card.last4);
                    $("#stripe_token").val(response.id);
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

    $("#change_card").click(function() {
        $("#card_on_file").hide();
        $("#add_card").show();
        $("#credit_card_number").focus();
        return false;
    });
    $("#cancel_change_card").click(function() {
        $("#add_card").hide();
        $("#card_on_file").show();
        return false;
    });
    $("#change_ride_card").click(function() {
        $("#add_ride_card").show();
        $("#add_stripe_customer").val(1);
        $("#id_first_name").focus();
    });
    $("#change_plan").click(function(e){
        e.preventDefault();
        $("#selected_plan").hide();
        $(".plan-buttons").show();
    });

    $('.cc-mask input').mask('0000-0000-0000-0000');
    $('.zip-mask input').mask('00000-0000');
});