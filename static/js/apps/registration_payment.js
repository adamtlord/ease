
$(function() {
  $("#user_form").submit(function() {
    var form = this;
    var card = {
        number:   $("#credit_card_number").val(),
        expMonth: $("#expiry_month").val(),
        expYear:  $("#expiry_year").val(),
        cvc:      $("#cvv").val(),
        address_zip: $('#billing_zip').val()
    };

    Stripe.createToken(card, function(status, response) {
        if (status === 200) {
            console.log(status, response);
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

    });
    $('.cc-mask input').mask('0000-0000-0000-0000');
    $('.zip-mask input').mask('00000-0000');
});